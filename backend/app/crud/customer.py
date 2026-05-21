from datetime import datetime
from decimal import Decimal
from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..core.exceptions import ConflictError
from ..models import CostRecord, Customer, Pet
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
) -> Tuple[List[dict], int]:
    """T-008: 列表项额外返回 has_cost（该客户名下任一宠物是否有过消费记录）。

    返回 dict 列表代替 ORM 实例，使 schema CustomerListItem 能直接读到 has_cost。
    """
    has_cost_subq = (
        select(CostRecord.id)
        .join(Pet, CostRecord.pet_id == Pet.id)
        .where(Pet.customer_id == Customer.id)
        .exists()
    )

    stmt = select(Customer, has_cost_subq.label("has_cost"))
    count_stmt = select(func.count(Customer.id))
    if q:
        like = f"%{q}%"
        cond = or_(Customer.name.like(like), Customer.phone.like(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    stmt = stmt.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size)

    rows = db.execute(stmt).all()
    items: List[dict] = []
    for row in rows:
        customer: Customer = row[0]
        items.append(
            {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "note": customer.note,
                "created_at": customer.created_at,
                "updated_at": customer.updated_at,
                "has_cost": bool(row[1]),
            }
        )
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


def get_summary(db: Session, customer_id: int) -> dict | None:
    """T-007：返回客户聚合指标。customer 不存在 → None。

    无消费记录 → total_amount=0、cost_count=0、last_visit_at=None。
    last_visit_at 取 max(cost_records.occurred_on)，转为当日 00:00 的 datetime。
    """
    customer = db.get(Customer, customer_id)
    if customer is None:
        return None

    stmt = (
        select(
            func.coalesce(func.sum(CostRecord.amount), 0).label("total_amount"),
            func.max(CostRecord.occurred_on).label("last_visit_date"),
            func.count(CostRecord.id).label("cost_count"),
        )
        .join(Pet, CostRecord.pet_id == Pet.id)
        .where(Pet.customer_id == customer_id)
    )
    total_amount, last_visit_date, cost_count = db.execute(stmt).one()

    last_visit_at: datetime | None = None
    if last_visit_date is not None:
        last_visit_at = datetime.combine(last_visit_date, datetime.min.time())

    return {
        "customer_id": customer_id,
        "total_amount": Decimal(total_amount or 0),
        "last_visit_at": last_visit_at,
        "cost_count": int(cost_count or 0),
    }
