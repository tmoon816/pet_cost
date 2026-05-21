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
