def test_create_budget_global(client):
    data = {
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00",
    }
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 200
    res = response.json()
    assert res["type"] == "global"
    assert res["amount"] == "5000.00"
    assert res["spent"] == "0"
    assert res["remaining"] == "5000.00"
    assert res["overspent"] is False


def test_create_budget_duplicate(client):
    data = {
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00",
    }
    assert client.post("/api/v1/budgets", json=data).status_code == 200
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 409
    assert response.json()["detail"] == "budget_already_exists"


def _create_customer_and_pet(client):
    customer_resp = client.post("/api/v1/customers", json={"name": "测试客户", "phone": "13900000002"})
    assert customer_resp.status_code == 201
    customer_id = customer_resp.json()["id"]
    pet_resp = client.post(
        "/api/v1/pets",
        json={"customer_id": customer_id, "name": "测试宠物", "species": "dog", "breed": "金毛"},
    )
    assert pet_resp.status_code == 201
    return customer_id, pet_resp.json()["id"]


def test_create_budget_pet(client):
    _, pet_id = _create_customer_and_pet(client)
    data = {
        "type": "pet",
        "target_id": str(pet_id),
        "year": 2026,
        "month": 5,
        "amount": "2000.00",
    }
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 200
    res = response.json()
    assert res["type"] == "pet"
    assert res["target_id"] == str(pet_id)


def test_create_budget_category(client):
    data = {
        "type": "category",
        "target_id": "food",
        "year": 2026,
        "month": 5,
        "amount": "1000.00",
    }
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 200
    res = response.json()
    assert res["type"] == "category"
    assert res["target_id"] == "food"


def test_list_budgets_by_month(client):
    client.post("/api/v1/budgets", json={
        "type": "global", "target_id": None, "year": 2026, "month": 5, "amount": "5000.00",
    })
    client.post("/api/v1/budgets", json={
        "type": "category", "target_id": "food", "year": 2026, "month": 5, "amount": "1000.00",
    })
    response = client.get("/api/v1/budgets?year=2026&month=5")
    assert response.status_code == 200
    res = response.json()
    assert len(res) >= 2
    types = [item["type"] for item in res]
    assert "global" in types
    assert "category" in types


def test_get_budget_detail(client):
    create_res = client.post("/api/v1/budgets", json={
        "type": "global", "target_id": None, "year": 2026, "month": 5, "amount": "5000.00",
    })
    assert create_res.status_code == 200
    budget_id = create_res.json()["id"]
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 200
    assert response.json()["id"] == budget_id


def test_update_budget(client):
    create_res = client.post("/api/v1/budgets", json={
        "type": "global", "target_id": None, "year": 2026, "month": 5, "amount": "5000.00",
    })
    budget_id = create_res.json()["id"]
    response = client.patch(f"/api/v1/budgets/{budget_id}", json={"amount": "6000.00"})
    assert response.status_code == 200
    assert response.json()["amount"] == "6000.00"
    assert response.json()["remaining"] == "6000.00"


def test_delete_budget(client):
    create_res = client.post("/api/v1/budgets", json={
        "type": "global", "target_id": None, "year": 2026, "month": 5, "amount": "5000.00",
    })
    budget_id = create_res.json()["id"]
    response = client.delete(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 204
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 404


def test_budget_spent_calculation(client):
    _, pet_id = _create_customer_and_pet(client)
    create_res = client.post("/api/v1/budgets", json={
        "type": "pet", "target_id": str(pet_id), "year": 2026, "month": 5, "amount": "2000.00",
    })
    budget_id = create_res.json()["id"]

    client.post("/api/v1/costs", json={
        "pet_id": pet_id, "category_code": "food", "amount": "100.00", "occurred_on": "2026-05-10",
    })
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 200
    res = response.json()
    assert res["spent"] == "100.00"
    assert res["remaining"] == "1900.00"
    assert res["overspent"] is False

    client.post("/api/v1/costs", json={
        "pet_id": pet_id, "category_code": "food", "amount": "2000.00", "occurred_on": "2026-05-15",
    })
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 200
    res = response.json()
    assert res["spent"] == "2100.00"
    assert res["remaining"] == "-100.00"
    assert res["overspent"] is True
