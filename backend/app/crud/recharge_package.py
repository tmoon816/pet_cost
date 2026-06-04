"""充值套餐 CRUD + 按套餐充值（checkout）。

checkout 复用 balance.recharge：到账 = price + bonus，赠品与套餐名写入流水备注。
"""
from __future__ import annotations

from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Customer, RechargePackage
from ..schemas.recharge_package import RechargePackageCreate, RechargePackageUpdate
from . import balance as crud_balance


def get(db: Session, package_id: int) -> RechargePackage | None:
    return db.get(RechargePackage, package_id)


def list_all(db: Session, *, active_only: bool = False) -> List[RechargePackage]:
    stmt = select(RechargePackage)
    if active_only:
        stmt = stmt.where(RechargePackage.is_active.is_(True))
    stmt = stmt.order_by(RechargePackage.sort_order, RechargePackage.id)
    return list(db.scalars(stmt).all())


def create(db: Session, data: RechargePackageCreate) -> RechargePackage:
    obj = RechargePackage(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, package_id: int, data: RechargePackageUpdate) -> RechargePackage | None:
    obj = db.get(RechargePackage, package_id)
    if obj is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def remove(db: Session, package_id: int) -> bool:
    obj = db.get(RechargePackage, package_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


def checkout(
    db: Session,
    package: RechargePackage,
    customer: Customer,
    *,
    channel: str,
    note: str | None,
) -> Tuple[Customer, "object"]:
    """给客户按套餐充值。返回 (customer, transaction)。"""
    gifts = list(package.gifts or [])
    parts = [f"套餐充值「{package.name}」"]
    if gifts:
        parts.append("赠品：" + "、".join(gifts))
    if note:
        parts.append(note)
    full_note = "；".join(parts)

    txn = crud_balance.recharge(
        db,
        customer,
        amount=package.price,
        bonus_amount=package.bonus_amount,
        channel=channel,
        note=full_note,
    )
    return customer, txn
