from datetime import date
from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import CostCategory, CostRecord, Pet
from ..schemas.cost import CostCreate, CostUpdate


def get(db: Session, cost_id: int) -> CostRecord | None:
    return db.get(CostRecord, cost_id)


def _pet_exists(db: Session, pet_id: int) -> bool:
    return db.scalar(select(Pet.id).where(Pet.id == pet_id)) is not None


def _category_exists(db: Session, code: str) -> bool:
    return db.scalar(select(CostCategory.code).where(CostCategory.code == code)) is not None


def list_paginated(
    db: Session,
    *,
    pet_id: int | None,
    customer_id: int | None,
    category_code: str | None,
    start: date | None,
    end: date | None,
    page: int,
    page_size: int,
) -> Tuple[List[CostRecord], int]:
    stmt = select(CostRecord)
    count_stmt = select(func.count(CostRecord.id))
    join_pet = customer_id is not None
    if join_pet:
        stmt = stmt.join(Pet, Pet.id == CostRecord.pet_id)
        count_stmt = count_stmt.join(Pet, Pet.id == CostRecord.pet_id)
        stmt = stmt.where(Pet.customer_id == customer_id)
        count_stmt = count_stmt.where(Pet.customer_id == customer_id)
    if pet_id is not None:
        stmt = stmt.where(CostRecord.pet_id == pet_id)
        count_stmt = count_stmt.where(CostRecord.pet_id == pet_id)
    if category_code:
        stmt = stmt.where(CostRecord.category_code == category_code)
        count_stmt = count_stmt.where(CostRecord.category_code == category_code)
    if start is not None:
        stmt = stmt.where(CostRecord.occurred_on >= start)
        count_stmt = count_stmt.where(CostRecord.occurred_on >= start)
    if end is not None:
        stmt = stmt.where(CostRecord.occurred_on <= end)
        count_stmt = count_stmt.where(CostRecord.occurred_on <= end)
    stmt = (
        stmt.order_by(CostRecord.occurred_on.desc(), CostRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(stmt).all())
    total = int(db.scalar(count_stmt) or 0)
    return items, total


def create(db: Session, data: CostCreate) -> CostRecord | None:
    if not _pet_exists(db, data.pet_id):
        return None
    if not _category_exists(db, data.category_code):
        return None
    obj = CostRecord(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, cost_id: int, data: CostUpdate) -> CostRecord | None:
    obj = db.get(CostRecord, cost_id)
    if obj is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "pet_id" in payload and not _pet_exists(db, payload["pet_id"]):
        return None
    if "category_code" in payload and not _category_exists(db, payload["category_code"]):
        return None
    for field, value in payload.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def remove(db: Session, cost_id: int) -> bool:
    obj = db.get(CostRecord, cost_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
