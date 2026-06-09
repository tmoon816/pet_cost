from decimal import Decimal

import pytest


@pytest.fixture
def cust_and_pet(client):
    c = client.post("/api/v1/customers", json={"name": "寄养王"}).json()
    # 充点余额
    client.post(f"/api/v1/customers/{c['id']}/recharge",
                json={"amount": "200.00", "channel": "cash"})
    p = client.post("/api/v1/pets", json={"customer_id": c["id"], "name": "旺财"}).json()
    return c, p


def test_create_boarding_charges_on_create(client, cust_and_pet):
    c, p = cust_and_pet
    resp = client.post("/api/v1/boarding", json={
        "pet_id": p["id"],
        "check_in_date": "2026-06-01",
        "expected_days": 10,
        "daily_rate": "50.00",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["pet_name"] == "旺财"
    assert body["customer_name"] == "寄养王"
    assert body["status"] == "active"
    # 创建即结算到今天，total_charged 应 > 0（今天已过 6/1）
    assert Decimal(body["total_charged"]) > 0


def test_list_and_settle_idempotent(client, cust_and_pet):
    c, p = cust_and_pet
    client.post("/api/v1/boarding", json={
        "pet_id": p["id"], "check_in_date": "2026-06-01",
        "expected_days": 10, "daily_rate": "10.00",
    })
    # 多次 settle 不应报错（幂等）
    r1 = client.post("/api/v1/boarding/settle").json()
    r2 = client.post("/api/v1/boarding/settle").json()
    assert r2["days_charged"] == 0  # 第二次没有新扣
    rows = client.get("/api/v1/boarding", params={"status": "active"}).json()
    assert len(rows) == 1


def test_close_boarding(client, cust_and_pet):
    c, p = cust_and_pet
    order = client.post("/api/v1/boarding", json={
        "pet_id": p["id"], "check_in_date": "2026-06-01",
        "expected_days": 10, "daily_rate": "20.00",
    }).json()
    resp = client.post(f"/api/v1/boarding/{order['id']}/close",
                       json={"check_out_date": "2026-06-03"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"
    # 再次 close 应 400
    resp2 = client.post(f"/api/v1/boarding/{order['id']}/close",
                        json={"check_out_date": "2026-06-03"})
    assert resp2.status_code == 400


def test_close_before_checkin_rejected(client, cust_and_pet):
    c, p = cust_and_pet
    order = client.post("/api/v1/boarding", json={
        "pet_id": p["id"], "check_in_date": "2026-06-10",
        "expected_days": 5, "daily_rate": "20.00",
    }).json()
    resp = client.post(f"/api/v1/boarding/{order['id']}/close",
                       json={"check_out_date": "2026-06-01"})
    assert resp.status_code == 400


def test_alerts_arrears(client, cust_and_pet):
    """余额不足扣成负 → 欠费提醒出现。"""
    c, p = cust_and_pet
    # 日费 500，远超 200 余额 => 必欠费
    client.post("/api/v1/boarding", json={
        "pet_id": p["id"], "check_in_date": "2026-06-01",
        "expected_days": 30, "daily_rate": "500.00",
    })
    alerts = client.get("/api/v1/boarding/alerts").json()
    assert any(a["type"] == "arrears" for a in alerts)


def test_create_unknown_pet(client):
    resp = client.post("/api/v1/boarding", json={
        "pet_id": 999999, "check_in_date": "2026-06-01",
        "expected_days": 5, "daily_rate": "20.00",
    })
    assert resp.status_code == 404


def test_delete_boarding(client, cust_and_pet):
    c, p = cust_and_pet
    order = client.post("/api/v1/boarding", json={
        "pet_id": p["id"], "check_in_date": "2026-06-01",
        "expected_days": 5, "daily_rate": "20.00",
    }).json()
    assert client.delete(f"/api/v1/boarding/{order['id']}").status_code == 204
    assert client.delete(f"/api/v1/boarding/{order['id']}").status_code == 404
