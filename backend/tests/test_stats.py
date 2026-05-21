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
