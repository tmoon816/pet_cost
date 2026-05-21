from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Customer, Pet
from ..schemas.pet import PetCreate, PetUpdate


def get(db: Session, pet_id: int) -> Pet | None:
    return db.get(Pet, pet_id)


def list_paginated(
    db: Session, customer_id: int | None, page: int, page_size: int
) -> Tuple[List[Pet], int]:
    stmt = select(Pet)
    count_stmt = select(func.count(Pet.id))
    if customer_id is not None:
        stmt = stmt.where(Pet.customer_id == customer_id)
        count_stmt = count_stmt.where(Pet.customer_id == customer_id)
    stmt = stmt.order_by(Pet.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.scalars(stmt).all())
    total = int(db.scalar(count_stmt) or 0)
    return items, total


def _customer_exists(db: Session, customer_id: int) -> bool:
    return db.scalar(select(Customer.id).where(Customer.id == customer_id)) is not None


def create(db: Session, data: PetCreate) -> Pet | None:
    if not _customer_exists(db, data.customer_id):
        return None
    obj = Pet(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, pet_id: int, data: PetUpdate) -> Pet | None:
    obj = db.get(Pet, pet_id)
    if obj is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "customer_id" in payload and not _customer_exists(db, payload["customer_id"]):
        return None
    for field, value in payload.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def remove(db: Session, pet_id: int) -> bool:
    obj = db.get(Pet, pet_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
