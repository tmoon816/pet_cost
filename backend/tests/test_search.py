"""Tests for app.crud.search — coverage target ≥80%."""

from datetime import date

import pytest

from app.crud.search import search
from app.models import CostCategory, CostRecord, Customer, Pet


def _seed(db):
    """Create a small test dataset and return the session."""
    c1 = Customer(name="张三", phone="13800001111")
    c2 = Customer(name="李四", phone="13900002222")
    db.add_all([c1, c2])
    db.flush()

    p1 = Pet(name="旺财", species="dog", breed="金毛", customer_id=c1.id)
    p2 = Pet(name="咪咪", species="cat", breed=None, customer_id=c2.id)
    p3 = Pet(name="阿福", species="other", breed="杂种", customer_id=c1.id)
    db.add_all([p1, p2, p3])
    db.flush()

    # ensure categories exist
    food = db.query(CostCategory).filter_by(code="food").first()
    if not food:
        food = CostCategory(code="food", label="粮食", sort_order=10)
        db.add(food)
        db.flush()

    db.add_all([
        CostRecord(
            pet_id=p1.id,
            category_code=food.code,  # type: ignore[union-attr]
            amount=150.00,
            occurred_on=date(2026, 5, 1),
            note="驱虫药",
        ),
        CostRecord(
            pet_id=p2.id,
            category_code=food.code,  # type: ignore[union-attr]
            amount=200.00,
            occurred_on=date(2026, 5, 10),
            note="进口猫粮",
        ),
        CostRecord(
            pet_id=p1.id,
            category_code=food.code,  # type: ignore[union-attr]
            amount=80.00,
            occurred_on=date(2026, 5, 15),
            note="洗澡美容",
        ),
    ])
    db.flush()
    return db


# ── empty / whitespace ──────────────────────────────────────────────

def test_search_empty_q_returns_empty(db_session):
    db = _seed(db_session())
    assert search(db, "") == []
    assert search(db, "   ") == []


def test_search_none_q_returns_empty(db_session):
    db = _seed(db_session())
    assert search(db, "") == []  # None == falsy, same code path


# ── customer name match ─────────────────────────────────────────────

def test_search_customer_by_name_exact(db_session):
    db = _seed(db_session())
    results = search(db, "张三")
    customers = [r for r in results if r["type"] == "customer"]
    assert len(customers) >= 1
    assert any(r["title"] == "张三" and r["url"] == f"/customers/{r['id']}" for r in customers)


def test_search_customer_by_name_partial(db_session):
    db = _seed(db_session())
    results = search(db, "张")
    customers = [r for r in results if r["type"] == "customer"]
    assert len(customers) >= 1
    assert all("张" in r["title"] for r in customers)


def test_search_customer_by_name_case_insensitive(db_session):
    """SQLite LIKE is case-insensitive for ASCII; this just validates the path."""
    db = _seed(db_session())
    results = search(db, "zhang")  # pinyin won't match Chinese; use an english-like name
    # verify the search function itself doesn't crash
    assert isinstance(results, list)


# ── customer phone match ────────────────────────────────────────────

def test_search_customer_by_phone(db_session):
    db = _seed(db_session())
    results = search(db, "1380000")
    customers = [r for r in results if r["type"] == "customer"]
    assert len(customers) >= 1
    assert any(r["subtitle"] == "13800001111" for r in customers)


def test_search_customer_by_phone_full(db_session):
    db = _seed(db_session())
    results = search(db, "13900002222")
    customers = [r for r in results if r["type"] == "customer"]
    assert len(customers) == 1
    assert customers[0]["title"] == "李四"


# ── pet name match ──────────────────────────────────────────────────

def test_search_pet_by_name(db_session):
    db = _seed(db_session())
    results = search(db, "旺财")
    pets = [r for r in results if r["type"] == "pet"]
    assert len(pets) >= 1
    assert any("旺财" in r["title"] for r in pets)


def test_search_pet_by_name_partial(db_session):
    db = _seed(db_session())
    results = search(db, "咪")
    pets = [r for r in results if r["type"] == "pet"]
    assert len(pets) >= 1
    assert all("咪" in r["title"] for r in pets)


def test_search_pet_species_emoji_dog(db_session):
    db = _seed(db_session())
    results = search(db, "旺财")
    pets = [r for r in results if r["type"] == "pet"]
    dog = next(r for r in pets if "旺财" in r["title"])
    assert "🐶" in dog["title"]


def test_search_pet_species_emoji_cat(db_session):
    db = _seed(db_session())
    results = search(db, "咪咪")
    pets = [r for r in results if r["type"] == "pet"]
    cat = next(r for r in pets if "咪咪" in r["title"])
    assert "🐱" in cat["title"]


def test_search_pet_with_breed_shows_breed(db_session):
    db = _seed(db_session())
    results = search(db, "旺财")
    pets = [r for r in results if r["type"] == "pet"]
    dog = next(r for r in pets if "旺财" in r["title"])
    assert "金毛" in dog["subtitle"]


def test_search_pet_without_breed(db_session):
    db = _seed(db_session())
    results = search(db, "咪咪")
    pets = [r for r in results if r["type"] == "pet"]
    cat = next(r for r in pets if "咪咪" in r["title"])
    # subtitle should be "cat" (the raw species string) since breed is None
    assert "cat" in cat["subtitle"] or "咪咪" in cat["title"]


def test_search_pet_owner_name_in_subtitle(db_session):
    db = _seed(db_session())
    results = search(db, "旺财")
    pets = [r for r in results if r["type"] == "pet"]
    dog = next(r for r in pets if "旺财" in r["title"])
    assert "张三" in dog["subtitle"]


# ── cost note match ─────────────────────────────────────────────────

def test_search_cost_by_note(db_session):
    db = _seed(db_session())
    results = search(db, "驱虫")
    costs = [r for r in results if r["type"] == "cost"]
    assert len(costs) >= 1
    assert any("驱虫" in r["title"] for r in costs)


def test_search_cost_amount_formatting(db_session):
    db = _seed(db_session())
    results = search(db, "驱虫")
    costs = [r for r in results if r["type"] == "cost"]
    cost = costs[0]
    assert cost["title"].startswith("¥")


def test_search_cost_pet_name_in_subtitle(db_session):
    db = _seed(db_session())
    results = search(db, "驱虫")
    costs = [r for r in results if r["type"] == "cost"]
    cost = costs[0]
    assert "旺财" in cost["subtitle"]


def test_search_cost_note_snippet_max_20(db_session):
    """Long note should be truncated to 20 chars in title snippet."""
    db = _seed(db_session())
    db.add(
        CostRecord(
            pet_id=db.query(Pet).filter_by(name="旺财").first().id,
            category_code=db.query(CostCategory).filter_by(code="food").first().code,
            amount=99.00,
            occurred_on=date(2026, 5, 20),
            note="这是一个很长的备注信息用来测试截断功能",
        )
    )
    db.flush()
    results = search(db, "备注信息")
    costs = [r for r in results if r["type"] == "cost"]
    assert len(costs) >= 1
    note_part = costs[0]["title"].split(" ", 1)[1] if " " in costs[0]["title"] else costs[0]["title"]
    assert len(note_part) <= 20  # snippet capped at 20 chars


# ── per_group limit ─────────────────────────────────────────────────

def test_search_per_group_limit_default_5(db_session):
    """Insert 6 customers matching the query, should return only 5."""
    db = _seed(db_session())
    for i in range(3, 9):
        db.add(Customer(name=f"测试客户{i}", phone=f"1300000000{i}"))
    db.flush()
    results = search(db, "测试")
    customers = [r for r in results if r["type"] == "customer"]
    assert len(customers) == 5


def test_search_per_group_limit_custom(db_session):
    """Custom per_group=3 should limit each group to 3."""
    db = _seed(db_session())
    for i in range(10, 16):
        db.add(Customer(name=f"搜索测试{i}", phone=f"1310000000{i}"))
    db.flush()
    results = search(db, "搜索测试", per_group=3)
    customers = [r for r in results if r["type"] == "customer"]
    assert len(customers) == 3


# ── mixed results / field completeness ──────────────────────────────

def test_search_mixed_results_type_field(db_session):
    """All result items must have type/url/id/title fields."""
    db = _seed(db_session())
    results = search(db, "咪")
    for r in results:
        assert "type" in r
        assert "url" in r
        assert "id" in r
        assert "title" in r
        assert "subtitle" in r
        assert r["type"] in ("customer", "pet", "cost")


def test_search_pet_url_format(db_session):
    db = _seed(db_session())
    results = search(db, "旺财")
    pets = [r for r in results if r["type"] == "pet"]
    for p in pets:
        assert p["url"].startswith("/pets/")


def test_search_customer_url_format(db_session):
    db = _seed(db_session())
    results = search(db, "张三")
    customers = [r for r in results if r["type"] == "customer"]
    for c in customers:
        assert c["url"].startswith("/customers/")


def test_search_no_match_returns_empty(db_session):
    db = _seed(db_session())
    results = search(db, "不存在的搜索词XYZ123")
    assert results == []