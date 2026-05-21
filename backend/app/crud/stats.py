from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from ..models import CostCategory, CostRecord, Pet


def _apply_window(stmt, start: date | None, end: date | None):
    if start is not None:
        stmt = stmt.where(CostRecord.occurred_on >= start)
    if end is not None:
        stmt = stmt.where(CostRecord.occurred_on <= end)
    return stmt


def summary(db: Session, start: date | None, end: date | None) -> dict:
    base = select(
        func.coalesce(func.sum(CostRecord.amount), 0),
        func.count(CostRecord.id),
        func.count(distinct(CostRecord.pet_id)),
    )
    base = _apply_window(base, start, end)
    total_amount, record_count, pet_count = db.execute(base).one()

    customer_stmt = select(func.count(distinct(Pet.customer_id))).join(
        CostRecord, CostRecord.pet_id == Pet.id
    )
    customer_stmt = _apply_window(customer_stmt, start, end)
    customer_count = int(db.scalar(customer_stmt) or 0)

    return {
        "total_amount": Decimal(total_amount or 0),
        "record_count": int(record_count or 0),
        "customer_count": customer_count,
        "pet_count": int(pet_count or 0),
    }


def by_category(db: Session, start: date | None, end: date | None) -> List[dict]:
    label_expr = func.coalesce(CostCategory.label, CostRecord.category_code).label("label")
    stmt = (
        select(
            CostRecord.category_code.label("category"),
            label_expr,
            func.coalesce(func.sum(CostRecord.amount), 0).label("total"),
            func.count(CostRecord.id).label("count"),
        )
        .outerjoin(CostCategory, CostCategory.code == CostRecord.category_code)
        .group_by(CostRecord.category_code, CostCategory.label)
        .order_by(func.sum(CostRecord.amount).desc())
    )
    stmt = _apply_window(stmt, start, end)
    rows = db.execute(stmt).all()
    return [
        {
            "category": row.category,
            "label": row.label,
            "total": Decimal(row.total or 0),
            "count": int(row.count),
        }
        for row in rows
    ]


def by_month(db: Session, start: date | None, end: date | None) -> List[dict]:
    dialect = db.bind.dialect.name if db.bind is not None else ""
    if dialect == "mysql":
        month_expr = func.date_format(CostRecord.occurred_on, "%Y-%m")
    else:
        month_expr = func.strftime("%Y-%m", CostRecord.occurred_on)
    month_label = month_expr.label("month")
    stmt = (
        select(month_label, func.coalesce(func.sum(CostRecord.amount), 0).label("total"))
        .group_by(month_label)
        .order_by(month_label)
    )
    stmt = _apply_window(stmt, start, end)
    rows = db.execute(stmt).all()
    return [{"month": row.month, "total": Decimal(row.total or 0)} for row in rows]


def by_pet(
    db: Session,
    customer_id: int | None,
    limit: int,
    start: date | None,
    end: date | None,
) -> List[dict]:
    stmt = (
        select(
            Pet.id.label("pet_id"),
            Pet.name.label("pet_name"),
            func.coalesce(func.sum(CostRecord.amount), 0).label("total"),
        )
        .join(CostRecord, CostRecord.pet_id == Pet.id)
        .group_by(Pet.id, Pet.name)
        .order_by(func.sum(CostRecord.amount).desc())
        .limit(limit)
    )
    if customer_id is not None:
        stmt = stmt.where(Pet.customer_id == customer_id)
    stmt = _apply_window(stmt, start, end)
    rows = db.execute(stmt).all()
    return [
        {"pet_id": int(row.pet_id), "pet_name": row.pet_name, "total": Decimal(row.total or 0)}
        for row in rows
    ]
