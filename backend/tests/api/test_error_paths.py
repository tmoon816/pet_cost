"""T-002: 集中补 API 层 404/422/参数校验等 error path 测试。

只新增测试用例，不修改任何业务源码。
每个被测函数同时覆盖到 1 个 happy path（已存在 / 此处再验一次） + 1 个 error path。
"""

import pytest


# ---------- Pets ----------


def test_get_pet_not_found_returns_404(client):
    """error path: GET 不存在的 pet 必须 404。"""
    resp = client.get("/api/v1/pets/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "pet_not_found"


def test_update_pet_not_found_returns_404(client):
    """error path: PATCH 不存在的 pet 必须 404，且不能造成 500。"""
    resp = client.patch("/api/v1/pets/999999", json={"breed": "柯基"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "pet_not_found"


def test_update_pet_to_unknown_customer_returns_404(client):
    """error path: PATCH 把 pet 的 customer_id 改成不存在的 customer 必须 404。"""
    c = client.post("/api/v1/customers", json={"name": "宿主A"}).json()
    p = client.post(
        "/api/v1/pets", json={"customer_id": c["id"], "name": "毛毛"}
    ).json()

    resp = client.patch(
        f"/api/v1/pets/{p['id']}", json={"customer_id": 999999}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "customer_not_found"


def test_delete_pet_not_found_returns_404(client):
    """error path: DELETE 不存在的 pet 必须 404。"""
    resp = client.delete("/api/v1/pets/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "pet_not_found"


def test_create_pet_happy_path(client):
    """happy path 兜底: 正常创建 pet 应当 201 并返回 customer_id。"""
    c = client.post("/api/v1/customers", json={"name": "宿主"}).json()
    resp = client.post(
        "/api/v1/pets", json={"customer_id": c["id"], "name": "皮皮"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["customer_id"] == c["id"]
    assert body["name"] == "皮皮"


# ---------- Costs ----------


@pytest.fixture
def _pet(client):
    c = client.post("/api/v1/customers", json={"name": "C"}).json()
    p = client.post(
        "/api/v1/pets", json={"customer_id": c["id"], "name": "P"}
    ).json()
    return p


def test_get_cost_not_found_returns_404(client):
    """error path: GET 不存在的 cost 必须 404。"""
    resp = client.get("/api/v1/costs/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "cost_not_found"


def test_update_cost_not_found_returns_404(client):
    """error path: PATCH 不存在的 cost 必须 404。"""
    resp = client.patch("/api/v1/costs/999999", json={"amount": "1.00"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "cost_not_found"


def test_update_cost_to_unknown_pet_returns_404(client, _pet):
    """error path: PATCH 把 cost 的 pet_id 改成不存在的 pet 必须 404。"""
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": _pet["id"],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-10",
        },
    ).json()
    resp = client.patch(
        f"/api/v1/costs/{cost['id']}", json={"pet_id": 999999}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "pet_not_found"


def test_update_cost_to_unknown_category_returns_404(client, _pet):
    """error path: PATCH 把 cost 的 category_code 改成不存在的 category 必须 404。"""
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": _pet["id"],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-10",
        },
    ).json()
    resp = client.patch(
        f"/api/v1/costs/{cost['id']}", json={"category_code": "nope"}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "category_not_found"


def test_delete_cost_not_found_returns_404(client):
    """error path: DELETE 不存在的 cost 必须 404。"""
    resp = client.delete("/api/v1/costs/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "cost_not_found"


def test_update_cost_happy_path_amount_only(client, _pet):
    """happy path 兜底: 仅改 amount 不触发 _validate_refs 也应当成功。"""
    cost = client.post(
        "/api/v1/costs",
        json={
            "pet_id": _pet["id"],
            "category_code": "food",
            "amount": "10.00",
            "occurred_on": "2026-05-10",
        },
    ).json()
    resp = client.patch(
        f"/api/v1/costs/{cost['id']}", json={"amount": "88.88"}
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == "88.88"


def test_list_costs_pagination_bounds(client, _pet):
    """error path: page_size 上限 100，超过应当被 422 拒绝。"""
    resp = client.get("/api/v1/costs", params={"page_size": 9999})
    assert resp.status_code == 422


# ---------- Budgets ----------


def test_get_budget_not_found_returns_404(client):
    resp = client.get("/api/v1/budgets/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "budget_not_found"


def test_update_budget_not_found_returns_404(client):
    resp = client.patch("/api/v1/budgets/999999", json={"amount": "100.00"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "budget_not_found"


def test_delete_budget_not_found_returns_404(client):
    resp = client.delete("/api/v1/budgets/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "budget_not_found"


# ---------- Categories ----------


def test_update_category_not_found_returns_404(client):
    resp = client.patch(
        "/api/v1/categories/no_such_code", json={"label": "x"}
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "category_not_found"


def test_delete_category_not_found_returns_404(client):
    resp = client.delete("/api/v1/categories/no_such_code")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "category_not_found"


# ---------- Customers ----------


def test_update_customer_not_found_returns_404(client):
    resp = client.patch("/api/v1/customers/999999", json={"name": "x"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "customer_not_found"


def test_delete_customer_not_found_returns_404(client):
    resp = client.delete("/api/v1/customers/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "customer_not_found"
