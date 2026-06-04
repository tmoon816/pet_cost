from decimal import Decimal

import pytest


@pytest.fixture
def fixture_data(client):
    c1 = client.post("/api/v1/customers", json={"name": "客户A"}).json()
    c2 = client.post("/api/v1/customers", json={"name": "客户B"}).json()
    p1 = client.post("/api/v1/pets", json={"customer_id": c1["id"], "name": "毛毛"}).json()
    p2 = client.post("/api/v1/pets", json={"customer_id": c1["id"], "name": "豆豆"}).json()
    p3 = client.post("/api/v1/pets", json={"customer_id": c2["id"], "name": "皮皮"}).json()

    records = [
        (p1["id"], "food", "100.00", "2026-03-05"),
        (p1["id"], "medical", "200.00", "2026-03-20"),
        (p1["id"], "food", "50.50", "2026-04-10"),
        (p2["id"], "toy", "30.00", "2026-04-15"),
        (p2["id"], "food", "80.00", "2026-05-01"),
        (p3["id"], "grooming", "150.00", "2026-05-08"),
        (p3["id"], "medical", "400.00", "2026-05-20"),
    ]
    for pet_id, cat, amount, day in records:
        client.post(
            "/api/v1/costs",
            json={
                "pet_id": pet_id,
                "category_code": cat,
                "amount": amount,
                "occurred_on": day,
            },
        )
    return {"c1": c1, "c2": c2, "p1": p1, "p2": p2, "p3": p3}


def test_summary_full_window(client, fixture_data):
    resp = client.get("/api/v1/stats/summary").json()
    assert Decimal(resp["total_amount"]) == Decimal("1010.50")
    assert resp["record_count"] == 7
    assert resp["customer_count"] == 2
    assert resp["pet_count"] == 3


def test_summary_with_window(client, fixture_data):
    resp = client.get(
        "/api/v1/stats/summary", params={"start": "2026-05-01", "end": "2026-05-31"}
    ).json()
    assert Decimal(resp["total_amount"]) == Decimal("630.00")
    assert resp["record_count"] == 3
    assert resp["customer_count"] == 2
    assert resp["pet_count"] == 2


def test_by_category(client, fixture_data):
    rows = client.get("/api/v1/stats/by-category").json()
    by_code = {row["category"]: row for row in rows}
    assert Decimal(by_code["food"]["total"]) == Decimal("230.50")
    assert by_code["food"]["count"] == 3
    assert by_code["food"]["label"] == "粮食"
    assert Decimal(by_code["medical"]["total"]) == Decimal("600.00")
    assert by_code["medical"]["count"] == 2


def test_by_month(client, fixture_data):
    rows = client.get("/api/v1/stats/by-month").json()
    by_month = {row["month"]: Decimal(row["total"]) for row in rows}
    assert by_month["2026-03"] == Decimal("300.00")
    assert by_month["2026-04"] == Decimal("80.50")
    assert by_month["2026-05"] == Decimal("630.00")


def test_cashflow_recharge_principal_plus_cash(client, fixture_data):
    """实收 = 充值本金(不含赠送) + 现金消费；储值消费不计入实收。"""
    c1_id = fixture_data["c1"]["id"]
    # 充 1000 送 200（本金 1000 计入实收，赠送 200 不计）
    client.post(f"/api/v1/customers/{c1_id}/recharge",
                json={"amount": "1000.00", "bonus_amount": "200.00", "channel": "cash"})

    cf = client.get("/api/v1/stats/cashflow").json()
    # fixture 里的订单都是默认 cash 支付，共 1010.50
    assert Decimal(cf["cash_consume"]) == Decimal("1010.50")
    assert Decimal(cf["recharge_principal"]) == Decimal("1000.00")
    assert Decimal(cf["total_cash_in"]) == Decimal("2010.50")


def test_cashflow_excludes_balance_consume(client, fixture_data):
    """储值消费不计入实收（避免和充值重复计）。"""
    c1_id = fixture_data["c1"]["id"]
    p1_id = fixture_data["p1"]["id"]
    client.post(f"/api/v1/customers/{c1_id}/recharge",
                json={"amount": "500.00", "channel": "cash"})
    # 用储值开一单 100，不应增加实收
    client.post("/api/v1/costs", json={
        "pet_id": p1_id, "category_code": "food", "amount": "100.00",
        "occurred_on": "2026-05-15", "pay_method": "balance",
    })
    cf = client.get("/api/v1/stats/cashflow").json()
    # 实收 = 现金消费 1010.50 + 充值本金 500（储值那 100 不算）
    assert Decimal(cf["recharge_principal"]) == Decimal("500.00")
    assert Decimal(cf["cash_consume"]) == Decimal("1010.50")
    assert Decimal(cf["total_cash_in"]) == Decimal("1510.50")


def test_by_day_full_window(client, fixture_data):
    rows = client.get("/api/v1/stats/by-day").json()
    by_day = {row["day"]: row for row in rows}
    # 每条消费各自单独一天，金额应原样落到对应日期
    assert Decimal(by_day["2026-03-05"]["total"]) == Decimal("100.00")
    assert Decimal(by_day["2026-03-20"]["total"]) == Decimal("200.00")
    assert Decimal(by_day["2026-05-20"]["total"]) == Decimal("400.00")
    # 只返回有消费的天，不含空白日
    assert "2026-03-06" not in by_day
    # 新增维度：订单数 / 去重客户数 / 去重宠物数
    assert by_day["2026-03-05"]["record_count"] == 1
    assert by_day["2026-03-05"]["customer_count"] == 1
    assert by_day["2026-03-05"]["pet_count"] == 1


def test_by_day_with_window(client, fixture_data):
    rows = client.get(
        "/api/v1/stats/by-day", params={"start": "2026-05-01", "end": "2026-05-31"}
    ).json()
    by_day = {row["day"]: row for row in rows}
    assert set(by_day.keys()) == {"2026-05-01", "2026-05-08", "2026-05-20"}
    assert Decimal(by_day["2026-05-08"]["total"]) == Decimal("150.00")
    assert by_day["2026-05-08"]["record_count"] == 1
    assert by_day["2026-05-08"]["pet_count"] == 1


def test_by_pet_top_n(client, fixture_data):
    rows = client.get("/api/v1/stats/by-pet", params={"limit": 2}).json()
    assert len(rows) == 2
    assert rows[0]["pet_name"] in {"毛毛", "皮皮"}
    totals = sorted(Decimal(r["total"]) for r in rows)
    assert totals[-1] == Decimal("550.00")  # 皮皮 grooming150 + medical400


def test_by_pet_filter_by_customer(client, fixture_data):
    c1_id = fixture_data["c1"]["id"]
    rows = client.get(
        "/api/v1/stats/by-pet", params={"customer_id": c1_id, "limit": 10}
    ).json()
    names = {row["pet_name"] for row in rows}
    assert names == {"毛毛", "豆豆"}


def test_by_category_includes_orphan_label(client, fixture_data):
    new = client.post(
        "/api/v1/categories",
        json={"code": "training", "label": "训练", "sort_order": 50},
    )
    assert new.status_code == 201
    pet_id = fixture_data["p1"]["id"]
    client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet_id,
            "category_code": "training",
            "amount": "60.00",
            "occurred_on": "2026-05-25",
        },
    )

    client.delete("/api/v1/categories/training")  # 应该 409，记录还在
    rows = client.get("/api/v1/stats/by-category").json()
    by_code = {row["category"]: row["label"] for row in rows}
    assert by_code["training"] == "训练"


def test_customer_acquisition_may_2026(client, fixture_data):
    """T-009: 2026-05 c1 老客（3月就开始消费）/ c2 新客（首次消费在5月8日）。"""
    resp = client.get(
        "/api/v1/stats/customer-acquisition", params={"year": 2026, "month": 5}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["year"] == 2026
    assert body["month"] == 5
    assert body["new_customers"] == 1
    assert body["returning_customers"] == 1
    assert body["total"] == 2


def test_customer_acquisition_empty_month(client, fixture_data):
    """月内无消费 → 全为 0。"""
    resp = client.get(
        "/api/v1/stats/customer-acquisition", params={"year": 2026, "month": 8}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {
        "year": 2026,
        "month": 8,
        "new_customers": 0,
        "returning_customers": 0,
        "total": 0,
    }


def test_dormant_customers_threshold_and_order(client, fixture_data, db_session):
    """T-010: 补上一个老客长期未消费的场景，验证阈值、排序、days_since。"""
    from datetime import date
    from app.crud import stats as crud_stats

    # 再添加一个老客 c3，最近消费 2026-01-10（比 c1 的 2026-05-01 更久）
    c3 = client.post("/api/v1/customers", json={"name": "老客C"}).json()
    p4 = client.post("/api/v1/pets", json={"customer_id": c3["id"], "name": "雪球"}).json()
    client.post(
        "/api/v1/costs",
        json={
            "pet_id": p4["id"],
            "category_code": "food",
            "amount": "60.00",
            "occurred_on": "2026-01-10",
        },
    )

    today = date(2026, 6, 1)  # 固定“今天”让断言稳定
    session = db_session()
    try:
        # days=30 阈值 → cutoff = 2026-05-02
        #   c1 last_visit=2026-05-01 ✅ (31 天 ≥ 30) → 入选
        #   c2 last_visit=2026-05-20 ❌ (12 天 < 30) → 不入
        #   c3 last_visit=2026-01-10 ✅ (142 天) → 入选
        # 按 last_visit 升序：c3 在前，c1 在后
        rows = crud_stats.dormant_customers(session, days=30, limit=10, today=today)
        assert len(rows) == 2
        assert rows[0]["customer_name"] == "老客C"
        assert rows[0]["last_visit_at"] == date(2026, 1, 10)
        assert rows[0]["days_since"] == 142
        assert rows[1]["customer_name"] == "客户A"
        assert rows[1]["last_visit_at"] == date(2026, 5, 1)
        assert rows[1]["days_since"] == 31

        # limit=1 只返一条，应为 c3（最久）
        rows_limit = crud_stats.dormant_customers(session, days=30, limit=1, today=today)
        assert len(rows_limit) == 1
        assert rows_limit[0]["customer_name"] == "老客C"

        # days 阈值抹去所有人（今天 − 任何消费 ≥ 1000）
        rows_none = crud_stats.dormant_customers(session, days=1000, limit=10, today=today)
        assert rows_none == []
    finally:
        session.close()


def test_dormant_customers_api_default_params(client, fixture_data):
    """T-010: API 默认参数调用可返 200 且结构正确。"""
    resp = client.get("/api/v1/stats/dormant-customers")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    for item in body:
        assert set(item.keys()) >= {
            "customer_id",
            "customer_name",
            "last_visit_at",
            "days_since",
        }
        assert item["days_since"] >= 90

# ── T-026: top-customers ──

def test_top_customers_ranking(client, db_session):
    from datetime import date as dt_date
    from app.models import Customer, CostRecord, Pet

    db = db_session()
    try:
        c1 = Customer(name="高价值A", phone="13900000001")
        c2 = Customer(name="高价值B", phone="13900000002")
        db.add_all([c1, c2])
        db.flush()

        p1 = Pet(name="p1", species="dog", customer_id=c1.id)
        p2 = Pet(name="p2", species="cat", customer_id=c2.id)
        db.add_all([p1, p2])
        db.flush()

        db.add_all([
            CostRecord(pet_id=p1.id, category_code="food", amount=500, occurred_on=dt_date(2026, 5, 1)),
            CostRecord(pet_id=p1.id, category_code="food", amount=300, occurred_on=dt_date(2026, 5, 2)),
            CostRecord(pet_id=p2.id, category_code="food", amount=100, occurred_on=dt_date(2026, 5, 3)),
        ])
        db.commit()
    finally:
        db.close()

    resp = client.get("/api/v1/stats/top-customers", params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["rank"] == 1
    assert data[0]["customer_name"] == "高价值A"
    assert data[0]["total_amount"] == "800.00"
    assert data[0]["order_count"] == 2
    assert data[1]["rank"] == 2
    assert data[1]["customer_name"] == "高价值B"


def test_top_customers_date_range(client, db_session):
    """传 start/end 时只统计区间内的消费（月榜口径）。"""
    from datetime import date as dt_date
    from app.models import Customer, CostRecord, Pet

    db = db_session()
    try:
        c1 = Customer(name="月榜A", phone="13911110001")
        c2 = Customer(name="月榜B", phone="13911110002")
        db.add_all([c1, c2])
        db.flush()
        p1 = Pet(name="p1", species="dog", customer_id=c1.id)
        p2 = Pet(name="p2", species="cat", customer_id=c2.id)
        db.add_all([p1, p2])
        db.flush()
        db.add_all([
            # A：4月大额（区间外）+ 6月小额（区间内 100）
            CostRecord(pet_id=p1.id, category_code="food", amount=900, occurred_on=dt_date(2026, 4, 10)),
            CostRecord(pet_id=p1.id, category_code="food", amount=100, occurred_on=dt_date(2026, 6, 5)),
            # B：6月中额（区间内 300）
            CostRecord(pet_id=p2.id, category_code="food", amount=300, occurred_on=dt_date(2026, 6, 8)),
        ])
        db.commit()
    finally:
        db.close()

    # 只看 6 月：B(300) 应排在 A(100) 前
    resp = client.get(
        "/api/v1/stats/top-customers",
        params={"limit": 10, "start": "2026-06-01", "end": "2026-06-30"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["customer_name"] == "月榜B"
    assert data[0]["total_amount"] == "300.00"
    assert data[1]["customer_name"] == "月榜A"
    assert data[1]["total_amount"] == "100.00"


def test_top_customers_limit(client, db_session):
    from app.models import Customer

    db = db_session()
    try:
        for i in range(5):
            db.add(Customer(name=f"限流客户{i}", phone=f"1300000000{i}"))
        db.commit()
    finally:
        db.close()

    resp = client.get("/api/v1/stats/top-customers", params={"limit": 3})
    assert resp.status_code == 200
    assert len(resp.json()) == 0  # 没有 cost 记录 → 空列表


def test_top_customers_no_costs(client, db_session):
    db_session()  # create tables
    resp = client.get("/api/v1/stats/top-customers")
    assert resp.status_code == 200
    assert resp.json() == []
