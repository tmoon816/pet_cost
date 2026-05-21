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


def test_pet_list_returns_last_visit_at(client):
    """列表返回 last_visit_at：取宠物名下 cost_records.occurred_on 的最大值，无消费为 None。"""
    customer = client.post("/api/v1/customers", json={"name": "老张"}).json()
    pet_with_costs = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "小包"}
    ).json()
    pet_no_costs = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "大友"}
    ).json()

    # 为 pet_with_costs 创 3 条消费，期望 last_visit_at = 2026-05-10（最大值）
    for occurred_on in ("2026-03-01", "2026-05-10", "2026-04-22"):
        resp = client.post(
            "/api/v1/costs",
            json={
                "pet_id": pet_with_costs["id"],
                "category_code": "food",
                "amount": "50.00",
                "occurred_on": occurred_on,
            },
        )
        assert resp.status_code == 201

    listed = client.get(
        "/api/v1/pets", params={"customer_id": customer["id"]}
    ).json()
    assert listed["total"] == 2
    by_id = {item["id"]: item for item in listed["items"]}
    assert by_id[pet_with_costs["id"]]["last_visit_at"] == "2026-05-10"
    assert by_id[pet_no_costs["id"]]["last_visit_at"] is None
