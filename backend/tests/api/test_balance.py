"""储值功能测试：充值（含赠送）、扣款、余额不足、删单/改单退款、流水账本。"""
import pytest


@pytest.fixture
def customer_and_pet(client):
    customer = client.post("/api/v1/customers", json={"name": "储值客户"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "毛毛"}
    ).json()
    return customer, pet


def _balance(client, cid):
    return client.get(f"/api/v1/customers/{cid}").json()["balance"]


def test_new_customer_has_zero_balance(client):
    c = client.post("/api/v1/customers", json={"name": "新客"}).json()
    assert c["balance"] == "0.00"


def test_recharge_with_bonus(client, customer_and_pet):
    customer, _ = customer_and_pet
    resp = client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "500.00", "bonus_amount": "50.00", "channel": "wechat"},
    )
    assert resp.status_code == 200
    assert resp.json()["balance"] == "550.00"
    # 流水记一条 recharge
    txns = client.get(f"/api/v1/customers/{customer['id']}/transactions").json()
    assert txns["total"] == 1
    t = txns["items"][0]
    assert t["type"] == "recharge"
    assert t["amount"] == "550.00"
    assert t["bonus_amount"] == "50.00"
    assert t["channel"] == "wechat"
    assert t["balance_after"] == "550.00"


def test_recharge_invalid_channel_rejected(client, customer_and_pet):
    customer, _ = customer_and_pet
    resp = client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "100.00", "channel": "paypal"},
    )
    assert resp.status_code == 422


def test_recharge_nonpositive_rejected(client, customer_and_pet):
    customer, _ = customer_and_pet
    resp = client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "0", "channel": "cash"},
    )
    assert resp.status_code == 422


def test_order_deducts_balance(client, customer_and_pet):
    customer, pet = customer_and_pet
    client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "200.00", "channel": "alipay"},
    )
    resp = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "grooming",
            "amount": "80.00",
            "occurred_on": "2026-06-01",
            "pay_method": "balance",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["pay_method"] == "balance"
    assert _balance(client, customer["id"]) == "120.00"
    # 流水：1 充值 + 1 消费
    txns = client.get(f"/api/v1/customers/{customer['id']}/transactions").json()
    assert txns["total"] == 2
    consume = [t for t in txns["items"] if t["type"] == "consume"][0]
    assert consume["amount"] == "-80.00"
    assert consume["balance_after"] == "120.00"
    assert consume["cost_id"] == resp.json()["id"]


def test_order_insufficient_balance_rejected_and_no_record(client, customer_and_pet):
    customer, pet = customer_and_pet
    client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "50.00", "channel": "cash"},
    )
    before = client.get("/api/v1/costs", params={"pet_id": pet["id"]}).json()["total"]
    resp = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "grooming",
            "amount": "80.00",
            "occurred_on": "2026-06-01",
            "pay_method": "balance",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["detail"] == "insufficient_balance"
    # 关键：余额不变，订单未落库（事务回滚）
    assert _balance(client, customer["id"]) == "50.00"
    after = client.get("/api/v1/costs", params={"pet_id": pet["id"]}).json()["total"]
    assert after == before


def test_cash_order_does_not_touch_balance(client, customer_and_pet):
    customer, pet = customer_and_pet
    client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "100.00", "channel": "cash"},
    )
    resp = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "food",
            "amount": "30.00",
            "occurred_on": "2026-06-01",
            "pay_method": "cash",
        },
    )
    assert resp.status_code == 201
    assert _balance(client, customer["id"]) == "100.00"


def test_delete_balance_order_refunds(client, customer_and_pet):
    customer, pet = customer_and_pet
    client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "200.00", "channel": "alipay"},
    )
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "grooming",
            "amount": "80.00",
            "occurred_on": "2026-06-01",
            "pay_method": "balance",
        },
    ).json()
    assert _balance(client, customer["id"]) == "120.00"
    assert client.delete(f"/api/v1/costs/{cost['id']}").status_code == 204
    # 自动退回
    assert _balance(client, customer["id"]) == "200.00"
    txns = client.get(f"/api/v1/customers/{customer['id']}/transactions").json()
    assert any(t["type"] == "refund" and t["amount"] == "80.00" for t in txns["items"])


def test_update_balance_order_amount_adjusts(client, customer_and_pet):
    customer, pet = customer_and_pet
    client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "200.00", "channel": "alipay"},
    )
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "grooming",
            "amount": "80.00",
            "occurred_on": "2026-06-01",
            "pay_method": "balance",
        },
    ).json()
    assert _balance(client, customer["id"]) == "120.00"
    # 金额从 80 改 100：应退 80 再扣 100 → 净余额 100
    upd = client.patch(f"/api/v1/costs/{cost['id']}", json={"amount": "100.00"})
    assert upd.status_code == 200
    assert _balance(client, customer["id"]) == "100.00"


def test_cash_to_balance_order_delete_no_refund(client, customer_and_pet):
    """现金单删除不退余额。"""
    customer, pet = customer_and_pet
    client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "100.00", "channel": "cash"},
    )
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "food",
            "amount": "30.00",
            "occurred_on": "2026-06-01",
            "pay_method": "cash",
        },
    ).json()
    client.delete(f"/api/v1/costs/{cost['id']}")
    assert _balance(client, customer["id"]) == "100.00"


def test_adjust_balance_up_and_down(client, customer_and_pet):
    customer, _ = customer_and_pet
    client.post(
        f"/api/v1/customers/{customer['id']}/recharge",
        json={"amount": "100.00", "channel": "cash"},
    )
    up = client.post(
        f"/api/v1/customers/{customer['id']}/balance/adjust",
        json={"amount": "20.00", "note": "补偿"},
    )
    assert up.status_code == 200
    assert up.json()["balance"] == "120.00"
    down = client.post(
        f"/api/v1/customers/{customer['id']}/balance/adjust",
        json={"amount": "-50.00"},
    )
    assert down.json()["balance"] == "70.00"


def test_adjust_cannot_go_negative(client, customer_and_pet):
    customer, _ = customer_and_pet
    resp = client.post(
        f"/api/v1/customers/{customer['id']}/balance/adjust",
        json={"amount": "-10.00"},
    )
    assert resp.status_code == 400


def test_batch_order_deducts_each_customer(client):
    c1 = client.post("/api/v1/customers", json={"name": "甲"}).json()
    c2 = client.post("/api/v1/customers", json={"name": "乙"}).json()
    p1 = client.post("/api/v1/pets", json={"customer_id": c1["id"], "name": "A"}).json()
    p2 = client.post("/api/v1/pets", json={"customer_id": c2["id"], "name": "B"}).json()
    for c in (c1, c2):
        client.post(
            f"/api/v1/customers/{c['id']}/recharge",
            json={"amount": "100.00", "channel": "cash"},
        )
    resp = client.post(
        "/api/v1/costs/batch",
        json={
            "pet_ids": [p1["id"], p2["id"]],
            "category_code": "grooming",
            "amount": "30.00",
            "occurred_on": "2026-06-01",
            "pay_method": "balance",
        },
    )
    assert resp.status_code == 201
    assert _balance(client, c1["id"]) == "70.00"
    assert _balance(client, c2["id"]) == "70.00"


def test_batch_order_insufficient_rolls_back_all(client):
    c1 = client.post("/api/v1/customers", json={"name": "甲"}).json()
    c2 = client.post("/api/v1/customers", json={"name": "乙"}).json()
    p1 = client.post("/api/v1/pets", json={"customer_id": c1["id"], "name": "A"}).json()
    p2 = client.post("/api/v1/pets", json={"customer_id": c2["id"], "name": "B"}).json()
    client.post(
        f"/api/v1/customers/{c1['id']}/recharge",
        json={"amount": "100.00", "channel": "cash"},
    )
    # c2 没充值，余额 0，批量必失败
    resp = client.post(
        "/api/v1/costs/batch",
        json={
            "pet_ids": [p1["id"], p2["id"]],
            "category_code": "grooming",
            "amount": "30.00",
            "occurred_on": "2026-06-01",
            "pay_method": "balance",
        },
    )
    assert resp.status_code == 400
    # 整批回滚：c1 余额不动，没有任何订单落库
    assert _balance(client, c1["id"]) == "100.00"
    assert client.get("/api/v1/costs").json()["total"] == 0


# ===== 客户分层（按贡献金额：充值本金 + 现金消费）=====


def _make_customer_pet(client, name="层级客户"):
    c = client.post("/api/v1/customers", json={"name": name}).json()
    p = client.post("/api/v1/pets", json={"customer_id": c["id"], "name": "宠"}).json()
    return c, p


def _type(client, cid):
    return client.get(f"/api/v1/customers/{cid}/summary").json()["customer_type"]


def test_tier_new_customer_is_first_visit(client):
    c = client.post("/api/v1/customers", json={"name": "纯新客"}).json()
    assert _type(client, c["id"]) == "first_visit"


def test_tier_regular_below_vip(client):
    c, p = _make_customer_pet(client)
    client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "food", "amount": "100.00",
              "occurred_on": "2026-06-01", "pay_method": "cash"},
    )
    assert _type(client, c["id"]) == "regular"


def test_tier_vip_by_cash_consume(client):
    c, p = _make_customer_pet(client)
    client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "food", "amount": "500.00",
              "occurred_on": "2026-06-01", "pay_method": "cash"},
    )
    assert _type(client, c["id"]) == "vip"


def test_tier_vip_by_recharge_principal_excludes_bonus(client):
    """充500送50：贡献按本金500算，正好 VIP；赠送不算。"""
    c, _ = _make_customer_pet(client)
    client.post(
        f"/api/v1/customers/{c['id']}/recharge",
        json={"amount": "500.00", "bonus_amount": "50.00", "channel": "wechat"},
    )
    assert _type(client, c["id"]) == "vip"


def test_tier_balance_consume_not_double_counted(client):
    """充值500（VIP），再用储值消费300：仍是VIP，不会因消费叠加升档。"""
    c, p = _make_customer_pet(client)
    client.post(
        f"/api/v1/customers/{c['id']}/recharge",
        json={"amount": "500.00", "channel": "alipay"},
    )
    client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "grooming", "amount": "300.00",
              "occurred_on": "2026-06-01", "pay_method": "balance"},
    )
    # 贡献 = 充值本金 500 + 现金消费 0 = 500 → vip（储值消费的 300 不计）
    assert _type(client, c["id"]) == "vip"


def test_tier_svip(client):
    c, p = _make_customer_pet(client)
    client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "food", "amount": "2000.00",
              "occurred_on": "2026-06-01", "pay_method": "cash"},
    )
    assert _type(client, c["id"]) == "svip"


def test_tier_supreme(client):
    c, p = _make_customer_pet(client)
    client.post(
        f"/api/v1/customers/{c['id']}/recharge",
        json={"amount": "3000.00", "channel": "cash"},
    )
    client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "food", "amount": "2000.00",
              "occurred_on": "2026-06-01", "pay_method": "cash"},
    )
    # 3000 充值本金 + 2000 现金 = 5000 → 至尊
    assert _type(client, c["id"]) == "supreme"


def test_tier_shown_in_customer_list(client):
    c, p = _make_customer_pet(client, name="列表层级客户")
    client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "food", "amount": "800.00",
              "occurred_on": "2026-06-01", "pay_method": "cash"},
    )
    listed = client.get("/api/v1/customers", params={"q": "列表层级客户"}).json()
    row = [x for x in listed["items"] if x["id"] == c["id"]][0]
    assert row["customer_type"] == "vip"


def test_consume_records_discount_amount(client):
    """储值消费带折扣时，流水里记录 discount_amount，扣的是折后价。"""
    c, p = _make_customer_pet(client, name="折扣流水客户")
    # 充 1000 成为 VIP（默认 VIP=500，98折）
    client.post(
        f"/api/v1/customers/{c['id']}/recharge",
        json={"amount": "1000.00", "channel": "wechat"},
    )
    # 原价 100，VIP 98 折 → 实扣 98，省 2
    resp = client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "grooming", "amount": "98.00",
              "occurred_on": "2026-06-01", "pay_method": "balance",
              "discount_amount": "2.00"},
    )
    assert resp.status_code == 201
    txns = client.get(f"/api/v1/customers/{c['id']}/transactions").json()
    consume = [t for t in txns["items"] if t["type"] == "consume"][0]
    assert consume["amount"] == "-98.00"
    assert consume["discount_amount"] == "2.00"
    assert "省" in consume["note"]
    # 余额 1000 - 98 = 902
    assert _balance(client, c["id"]) == "902.00"


def test_order_stores_discount_amount(client):
    """订单本身记录 discount_amount，列表/详情可读。"""
    c, p = _make_customer_pet(client, name="订单折扣字段")
    client.post(
        f"/api/v1/customers/{c['id']}/recharge",
        json={"amount": "1000.00", "channel": "wechat"},
    )
    created = client.post(
        "/api/v1/costs",
        json={"pet_id": p["id"], "category_code": "grooming", "amount": "98.00",
              "occurred_on": "2026-06-01", "pay_method": "balance",
              "discount_amount": "2.00"},
    ).json()
    assert created["discount_amount"] == "2.00"
    # 列表也带该字段
    listed = client.get("/api/v1/costs", params={"customer_id": c["id"]}).json()
    assert listed["items"][0]["discount_amount"] == "2.00"
    # 单条详情
    got = client.get(f"/api/v1/costs/{created['id']}").json()
    assert got["discount_amount"] == "2.00"
