"""分层阈值 + 折扣率配置：默认值、更新、校验、对分层结果的影响。"""


def test_default_tier_config(client):
    cfg = client.get("/api/v1/settings/tiers").json()
    assert cfg["vip_amount"] == "500"
    assert cfg["svip_amount"] == "2000"
    assert cfg["supreme_amount"] == "5000"
    assert cfg["vip_discount"] == 98
    assert cfg["svip_discount"] == 95
    assert cfg["supreme_discount"] == 90


def test_update_tier_config(client):
    payload = {
        "vip_amount": "300",
        "svip_amount": "1500",
        "supreme_amount": "8000",
        "vip_discount": 99,
        "svip_discount": 96,
        "supreme_discount": 88,
    }
    resp = client.put("/api/v1/settings/tiers", json=payload)
    assert resp.status_code == 200
    cfg = client.get("/api/v1/settings/tiers").json()
    assert cfg["vip_amount"] == "300"
    assert cfg["supreme_discount"] == 88


def test_update_rejects_bad_amount_order(client):
    payload = {
        "vip_amount": "2000",
        "svip_amount": "1000",  # svip < vip 非法
        "supreme_amount": "8000",
        "vip_discount": 98,
        "svip_discount": 95,
        "supreme_discount": 90,
    }
    assert client.put("/api/v1/settings/tiers", json=payload).status_code == 400


def test_update_rejects_discount_out_of_range(client):
    payload = {
        "vip_amount": "300",
        "svip_amount": "1500",
        "supreme_amount": "8000",
        "vip_discount": 120,  # >100 非法
        "svip_discount": 95,
        "supreme_discount": 90,
    }
    assert client.put("/api/v1/settings/tiers", json=payload).status_code == 422


def test_tier_threshold_change_affects_classification(client):
    """把 VIP 门槛降到 200，则现金消费 300 的客户从 regular 升为 vip。"""
    c = client.post("/api/v1/customers", json={"name": "门槛测试"}).json()
    p = client.post("/api/v1/pets", json={"customer_id": c["id"], "name": "宠"}).json()
    client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "food", "amount": "300.00",
              "occurred_on": "2026-06-01", "pay_method": "cash"},
    )
    # 默认 VIP=500，300 → regular
    assert client.get(f"/api/v1/customers/{c['id']}/summary").json()["customer_type"] == "regular"
    # 降低门槛到 200
    client.put("/api/v1/settings/tiers", json={
        "vip_amount": "200", "svip_amount": "1500", "supreme_amount": "8000",
        "vip_discount": 98, "svip_discount": 95, "supreme_discount": 90,
    })
    # 现在 300 → vip
    summary = client.get(f"/api/v1/customers/{c['id']}/summary").json()
    assert summary["customer_type"] == "vip"
    assert summary["discount"] == 98


def test_summary_returns_discount(client):
    c = client.post("/api/v1/customers", json={"name": "折扣展示"}).json()
    # 新客无折扣 → 100
    assert client.get(f"/api/v1/customers/{c['id']}/summary").json()["discount"] == 100
