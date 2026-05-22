def test_create_and_get_customer(client):
    resp = client.post("/api/v1/customers", json={"name": "测试客户", "phone": "13900000001"})
    assert resp.status_code == 201
    body = resp.json()
    cid = body["id"]
    assert body["name"] == "测试客户"
    assert body["phone"] == "13900000001"
    assert "created_at" in body

    detail = client.get(f"/api/v1/customers/{cid}")
    assert detail.status_code == 200
    assert detail.json()["pets"] == []


def test_list_search_and_pagination(client):
    for name in ["张三", "李四", "王五"]:
        client.post("/api/v1/customers", json={"name": name})

    resp = client.get("/api/v1/customers", params={"q": "李"})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "李四"

    paged = client.get("/api/v1/customers", params={"page": 1, "page_size": 2})
    assert paged.status_code == 200
    assert paged.json()["page_size"] == 2
    assert len(paged.json()["items"]) == 2


def test_list_search_by_phone_fuzzy(client):
    """T-006 核实：GET /api/v1/customers 支持 phone 模糊匹配。"""
    client.post("/api/v1/customers", json={"name": "甲", "phone": "13811112222"})
    client.post("/api/v1/customers", json={"name": "乙", "phone": "13822223333"})
    client.post("/api/v1/customers", json={"name": "丙", "phone": "13911114444"})

    # 精准后 7 位
    exact = client.get("/api/v1/customers", params={"q": "11112222"})
    assert exact.status_code == 200
    body = exact.json()
    assert body["total"] == 1
    assert body["items"][0]["phone"] == "13811112222"

    # 中间片段模糊命中多个
    middle = client.get("/api/v1/customers", params={"q": "1111"})
    assert middle.status_code == 200
    phones = sorted(item["phone"] for item in middle.json()["items"])
    assert phones == ["13811112222", "13911114444"]

    # 手机号完全不匹配返回空
    miss = client.get("/api/v1/customers", params={"q": "99999999"})
    assert miss.status_code == 200
    assert miss.json()["total"] == 0


def test_phone_conflict_returns_409(client):
    a = client.post("/api/v1/customers", json={"name": "A", "phone": "13888888888"})
    assert a.status_code == 201
    existing_id = a.json()["id"]

    dup = client.post("/api/v1/customers", json={"name": "B", "phone": "13888888888"})
    assert dup.status_code == 409
    detail = dup.json()["detail"]
    assert detail["detail"] == "phone_exists"
    assert detail["existing_id"] == existing_id


def test_update_phone_conflict_returns_409(client):
    a = client.post("/api/v1/customers", json={"name": "A", "phone": "13800000001"}).json()
    b = client.post("/api/v1/customers", json={"name": "B", "phone": "13800000002"}).json()

    resp = client.patch(f"/api/v1/customers/{b['id']}", json={"phone": "13800000001"})
    assert resp.status_code == 409
    assert resp.json()["detail"]["existing_id"] == a["id"]

    same = client.patch(f"/api/v1/customers/{a['id']}", json={"phone": "13800000001", "name": "AA"})
    assert same.status_code == 200
    assert same.json()["name"] == "AA"


def test_get_missing_customer_returns_404(client):
    resp = client.get("/api/v1/customers/9999")
    assert resp.status_code == 404


def test_create_validation_error_returns_422(client):
    resp = client.post("/api/v1/customers", json={})
    assert resp.status_code == 422


def test_delete_cascades_pets_and_costs(client):
    customer = client.post("/api/v1/customers", json={"name": "级联客户"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": customer["id"], "name": "毛毛"}
    ).json()
    client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "food",
            "amount": "12.50",
            "occurred_on": "2026-05-01",
        },
    )

    resp = client.delete(f"/api/v1/customers/{customer['id']}")
    assert resp.status_code == 204

    assert client.get(f"/api/v1/pets/{pet['id']}").status_code == 404
    listed = client.get("/api/v1/costs", params={"pet_id": pet["id"]}).json()
    assert listed["total"] == 0


def test_customer_summary_happy_path(client):
    """T-007: 客户聚合卡片 — 累计金额/上次到店/总订单数。"""
    cust = client.post("/api/v1/customers", json={"name": "汇总测试"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": cust["id"], "name": "汪汪"}
    ).json()

    # 无消费记录：全部为 0 / None
    empty = client.get(f"/api/v1/customers/{cust['id']}/summary").json()
    assert empty["customer_id"] == cust["id"]
    assert empty["total_amount"] == "0"
    assert empty["last_visit_at"] is None
    assert empty["cost_count"] == 0

    # 写 3 笔消费，跨日期
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet["id"], "category_code": "food", "amount": "12.50", "occurred_on": "2026-05-01"},
    )
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet["id"], "category_code": "medical", "amount": "100.00", "occurred_on": "2026-05-10"},
    )
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet["id"], "category_code": "toy", "amount": "5.25", "occurred_on": "2026-05-05"},
    )

    summary = client.get(f"/api/v1/customers/{cust['id']}/summary").json()
    assert summary["customer_id"] == cust["id"]
    assert summary["total_amount"] == "117.75"
    assert summary["cost_count"] == 3
    assert summary["last_visit_at"].startswith("2026-05-10")


def test_customer_summary_404_when_missing(client):
    resp = client.get("/api/v1/customers/99999/summary")
    assert resp.status_code == 404


def test_customer_list_has_cost_flag(client):
    """T-008: 列表返回 has_cost；首次有消费即老客。"""
    # 新客：只创建客户，没有消费
    new_cust = client.post("/api/v1/customers", json={"name": "全新客户"}).json()

    # 老客：创建客户 + 宠物 + 1 笔消费
    old_cust = client.post("/api/v1/customers", json={"name": "回头客"}).json()
    pet = client.post(
        "/api/v1/pets", json={"customer_id": old_cust["id"], "name": "小黑"}
    ).json()
    client.post(
        "/api/v1/costs",
        json={
            "pet_id": pet["id"],
            "category_code": "food",
            "amount": "20.00",
            "occurred_on": "2026-05-15",
        },
    )

    body = client.get("/api/v1/customers").json()
    items_by_id = {it["id"]: it for it in body["items"]}
    assert items_by_id[new_cust["id"]]["has_cost"] is False
    assert items_by_id[old_cust["id"]]["has_cost"] is True


def test_recent_customers_returns_by_last_visit_desc_excludes_no_cost(client):
    """T-014：GET /api/v1/customers/recent 按「名下最近一次消费」倒序，无消费不返回，同人多条只计最近一次。"""
    # 创建 4 个客户。A/B/C 有消费，D 无消费。
    cust_a = client.post("/api/v1/customers", json={"name": "客户A"}).json()
    cust_b = client.post("/api/v1/customers", json={"name": "客户B"}).json()
    cust_c = client.post("/api/v1/customers", json={"name": "客户C"}).json()
    cust_d = client.post("/api/v1/customers", json={"name": "客户D无消费"}).json()

    pet_a = client.post("/api/v1/pets", json={"customer_id": cust_a["id"], "name": "a1"}).json()
    pet_b = client.post("/api/v1/pets", json={"customer_id": cust_b["id"], "name": "b1"}).json()
    pet_c = client.post("/api/v1/pets", json={"customer_id": cust_c["id"], "name": "c1"}).json()

    # A: 最早 (2026-05-01)
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_a["id"], "category_code": "food", "amount": "10", "occurred_on": "2026-05-01"},
    )
    # B: 最近 (2026-05-20)。为证明“同人多条取 max”，同时补一条更早的 2026-05-02
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_b["id"], "category_code": "food", "amount": "10", "occurred_on": "2026-05-02"},
    )
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_b["id"], "category_code": "food", "amount": "10", "occurred_on": "2026-05-20"},
    )
    # C: 中间 (2026-05-10)
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_c["id"], "category_code": "food", "amount": "10", "occurred_on": "2026-05-10"},
    )

    resp = client.get("/api/v1/customers/recent")
    assert resp.status_code == 200
    items = resp.json()
    ids = [it["id"] for it in items]
    # 排序：B (05-20) > C (05-10) > A (05-01)；D 不出现
    assert ids == [cust_b["id"], cust_c["id"], cust_a["id"]]
    assert cust_d["id"] not in ids
    # 默认 limit=5，这里只有 3 个有消费的客户，都该返回
    assert len(items) == 3

    # 验证 limit 参数生效
    resp2 = client.get("/api/v1/customers/recent", params={"limit": 2})
    assert resp2.status_code == 200
    assert [it["id"] for it in resp2.json()] == [cust_b["id"], cust_c["id"]]


def test_customer_list_sort_by_total_amount(client):
    """T-015：sort_by=total_amount&sort_dir=desc|asc 生效，默认仍以 id DESC（created_at 代理）。"""
    # 创建 3 客户，各自补不同金额的消费；D 无消费 → total_amount=0
    cust_a = client.post("/api/v1/customers", json={"name": "小金额 A"}).json()
    cust_b = client.post("/api/v1/customers", json={"name": "大金额 B"}).json()
    cust_c = client.post("/api/v1/customers", json={"name": "中金额 C"}).json()
    cust_d = client.post("/api/v1/customers", json={"name": "无消费 D"}).json()

    pet_a = client.post("/api/v1/pets", json={"customer_id": cust_a["id"], "name": "a"}).json()
    pet_b = client.post("/api/v1/pets", json={"customer_id": cust_b["id"], "name": "b"}).json()
    pet_c = client.post("/api/v1/pets", json={"customer_id": cust_c["id"], "name": "c"}).json()

    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_a["id"], "category_code": "food", "amount": "10.00", "occurred_on": "2026-05-01"},
    )
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_b["id"], "category_code": "food", "amount": "100.00", "occurred_on": "2026-05-01"},
    )
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_b["id"], "category_code": "food", "amount": "50.00", "occurred_on": "2026-05-02"},
    )  # B 总额 150
    client.post(
        "/api/v1/costs",
        json={"pet_id": pet_c["id"], "category_code": "food", "amount": "30.00", "occurred_on": "2026-05-01"},
    )

    # 默认排序：id DESC（= created_at 倒序代理），后创建的在前。仅验证本用例创建的 4 个。
    default = client.get("/api/v1/customers").json()
    ids_in_default = [
        it["id"] for it in default["items"] if it["id"] in {cust_a["id"], cust_b["id"], cust_c["id"], cust_d["id"]}
    ]
    assert ids_in_default == [cust_d["id"], cust_c["id"], cust_b["id"], cust_a["id"]]

    # total_amount 字段被正确计算
    by_id = {it["id"]: it for it in default["items"]}
    assert by_id[cust_a["id"]]["total_amount"] == "10.00"
    assert by_id[cust_b["id"]]["total_amount"] == "150.00"
    assert by_id[cust_c["id"]]["total_amount"] == "30.00"
    assert by_id[cust_d["id"]]["total_amount"] == "0"

    # 按金额 desc：B(150) > C(30) > A(10) > D(0)
    desc = client.get("/api/v1/customers", params={"sort_by": "total_amount", "sort_dir": "desc"}).json()
    ids_desc = [
        it["id"] for it in desc["items"] if it["id"] in {cust_a["id"], cust_b["id"], cust_c["id"], cust_d["id"]}
    ]
    assert ids_desc == [cust_b["id"], cust_c["id"], cust_a["id"], cust_d["id"]]

    # 按金额 asc：D(0) < A(10) < C(30) < B(150)
    asc = client.get("/api/v1/customers", params={"sort_by": "total_amount", "sort_dir": "asc"}).json()
    ids_asc = [
        it["id"] for it in asc["items"] if it["id"] in {cust_a["id"], cust_b["id"], cust_c["id"], cust_d["id"]}
    ]
    assert ids_asc == [cust_d["id"], cust_a["id"], cust_c["id"], cust_b["id"]]

    # 非法 sort_by/sort_dir 被 pattern 拦下
    bad = client.get("/api/v1/customers", params={"sort_by": "hack"})
    assert bad.status_code == 422
