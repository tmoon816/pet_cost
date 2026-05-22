"""Tests for T-022 CSV export endpoints — customers/export and costs/export."""

def test_export_customers_csv_bom(client, db_session):
    db = db_session()
    from app.models import Customer
    db.add_all([
        Customer(name="测试客户A", phone="13000000000", note="备注A"),
        Customer(name="测试客户B", phone="13100000000", note=""),
    ])
    db.flush()

    resp = client.get("/api/v1/customers/export")
    assert resp.status_code == 200
    text = resp.text
    # UTF-8 BOM
    assert text.startswith("\ufeff")
    # 表头
    assert "姓名" in text
    assert "手机号" in text
    # 数据
    assert "测试客户A" in text
    assert "13000000000" in text
    assert "测试客户B" in text
    assert "13100000000" in text


def test_export_customers_csv_with_filter(client, db_session):
    db = db_session()
    from app.models import Customer
    db.add_all([
        Customer(name="导出测试1", phone="13200000001"),
        Customer(name="导出测试2", phone="13200000002"),
    ])
    db.flush()

    resp = client.get("/api/v1/customers/export", params={"q": "导出测试1"})
    assert resp.status_code == 200
    assert "导出测试1" in resp.text
    assert "导出测试2" not in resp.text  # 筛选生效


def test_export_customers_csv_empty(client, db_session):
    db_session()  # ensure tables
    resp = client.get("/api/v1/customers/export")
    assert resp.status_code == 200
    text = resp.text
    assert text.startswith("\ufeff")
    assert "姓名" in text
    # Only header + newline, no data rows
    lines = [l for l in text.split("\r\n") if l]
    assert len(lines) == 1  # header only


def test_export_costs_csv_bom(client, db_session):
    db = db_session()
    from datetime import date as dt_date
    from app.models import CostCategory, Customer, CostRecord, Pet

    c = Customer(name="订单客户", phone="13300000000")
    p = Pet(name="测试宠物", species="dog", customer=c)
    cat = db.query(CostCategory).filter_by(code="food").first()
    cr = CostRecord(
        pet=p, category_code=cat.code, amount=123.45,
        occurred_on=dt_date(2026, 5, 15), note="测试备注",
    )
    db.add_all([c, p, cr])
    db.flush()

    resp = client.get("/api/v1/costs/export")
    assert resp.status_code == 200
    text = resp.text
    assert text.startswith("\ufeff")
    assert "日期" in text
    assert "宠物名" in text
    assert "客户名" in text
    assert "测试宠物" in text
    assert "订单客户" in text
    assert "123.45" in text
    assert "测试备注" in text


def test_export_costs_csv_filter_category(client, db_session):
    db = db_session()
    from datetime import date as dt_date
    from app.models import CostCategory, Customer, CostRecord, Pet

    c = Customer(name="筛选客户", phone="13400000000")
    p = Pet(name="筛选宠物", species="cat", customer=c)
    food = db.query(CostCategory).filter_by(code="food").first()
    medical = db.query(CostCategory).filter_by(code="medical").first()
    db.add_all([c, p])
    db.add(CostRecord(pet=p, category_code=food.code, amount=100, occurred_on=dt_date(2026, 5, 1), note="驱虫"))
    db.add(CostRecord(pet=p, category_code=medical.code, amount=200, occurred_on=dt_date(2026, 5, 2), note="体检"))
    db.flush()

    resp = client.get("/api/v1/costs/export", params={"category": "food"})
    assert resp.status_code == 200
    assert "驱虫" in resp.text
    assert "体检" not in resp.text  # filtered out


def test_export_costs_csv_empty(client, db_session):
    db_session()
    resp = client.get("/api/v1/costs/export")
    assert resp.status_code == 200
    text = resp.text
    assert text.startswith("\ufeff")
    lines = [l for l in text.split("\r\n") if l]
    assert len(lines) == 1  # header only