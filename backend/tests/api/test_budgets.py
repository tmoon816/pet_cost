import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_budget_global():
    """测试创建全局预算"""
    data = {
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00"
    }
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 200
    res = response.json()
    assert res["type"] == "global"
    assert res["amount"] == "5000.00"
    assert res["spent"] == "0"
    assert res["remaining"] == "5000.00"
    assert res["overspent"] is False

def test_create_budget_duplicate():
    """测试重复创建同一预算返回409"""
    data = {
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00"
    }
    # 第一次创建成功
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 200
    # 第二次创建失败
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 409
    assert response.json()["detail"] == "budget_already_exists"

def test_create_budget_pet():
    """测试创建单宠物预算"""
    # 先创建宠物
    pet_resp = client.post("/api/v1/pets", json={
        "customer_id": 1,
        "name": "测试宠物",
        "species": "dog",
        "breed": "金毛"
    })
    assert pet_resp.status_code == 201
    pet_id = pet_resp.json()["id"]
    # 创建宠物预算
    data = {
        "type": "pet",
        "target_id": str(pet_id),
        "year": 2026,
        "month": 5,
        "amount": "2000.00"
    }
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 200
    res = response.json()
    assert res["type"] == "pet"
    assert res["target_id"] == str(pet_id)

def test_create_budget_category():
    """测试创建分类预算"""
    data = {
        "type": "category",
        "target_id": "food",
        "year": 2026,
        "month": 5,
        "amount": "1000.00"
    }
    response = client.post("/api/v1/budgets", json=data)
    assert response.status_code == 200
    res = response.json()
    assert res["type"] == "category"
    assert res["target_id"] == "food"

def test_list_budgets_by_month():
    """测试按月份查询预算列表"""
    # 创建两个预算
    client.post("/api/v1/budgets", json={
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00"
    })
    client.post("/api/v1/budgets", json={
        "type": "category",
        "target_id": "food",
        "year": 2026,
        "month": 5,
        "amount": "1000.00"
    })
    # 查询
    response = client.get("/api/v1/budgets?year=2026&month=5")
    assert response.status_code == 200
    res = response.json()
    assert len(res) >= 2
    types = [item["type"] for item in res]
    assert "global" in types
    assert "category" in types

def test_get_budget_detail():
    """测试查询单个预算详情"""
    create_res = client.post("/api/v1/budgets", json={
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00"
    })
    budget_id = create_res.json()["id"]
    # 查询详情
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 200
    assert response.json()["id"] == budget_id

def test_update_budget():
    """测试更新预算金额"""
    create_res = client.post("/api/v1/budgets", json={
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00"
    })
    budget_id = create_res.json()["id"]
    # 更新
    response = client.patch(f"/api/v1/budgets/{budget_id}", json={
        "amount": "6000.00"
    })
    assert response.status_code == 200
    assert response.json()["amount"] == "6000.00"
    assert response.json()["remaining"] == "6000.00"

def test_delete_budget():
    """测试删除预算"""
    create_res = client.post("/api/v1/budgets", json={
        "type": "global",
        "target_id": None,
        "year": 2026,
        "month": 5,
        "amount": "5000.00"
    })
    budget_id = create_res.json()["id"]
    # 删除
    response = client.delete(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 204
    # 验证已删除
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 404

def test_budget_spent_calculation():
    """测试预算已花费金额计算正确"""
    # 先创建客户和宠物
    customer_resp = client.post("/api/v1/customers", json={"name": "测试客户", "phone": "13900000002"})
    customer_id = customer_resp.json()["id"]
    pet_resp = client.post("/api/v1/pets", json={
        "customer_id": customer_id,
        "name": "测试宠物",
        "species": "dog",
        "breed": "金毛"
    })
    pet_id = pet_resp.json()["id"]
    # 创建宠物预算
    create_res = client.post("/api/v1/budgets", json={
        "type": "pet",
        "target_id": str(pet_id),
        "year": 2026,
        "month": 5,
        "amount": "2000.00"
    })
    budget_id = create_res.json()["id"]
    # 新增一笔消费
    client.post("/api/v1/costs", json={
        "pet_id": pet_id,
        "category_code": "food",
        "amount": "100.00",
        "occurred_on": "2026-05-10"
    })
    # 查询预算，已花金额应该是100
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 200
    res = response.json()
    assert res["spent"] == "100.00"
    assert res["remaining"] == "1900.00"
    assert res["overspent"] is False
    # 再新增一笔超支的消费
    client.post("/api/v1/costs", json={
        "pet_id": pet_id,
        "category_code": "food",
        "amount": "2000.00",
        "occurred_on": "2026-05-15"
    })
    # 再次查询，应该超支
    response = client.get(f"/api/v1/budgets/{budget_id}")
    assert response.status_code == 200
    res = response.json()
    assert res["spent"] == "2100.00"
    assert res["remaining"] == "-100.00"
    assert res["overspent"] is True
