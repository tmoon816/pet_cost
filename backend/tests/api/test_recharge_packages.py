from decimal import Decimal

import pytest


@pytest.fixture
def a_customer(client):
    return client.post("/api/v1/customers", json={"name": "充值客户"}).json()


@pytest.fixture
def a_package(client):
    resp = client.post(
        "/api/v1/recharge-packages",
        json={
            "name": "Pro 卡",
            "subtitle": "常来洗护",
            "price": "1000.00",
            "bonus_amount": "200.00",
            "gifts": ["进口猫砂 1 袋", "精细洗护 1 次"],
            "highlights": ["充 1000 送 200", "洗护 9 折"],
            "badge": "最受欢迎",
            "is_recommended": True,
            "sort_order": 20,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_create_and_list_packages(client, a_package):
    rows = client.get("/api/v1/recharge-packages").json()
    assert len(rows) == 1
    pkg = rows[0]
    assert pkg["name"] == "Pro 卡"
    assert Decimal(pkg["price"]) == Decimal("1000.00")
    assert Decimal(pkg["bonus_amount"]) == Decimal("200.00")
    assert pkg["gifts"] == ["进口猫砂 1 袋", "精细洗护 1 次"]
    assert pkg["is_recommended"] is True


def test_active_only_filter(client, a_package):
    client.post(
        "/api/v1/recharge-packages",
        json={"name": "停用卡", "price": "100.00", "is_active": False},
    )
    all_rows = client.get("/api/v1/recharge-packages").json()
    active_rows = client.get("/api/v1/recharge-packages", params={"active_only": True}).json()
    assert len(all_rows) == 2
    assert len(active_rows) == 1
    assert active_rows[0]["name"] == "Pro 卡"


def test_update_package(client, a_package):
    pid = a_package["id"]
    resp = client.patch(
        f"/api/v1/recharge-packages/{pid}",
        json={"price": "1200.00", "badge": "超值"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert Decimal(body["price"]) == Decimal("1200.00")
    assert body["badge"] == "超值"
    # 未传字段保持不变
    assert Decimal(body["bonus_amount"]) == Decimal("200.00")


def test_delete_package(client, a_package):
    pid = a_package["id"]
    assert client.delete(f"/api/v1/recharge-packages/{pid}").status_code == 204
    assert client.get("/api/v1/recharge-packages").json() == []
    assert client.delete(f"/api/v1/recharge-packages/{pid}").status_code == 404


def test_checkout_credits_balance_and_records_txn(client, a_package, a_customer):
    pid = a_package["id"]
    cid = a_customer["id"]
    resp = client.post(
        f"/api/v1/recharge-packages/{pid}/checkout",
        json={"customer_id": cid, "channel": "wechat"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # 到账 = 本金 1000 + 赠送 200
    assert Decimal(body["paid_amount"]) == Decimal("1000.00")
    assert Decimal(body["bonus_amount"]) == Decimal("200.00")
    assert Decimal(body["credited"]) == Decimal("1200.00")
    assert Decimal(body["balance"]) == Decimal("1200.00")
    assert body["gifts"] == ["进口猫砂 1 袋", "精细洗护 1 次"]

    # 流水里有一条 recharge，备注含套餐名与赠品
    txns = client.get(f"/api/v1/customers/{cid}/transactions").json()
    assert txns["total"] == 1
    txn = txns["items"][0]
    assert txn["type"] == "recharge"
    assert Decimal(txn["amount"]) == Decimal("1200.00")
    assert Decimal(txn["bonus_amount"]) == Decimal("200.00")
    assert "Pro 卡" in txn["note"]
    assert "进口猫砂 1 袋" in txn["note"]


def test_checkout_unknown_customer(client, a_package):
    pid = a_package["id"]
    resp = client.post(
        f"/api/v1/recharge-packages/{pid}/checkout",
        json={"customer_id": 999999, "channel": "cash"},
    )
    assert resp.status_code == 404


def test_checkout_inactive_package(client, a_customer):
    pkg = client.post(
        "/api/v1/recharge-packages",
        json={"name": "停用卡", "price": "100.00", "is_active": False},
    ).json()
    resp = client.post(
        f"/api/v1/recharge-packages/{pkg['id']}/checkout",
        json={"customer_id": a_customer["id"], "channel": "cash"},
    )
    assert resp.status_code == 400


def test_checkout_invalid_channel(client, a_package, a_customer):
    resp = client.post(
        f"/api/v1/recharge-packages/{a_package['id']}/checkout",
        json={"customer_id": a_customer["id"], "channel": "bitcoin"},
    )
    assert resp.status_code == 422
