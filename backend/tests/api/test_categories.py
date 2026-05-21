def test_list_default_categories(client):
    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    codes = [c["code"] for c in resp.json()]
    assert codes == ["food", "medical", "grooming", "toy", "other"]


def test_create_duplicate_category_returns_409(client):
    resp = client.post(
        "/api/v1/categories", json={"code": "food", "label": "Food", "sort_order": 1}
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["detail"] == "category_code_exists"


def test_create_update_delete_category(client):
    new = client.post(
        "/api/v1/categories",
        json={"code": "training", "label": "训练", "sort_order": 50},
    )
    assert new.status_code == 201

    upd = client.patch("/api/v1/categories/training", json={"label": "行为训练"})
    assert upd.status_code == 200
    assert upd.json()["label"] == "行为训练"

    delete = client.delete("/api/v1/categories/training")
    assert delete.status_code == 204
    assert client.get("/api/v1/categories").json().__len__() == 5


def test_delete_referenced_category_returns_409(client):
    customer = client.post("/api/v1/customers", json={"name": "C"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "P"}
    ).json()
    client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-01-01",
        },
    )

    resp = client.delete("/api/v1/categories/food")
    assert resp.status_code == 409
    assert resp.json()["detail"]["detail"] == "category_in_use"
