from datetime import date, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from ..models import CostCategory, CostRecord, Customer, Pet


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


def customer_acquisition(db: Session, year: int, month: int) -> dict:
    """T-009: 给定年月，返回当月新客 vs 回头客数。

    口径:
      当月有消费(occurred_on 落在 [start, end_of_month]) 的去重客户里：
        - 该客户全量消费历史的最早 occurred_on 在 [start, end_of_month] => 新客
        - 否则 => 回头客
    """
    from calendar import monthrange

    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])

    # 客户在当月有消费
    customers_with_cost_this_month = (
        select(Pet.customer_id)
        .join(CostRecord, CostRecord.pet_id == Pet.id)
        .where(CostRecord.occurred_on >= start)
        .where(CostRecord.occurred_on <= end)
        .distinct()
        .subquery()
    )

    # 每个客户的最早消费日期（全量历史）
    first_cost_per_customer = (
        select(
            Pet.customer_id.label("customer_id"),
            func.min(CostRecord.occurred_on).label("first_date"),
        )
        .join(CostRecord, CostRecord.pet_id == Pet.id)
        .group_by(Pet.customer_id)
        .subquery()
    )

    rows = db.execute(
        select(
            first_cost_per_customer.c.customer_id,
            first_cost_per_customer.c.first_date,
        ).join(
            customers_with_cost_this_month,
            customers_with_cost_this_month.c.customer_id
            == first_cost_per_customer.c.customer_id,
        )
    ).all()

    new_customers = sum(1 for r in rows if start <= r.first_date <= end)
    total = len(rows)
    returning_customers = total - new_customers

    return {
        "year": year,
        "month": month,
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "total": total,
    }


def dormant_customers(db: Session, days: int, limit: int, today: date | None = None) -> List[dict]:
    """T-010: 返回 last_visit_at 距今 ≥ days 天的老客预警列表。

    口径:
      - last_visit_at = 该客户名下所有宠物的最近一次 CostRecord.occurred_on
      - 仅考虑历史上至少有一次消费的客户（“老客”）
      - 今天 - last_visit_at ≥ days 天才入列
      - 按 last_visit_at 升序（最久没来的排前），limit 裁切
    """
    today = today or date.today()
    threshold = today - timedelta(days=days)

    last_visit_per_customer = (
        select(
            Pet.customer_id.label("customer_id"),
            func.max(CostRecord.occurred_on).label("last_visit_at"),
        )
        .join(CostRecord, CostRecord.pet_id == Pet.id)
        .group_by(Pet.customer_id)
        .subquery()
    )

    stmt = (
        select(
            Customer.id.label("customer_id"),
            Customer.name.label("customer_name"),
            last_visit_per_customer.c.last_visit_at,
        )
        .join(
            last_visit_per_customer,
            last_visit_per_customer.c.customer_id == Customer.id,
        )
        .where(last_visit_per_customer.c.last_visit_at <= threshold)
        .order_by(last_visit_per_customer.c.last_visit_at.asc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()
    return [
        {
            "customer_id": int(row.customer_id),
            "customer_name": row.customer_name,
            "last_visit_at": row.last_visit_at,
            "days_since": (today - row.last_visit_at).days,
        }
        for row in rows
    ]
