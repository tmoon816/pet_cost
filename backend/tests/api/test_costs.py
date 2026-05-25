import pytest


@pytest.fixture
def customer_and_pet(client):
    customer = client.post("/api/v1/customers", json={"name": "客户"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "毛毛"}
    ).json()
    return customer, pet


def test_cost_create_and_filters(client, customer_and_pet):
    customer, pet = customer_and_pet
    payload = {
        "pet_id": pet["id"],
        "category_code": "food",
        "amount": "120.50",
        "occurred_on": "2026-05-10",
    }
    resp = client.post("/api/v1/costs", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount"] == "120.50"

    other_cat = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "medical",
            "amount": "300.00",
            "occurred_on": "2026-03-01",
        },
    )
    assert other_cat.status_code == 201

    by_cat = client.get("/api/v1/costs", params={"category": "food"}).json()
    assert by_cat["total"] == 1
    assert by_cat["items"][0]["category_code"] == "food"

    by_pet = client.get("/api/v1/costs", params={"pet_id": pet["id"]}).json()
    assert by_pet["total"] == 2

    by_customer = client.get(
        "/api/v1/costs", params={"customer_id": customer["id"]}
    ).json()
    assert by_customer["total"] == 2

    in_window = client.get(
        "/api/v1/costs", params={"start": "2026-05-01", "end": "2026-05-31"}
    ).json()
    assert in_window["total"] == 1
    assert in_window["items"][0]["occurred_on"] == "2026-05-10"


def test_cost_create_with_unknown_pet(client):
    resp = client.post(
        "/api/v1/costs",
        json={
            "pet_id": 9999,
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-10",
        },
    )
    assert resp.status_code == 404


def test_cost_create_with_unknown_category(client, customer_and_pet):
    _, pet = customer_and_pet
    resp = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "unknown",
            "amount": "10.00",
            "occurred_on": "2026-05-10",
        },
    )
    assert resp.status_code == 404


def test_cost_update_and_delete(client, customer_and_pet):
    _, pet = customer_and_pet
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-10",
        },
    ).json()

    upd = client.patch(f"/api/v1/costs/{cost['id']}", json={"amount": "55.55", "note": "改了"})
    assert upd.status_code == 200
    assert upd.json()["amount"] == "55.55"
    assert upd.json()["note"] == "改了"

    assert client.delete(f"/api/v1/costs/{cost['id']}").status_code == 204
    assert client.get(f"/api/v1/costs/{cost['id']}").status_code == 404


def test_list_costs_returns_pet_name(client, customer_and_pet):
    """Task 2: 账单列表必须返回 pet_name，让前端不用再 N+1 反查。"""
    _, pet = customer_and_pet
    client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "food",
            "amount": "12.34",
            "occurred_on": "2026-05-15",
        },
    )
    body = client.get("/api/v1/costs").json()
    assert body["total"] >= 1
    assert all("pet_name" in item for item in body["items"])
    assert body["items"][0]["pet_name"] == pet["name"]


def test_costs_batch_creates_n_records(client):
    """T-029: 同金额同分类同日期，给多只宠物批量开单。"""
    customer = client.post("/api/v1/customers", json={"name": "多宠主"}).json()
    p1 = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "豆豆"}
    ).json()
    p2 = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "团团"}
    ).json()

    resp = client.post(
        "/api/v1/costs/batch",
        json={
            "pet_ids": [p1["id"], p2["id"]],
            "category_code": "grooming",
            "amount": "80.00",
            "occurred_on": "2026-05-25",
            "note": "双狗洗澡",
        },
    )
    assert resp.status_code == 201
    items = resp.json()
    assert len(items) == 2
    assert {it["pet_id"] for it in items} == {p1["id"], p2["id"]}
    assert all(it["amount"] == "80.00" for it in items)
    # 列表里应当能查到这两条
    listed = client.get("/api/v1/costs", params={"customer_id": customer["id"]}).json()
    assert listed["total"] == 2


def test_costs_batch_dedupes_pet_ids(client):
    """T-029: pet_ids 内重复的 id 应去重，避免同一只宠物录两条。"""
    customer = client.post("/api/v1/customers", json={"name": "C"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "P"}
    ).json()
    resp = client.post(
        "/api/v1/costs/batch",
        json={
            "pet_ids": [pet["id"], pet["id"], pet["id"]],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-25",
        },
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 1


def test_costs_batch_rolls_back_on_unknown_pet(client):
    """T-029: 任一 pet 不存在，整批不落库（事务原子）。"""
    customer = client.post("/api/v1/customers", json={"name": "C"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "P"}
    ).json()
    before = client.get("/api/v1/costs").json()["total"]

    resp = client.post(
        "/api/v1/costs/batch",
        json={
            "pet_ids": [pet["id"], 999999],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-25",
        },
    )
    assert resp.status_code == 404
    after = client.get("/api/v1/costs").json()["total"]
    assert after == before


def test_costs_batch_validates_unknown_category(client):
    customer = client.post("/api/v1/customers", json={"name": "C"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "P"}
    ).json()
    resp = client.post(
        "/api/v1/costs/batch",
        json={
            "pet_ids": [pet["id"]],
            "category_code": "ghost",
            "amount": "10.00",
            "occurred_on": "2026-05-25",
        },
    )
    assert resp.status_code == 404


def test_costs_batch_requires_at_least_one_pet(client):
    resp = client.post(
        "/api/v1/costs/batch",
        json={
            "pet_ids": [],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-25",
        },
    )
    assert resp.status_code == 422
