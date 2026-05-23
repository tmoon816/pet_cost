from datetime import datetime
from decimal import Decimal
from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..core.config import settings
from ..core.exceptions import ConflictError
from ..models import CostRecord, Customer, Pet
from ..schemas.customer import CustomerCreate, CustomerUpdate


def classify_customer(visit_count: int) -> str:
    """P-006: 0 单=first_visit，1~VIP_THRESHOLD-1=returning，>=VIP_THRESHOLD=vip。"""
    if visit_count <= 0:
        return "first_visit"
    if visit_count >= settings.VIP_THRESHOLD:
        return "vip"
    return "returning"


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
    db: Session,
    q: str | None,
    page: int,
    page_size: int,
    sort_by: str | None = None,
    sort_dir: str = "desc",
) -> Tuple[List[dict], int]:
    """T-008: 列表项额外返回 has_cost（该客户名下任一宠物是否有过消费记录）。

    T-015: 额外返回 total_amount（名下所有宠物累计消费，无消费为 0）。支持
    sort_by=total_amount 按金额排序；sort_by=None 保持原默认 created_at DESC。

    返回 dict 列表代替 ORM 实例，使 schema CustomerListItem 能直接读到 has_cost。
    """
    has_cost_subq = (
        select(CostRecord.id)
        .join(Pet, CostRecord.pet_id == Pet.id)
        .where(Pet.customer_id == Customer.id)
        .exists()
    )
    # T-015：correlated scalar subquery 算累计消费（无消费 → 0）
    total_amount_subq = (
        select(func.coalesce(func.sum(CostRecord.amount), 0))
        .join(Pet, CostRecord.pet_id == Pet.id)
        .where(Pet.customer_id == Customer.id)
        .correlate(Customer)
        .scalar_subquery()
    )
    # P-006：消费记录数 → 客户分层
    visit_count_subq = (
        select(func.count(CostRecord.id))
        .join(Pet, CostRecord.pet_id == Pet.id)
        .where(Pet.customer_id == Customer.id)
        .correlate(Customer)
        .scalar_subquery()
    )

    stmt = select(
        Customer,
        has_cost_subq.label("has_cost"),
        total_amount_subq.label("total_amount"),
        visit_count_subq.label("visit_count"),
    )
    count_stmt = select(func.count(Customer.id))
    if q:
        like = f"%{q}%"
        cond = or_(Customer.name.like(like), Customer.phone.like(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

    if sort_by == "total_amount":
        order_col = total_amount_subq
        order_expr = order_col.asc() if sort_dir == "asc" else order_col.desc()
        # 金额相同时按 id 倒序保证顺序稳定
        stmt = stmt.order_by(order_expr, Customer.id.desc())
    else:
        # 默认：以 created_at 倒序（这里用 id DESC 作为 created_at 倒序的有效代理，与原逻辑一致）
        stmt = stmt.order_by(Customer.id.desc())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    rows = db.execute(stmt).all()
    items: List[dict] = []
    for row in rows:
        customer: Customer = row[0]
        visit_count = int(row[3] or 0)
        items.append(
            {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "note": customer.note,
                "created_at": customer.created_at,
                "updated_at": customer.updated_at,
                "has_cost": bool(row[1]),
                "total_amount": Decimal(row[2] or 0),
                "visit_count": visit_count,
                "customer_type": classify_customer(visit_count),
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
        "customer_type": classify_customer(int(cost_count or 0)),
    }


def list_recent(db: Session, limit: int = 5) -> List[Customer]:
    """T-014：返回最近产生过消费的客户，按名下最近一次消费时间（max(occurred_on)）倒序。

    无任何消费的客户不返回（INNER JOIN 筛掉）。
    同一客户下多条记录只计最近一次（GROUP BY customer_id）。
    """
    last_visit = func.max(CostRecord.occurred_on).label("last_visit")
    stmt = (
        select(Customer, last_visit)
        .join(Pet, Pet.customer_id == Customer.id)
        .join(CostRecord, CostRecord.pet_id == Pet.id)
        .group_by(Customer.id)
        .order_by(last_visit.desc(), Customer.id.desc())
        .limit(limit)
    )
    return [row[0] for row in db.execute(stmt).all()]
