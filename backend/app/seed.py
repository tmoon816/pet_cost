"""Seed development data.

Run with: ``uv run python -m app.seed``

Idempotent: each run wipes ``cost_records`` / ``pets`` / ``customers`` first,
then re-inserts a fresh batch. ``cost_categories`` is never touched (managed by
Alembic).
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, select

from .core.database import SessionLocal
from .models import CostCategory, CostRecord, Customer, Pet


CUSTOMER_PROFILES = [
    {"name": "张伟", "phone": "13800001001", "note": "会员积分 3200，常带毛毛来洗澡"},
    {"name": "李娜", "phone": "13900002002", "note": "VIP 会员，最近收养了一只流浪猫"},
    {"name": "王强", "phone": "13700003003", "note": "两只金毛，每月全套护理 + 定期寄养"},
]

PET_TEMPLATES = [
    [
        {"name": "毛毛", "species": "dog", "breed": "柯基", "gender": "male"},
    ],
    [
        {"name": "豆豆", "species": "cat", "breed": "中华田园猫", "gender": "female"},
        {"name": "皮皮", "species": "cat", "breed": "英短", "gender": "male"},
    ],
    [
        {"name": "大金", "species": "dog", "breed": "金毛", "gender": "male"},
        {"name": "小金", "species": "dog", "breed": "金毛", "gender": "female"},
    ],
]


def _random_amount() -> Decimal:
    cents = random.randint(1000, 50000)
    return Decimal(cents) / Decimal(100)


def _random_date_within(days_back: int = 180) -> date:
    today = date.today()
    delta = random.randint(0, days_back)
    return today - timedelta(days=delta)


def run() -> None:
    rng = random.Random(42)
    random.seed(42)

    with SessionLocal() as db:
        category_codes = list(db.scalars(select(CostCategory.code)).all())
        if not category_codes:
            raise RuntimeError(
                "cost_categories is empty — run `alembic upgrade head` first."
            )

        db.execute(delete(CostRecord))
        db.execute(delete(Pet))
        db.execute(delete(Customer))
        db.commit()

        customers: list[Customer] = []
        for profile in CUSTOMER_PROFILES:
            obj = Customer(**profile)
            db.add(obj)
            customers.append(obj)
        db.flush()

        pets: list[Pet] = []
        for customer, pet_specs in zip(customers, PET_TEMPLATES):
            for spec in pet_specs:
                pet = Pet(customer_id=customer.id, **spec, birthday=_random_date_within(1500))
                db.add(pet)
                pets.append(pet)
        db.flush()

        cost_records: list[CostRecord] = []
        for pet in pets:
            count = rng.randint(8, 15)
            for _ in range(count):
                cost_records.append(
                    CostRecord(
                        pet_id=pet.id,
                        category_code=rng.choice(category_codes),
                        amount=_random_amount(),
                        occurred_on=_random_date_within(180),
                        note=None,
                    )
                )
        db.add_all(cost_records)
        db.commit()

        print(
            f"Seeded: {len(customers)} customers, {len(pets)} pets, "
            f"{len(cost_records)} cost records"
        )


if __name__ == "__main__":
    run()
