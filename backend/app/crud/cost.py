from datetime import date
from typing import List, Tuple
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import CostCategory, CostRecord, Pet
from ..schemas.cost import CostBatchCreate, CostCreate, CostUpdate


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
    # 始终联表 Pet 以便返回 pet_name（宠物店前端账单列表必须展示宠物名）。
    # 用元组查询：避免对 ORM 对象做 join 时产生重复行；CostRecord -> Pet 是多对一，安全。
    stmt = select(CostRecord, Pet.name).join(Pet, Pet.id == CostRecord.pet_id)
    count_stmt = select(func.count(CostRecord.id)).join(Pet, Pet.id == CostRecord.pet_id)
    if customer_id is not None:
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
    rows = db.execute(stmt).all()
    items: List[CostRecord] = []
    for row in rows:
        record: CostRecord = row[0]
        # 短生命周期对象，setattr 是安全的（不会被 session 再次刷新覆盖）
        record.pet_name = row[1]
        items.append(record)
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


def create_batch(db: Session, data: CostBatchCreate) -> List[CostRecord]:
    """T-029: 多只宠物同金额同分类批量开单。
    引用合法性已由路由层 _validate_refs 校验过；这里只做事务内 N 条 insert。
    任一插入失败 SQLAlchemy 自动回滚（commit 抛错时整批不会落库）。
    """
    objs: List[CostRecord] = []
    for pid in data.pet_ids:
        obj = CostRecord(
            pet_id=pid,
            category_code=data.category_code,
            amount=data.amount,
            occurred_on=data.occurred_on,
            note=data.note,
        )
        db.add(obj)
        objs.append(obj)
    db.commit()
    for obj in objs:
        db.refresh(obj)
    return objs


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

def get_total_by_date_range(db: Session, start_date: str, end_date: str) -> Decimal:
    """查询指定时间范围内的总花费"""
    total = db.scalar(
        select(func.sum(CostRecord.amount))
        .where(CostRecord.occurred_on >= start_date)
        .where(CostRecord.occurred_on < end_date)
    )
    return total or Decimal(0)

def get_total_by_pet_and_date_range(db: Session, pet_id: int, start_date: str, end_date: str) -> Decimal:
    """查询指定宠物指定时间范围内的总花费"""
    total = db.scalar(
        select(func.sum(CostRecord.amount))
        .where(CostRecord.pet_id == pet_id)
        .where(CostRecord.occurred_on >= start_date)
        .where(CostRecord.occurred_on < end_date)
    )
    return total or Decimal(0)

def get_total_by_category_and_date_range(db: Session, category_code: str, start_date: str, end_date: str) -> Decimal:
    """查询指定分类指定时间范围内的总花费"""
    total = db.scalar(
        select(func.sum(CostRecord.amount))
        .where(CostRecord.category_code == category_code)
        .where(CostRecord.occurred_on >= start_date)
        .where(CostRecord.occurred_on < end_date)
    )
    return total or Decimal(0)
