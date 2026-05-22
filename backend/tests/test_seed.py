"""Tests for app/seed.py — seed development data."""

from contextlib import contextmanager

import pytest
from sqlalchemy import delete, func, select

from app import seed
from app.models import CostCategory, CostRecord, Customer, Pet


@pytest.fixture
def seed_session(db_session):
    """Replace seed.SessionLocal so run() uses a fresh in-memory test session."""
    # db_session from conftest is a sessionmaker (class/factory).
    # Each call to db_session() creates a new actual Session.
    @contextmanager
    def _fake_session():
        session = db_session()
        try:
            yield session
        finally:
            session.close()

    original = seed.SessionLocal
    seed.SessionLocal = _fake_session
    try:
        yield db_session  # still a sessionmaker for queries
    finally:
        seed.SessionLocal = original


@contextmanager
def _query(ss_maker):
    """Get a fresh session from the sessionmaker for querying."""
    s = ss_maker()
    try:
        yield s
    finally:
        s.close()


def test_seed_run_creates_customers(seed_session):
    """run() should create 3 customers from CUSTOMER_PROFILES."""
    seed.run()
    with _query(seed_session) as s:
        count = s.scalar(select(func.count()).select_from(Customer))
        assert count == 3


def test_seed_run_creates_pets(seed_session):
    """run() should create the expected number of pets (1+2+2=5)."""
    seed.run()
    with _query(seed_session) as s:
        count = s.scalar(select(func.count()).select_from(Pet))
        assert count == 5


def test_seed_run_creates_cost_records(seed_session):
    """run() should create cost records for every pet."""
    seed.run()
    with _query(seed_session) as s:
        count = s.scalar(select(func.count()).select_from(CostRecord))
        assert count >= 40


def test_seed_run_assigns_correct_pet_ownership(seed_session):
    """Each pet should belong to one of the seeded customers."""
    seed.run()
    with _query(seed_session) as s:
        customers = s.scalars(select(Customer)).all()
        customer_ids = {c.id for c in customers}
        pets = s.scalars(select(Pet)).all()
        assert len(pets) > 0
        for pet in pets:
            assert pet.customer_id in customer_ids


def test_seed_run_every_cost_has_category(seed_session):
    """Every cost record should have a valid category_code."""
    seed.run()
    with _query(seed_session) as s:
        costs = s.scalars(select(CostRecord)).all()
        assert len(costs) > 0
        for cost in costs:
            assert cost.category_code is not None
            assert cost.category_code != ""


def test_seed_run_idempotent(seed_session):
    """Second run should also succeed (delete + re-insert)."""
    seed.run()
    with _query(seed_session) as s:
        first_pet_count = s.scalar(select(func.count()).select_from(Pet))
    seed.run()
    with _query(seed_session) as s:
        second_pet_count = s.scalar(select(func.count()).select_from(Pet))
        assert second_pet_count == first_pet_count


def test_seed_run_customers_have_names(seed_session):
    """Seeded customers should have the expected names."""
    seed.run()
    with _query(seed_session) as s:
        customers = s.scalars(select(Customer)).all()
        names = {c.name for c in customers}
        assert "张伟" in names
        assert "李娜" in names
        assert "王强" in names


def test_seed_run_pets_have_correct_names(seed_session):
    """Pets should have the expected names from PET_TEMPLATES."""
    seed.run()
    with _query(seed_session) as s:
        pets = s.scalars(select(Pet)).all()
        pet_names = {p.name for p in pets}
        expected = {"毛毛", "豆豆", "皮皮", "大金", "小金"}
        assert pet_names == expected


def test_seed_run_cost_amounts_positive(seed_session):
    """All cost amounts should be positive decimals."""
    seed.run()
    with _query(seed_session) as s:
        costs = s.scalars(select(CostRecord)).all()
        assert len(costs) > 0
        for cost in costs:
            assert float(cost.amount) > 0


def test_seed_run_fails_without_categories(db_session):
    """run() should raise RuntimeError if cost_categories is empty."""
    @contextmanager
    def _fake_session():
        session = db_session()
        try:
            yield session
        finally:
            session.close()

    # Remove categories
    _s = db_session()
    _s.execute(delete(CostCategory))
    _s.commit()
    _s.close()

    original = seed.SessionLocal
    seed.SessionLocal = _fake_session
    try:
        with pytest.raises(RuntimeError, match="cost_categories is empty"):
            seed.run()
    finally:
        seed.SessionLocal = original