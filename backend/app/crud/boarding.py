"""寄养单 CRUD + 按天自动结算引擎。

数据准确性是本模块第一要务，三道防线：
  1. 游标 settled_through：只结算 (settled_through, target_day] 区间，幂等。
  2. 唯一约束 uk_costs_boarding_day：DB 层禁止同一单同一天重复扣费。
  3. 结算前 SELECT 已存在的扣费日集合，跳过已扣天（断点续扣 / 自愈）。

每张寄养单的"补扣多天 + 扣余额 + 推进游标 + 累计快照"在**单个事务**内完成，
失败整体回滚、游标不动，下次结算自动重试，绝不丢数据、不重复扣。
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import BoardingOrder, CostRecord, Customer
from . import balance as balance_crud

BOARDING_CATEGORY = "boarding"


def _q(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def get(db: Session, boarding_id: int) -> BoardingOrder | None:
    return db.get(BoardingOrder, boarding_id)


def list_all(
    db: Session, *, status: str | None = None, customer_id: int | None = None
) -> List[BoardingOrder]:
    stmt = select(BoardingOrder)
    if status:
        stmt = stmt.where(BoardingOrder.status == status)
    if customer_id is not None:
        stmt = stmt.where(BoardingOrder.customer_id == customer_id)
    stmt = stmt.order_by(BoardingOrder.status.asc(), BoardingOrder.check_in_date.desc(), BoardingOrder.id.desc())
    return list(db.scalars(stmt).all())


def create(
    db: Session,
    *,
    pet_id: int,
    customer_id: int,
    check_in_date: date,
    expected_days: int,
    daily_rate: Decimal,
    note: str | None,
    settle_today: bool = True,
    today: date | None = None,
) -> BoardingOrder:
    """开寄养单。默认立即结算到今天（把入住日起到今天的天数补扣上）。"""
    obj = BoardingOrder(
        pet_id=pet_id,
        customer_id=customer_id,
        check_in_date=check_in_date,
        expected_days=expected_days,
        daily_rate=_q(daily_rate),
        status="active",
        settled_through=None,
        total_charged=Decimal("0.00"),
        note=note,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    if settle_today:
        settle_one(db, obj, today=today or date.today())
        db.refresh(obj)
    return obj


def _charge_day(db: Session, order: BoardingOrder, customer: Customer, day: date) -> bool:
    """给某一天扣一笔寄养费。已存在则跳过（返回 False），新扣返回 True。

    不 commit；由 settle_one 统一提交。
    """
    exists = db.scalar(
        select(CostRecord.id).where(
            CostRecord.boarding_order_id == order.id,
            CostRecord.occurred_on == day,
        )
    )
    if exists is not None:
        return False  # 该天已扣过，跳过（幂等自愈）

    amount = _q(order.daily_rate)
    cost = CostRecord(
        pet_id=order.pet_id,
        category_code=BOARDING_CATEGORY,
        amount=amount,
        discount_amount=Decimal("0.00"),
        pay_method="balance",
        boarding_order_id=order.id,
        occurred_on=day,
        note=f"寄养日扣费 {day.isoformat()}",
    )
    db.add(cost)
    db.flush()  # 拿 cost.id 供流水引用
    balance_crud.deduct_for_boarding(
        db, customer, amount=amount, cost_id=cost.id,
        note=f"寄养扣费（{day.isoformat()}）",
    )
    order.total_charged = _q(order.total_charged) + amount
    return True


def settle_one(db: Session, order: BoardingOrder, *, today: date | None = None) -> int:
    """结算单张寄养单到 target 日（含）。返回本次新扣的天数。

    target = closed 单的 check_out_date 前一天（退房当天不计费），否则今天。
    单事务：任一步失败整体回滚、游标不动，下次重试。
    """
    today = today or date.today()
    if order.status == "closed":
        # 退房当天不计费：结算到退房日的前一天
        if order.check_out_date is None:
            return 0
        target = order.check_out_date - timedelta(days=1)
    else:
        target = today

    # 计费起点：游标的下一天；游标为空则从入住日开始
    start = order.check_in_date if order.settled_through is None else order.settled_through + timedelta(days=1)
    if start > target:
        return 0  # 无可结算区间

    customer = db.get(Customer, order.customer_id)
    if customer is None:
        return 0

    charged = 0
    try:
        day = start
        while day <= target:
            if _charge_day(db, order, customer, day):
                charged += 1
            day += timedelta(days=1)
        order.settled_through = target
        db.commit()
    except Exception:
        db.rollback()
        raise
    return charged


def settle_all_active(db: Session, *, today: date | None = None) -> dict:
    """结算所有在住寄养单到今天。每单独立事务，一单失败不影响其他单。

    返回 {orders_processed, days_charged, errors}。
    """
    today = today or date.today()
    order_ids = list(
        db.scalars(select(BoardingOrder.id).where(BoardingOrder.status == "active")).all()
    )
    days_total = 0
    processed = 0
    errors: List[int] = []
    for oid in order_ids:
        order = db.get(BoardingOrder, oid)
        if order is None:
            continue
        try:
            days_total += settle_one(db, order, today=today)
            processed += 1
        except Exception:
            errors.append(oid)
    return {"orders_processed": processed, "days_charged": days_total, "errors": errors}


def close(db: Session, order: BoardingOrder, *, check_out_date: date) -> BoardingOrder:
    """退房结算封口。先把住到退房前一天的费用补扣齐，再置为 closed。"""
    # 先按 active 结算到退房前一天
    settle_target = check_out_date - timedelta(days=1)
    if order.settled_through is None or order.settled_through < settle_target:
        # 临时用 active 逻辑结算到退房前一天
        order.check_out_date = None
        settle_one(db, order, today=settle_target)
        db.refresh(order)
    order.status = "closed"
    order.check_out_date = check_out_date
    db.commit()
    db.refresh(order)
    return order


def remove(db: Session, order: BoardingOrder) -> bool:
    """删除寄养单。关联的寄养扣费订单经由外键级联删除，对应余额不在此自动退。

    说明：删除会连带删掉按天扣费的 cost_records（ON DELETE CASCADE），
    但**不会自动退余额**——删除寄养单属于管理操作，若需退费请走订单退款或手动调整，
    避免静默改动客户余额造成对账困难。
    """
    db.delete(order)
    db.commit()
    return True


def reconcile(db: Session, order: BoardingOrder) -> Tuple[Decimal, Decimal]:
    """对账：返回 (快照累计, 实际寄养扣费之和)。两者应相等。"""
    from sqlalchemy import func

    actual = db.scalar(
        select(func.coalesce(func.sum(CostRecord.amount), 0)).where(
            CostRecord.boarding_order_id == order.id
        )
    )
    return _q(order.total_charged), _q(actual or 0)
