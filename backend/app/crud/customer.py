from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..core.exceptions import ConflictError
from ..models import Customer
from ..schemas.customer import CustomerCreate, CustomerUpdate


def _check_phone_conflict(db: Session, phone: str | None, exclude_id: int | None = None) -> None:
    if not phone:
        return
    stmt = select(Customer.id).where(Customer.phone == phone)
    if exclude_id is not None:
        stmt = stmt.where(Customer.id != exclude_id)
    existing = db.scalar(stmt.limit(1))
    if existing is not None:
        raise ConflictError({"detail": "phone_exists", "existing_id": int(existing)})


def get(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def get_with_pets(db: Session, customer_id: int) -> Customer | None:
    stmt = (
        select(Customer)
        .options(selectinload(Customer.pets))
        .where(Customer.id == customer_id)
    )
    return db.scalar(stmt)


def list_paginated(
    db: Session, q: str | None, page: int, page_size: int
) -> Tuple[List[Customer], int]:
    stmt = select(Customer)
    count_stmt = select(func.count(Customer.id))
    if q:
        like = f"%{q}%"
        cond = or_(Customer.name.like(like), Customer.phone.like(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    stmt = stmt.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.scalars(stmt).all())
    total = int(db.scalar(count_stmt) or 0)
    return items, total


def create(db: Session, data: CustomerCreate) -> Customer:
    _check_phone_conflict(db, data.phone)
    obj = Customer(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, customer_id: int, data: CustomerUpdate) -> Customer | None:
    obj = db.get(Customer, customer_id)
    if obj is None:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "phone" in payload:
        _check_phone_conflict(db, payload["phone"], exclude_id=customer_id)
    for field, value in payload.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def remove(db: Session, customer_id: int) -> bool:
    obj = db.get(Customer, customer_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
