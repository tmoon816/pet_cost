def test_create_pet_requires_existing_customer(client):
    resp = client.post("/api/v1/pets", json={"customer_id": 9999, "name": "鬼宠"})
    assert resp.status_code == 404


def test_pet_crud_and_filter(client):
    c1 = client.post("/api/v1/customers", json={"name": "客户1"}).json()
    c2 = client.post("/api/v1/customers", json={"name": "客户2"}).json()
    p1 = client.post("/api/v1/pets", json={"customer_id": c1["id"], "name": "毛毛"}).json()
    client.post("/api/v1/pets", json={"customer_id": c2["id"], "name": "豆豆"})

    listed = client.get("/api/v1/pets", params={"customer_id": c1["id"]}).json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == p1["id"]

    updated = client.patch(f"/api/v1/pets/{p1['id']}", json={"breed": "柯基"})
    assert updated.status_code == 200
    assert updated.json()["breed"] == "柯基"

    assert client.delete(f"/api/v1/pets/{p1['id']}").status_code == 204
    assert client.get(f"/api/v1/pets/{p1['id']}").status_code == 404


def test_pet_cascade_delete_removes_costs(client):
    customer = client.post("/api/v1/customers", json={"name": "客"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "皮皮"}
    ).json()
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "toy",
            "amount": "30.00",
            "occurred_on": "2026-04-15",
        },
    ).json()

    client.delete(f"/api/v1/pets/{pet['id']}")
    assert client.get(f"/api/v1/costs/{cost['id']}").status_code == 404
