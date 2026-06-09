"""储值余额与流水。

设计要点（涉及钱，务必看）：
- ``recharge`` / ``adjust`` 自身 commit（独立操作）。
- ``deduct_for_cost`` / ``refund_for_cost`` **不 commit**，只在传入的 session 内改余额 + 加流水，
  由调用方（cost 的开单/删单/改单流程）统一 commit，保证「扣款与建单」原子。
- 余额快照 ``balance_after`` 每笔都写，可对账。
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.exceptions import InsufficientBalanceError
from ..models import BalanceTransaction, Customer, Pet


def _q(value) -> Decimal:
    """统一量化到 2 位小数。"""
    return Decimal(value).quantize(Decimal("0.01"))


def get_customer_for_pet(db: Session, pet_id: int) -> Customer | None:
    """订单挂在 pet 上，扣款要反查 pet 所属客户。"""
    customer_id = db.scalar(select(Pet.customer_id).where(Pet.id == pet_id))
    if customer_id is None:
        return None
    return db.get(Customer, customer_id)


def recharge(
    db: Session,
    customer: Customer,
    *,
    amount: Decimal,
    bonus_amount: Decimal,
    channel: str,
    note: str | None,
) -> BalanceTransaction:
    """虚拟充值：余额 += 本金 + 赠送，记一条 recharge 流水。自身 commit。"""
    credit = _q(amount) + _q(bonus_amount)
    customer.balance = _q(customer.balance) + credit
    txn = BalanceTransaction(
        customer_id=customer.id,
        type="recharge",
        amount=credit,
        bonus_amount=_q(bonus_amount),
        balance_after=customer.balance,
        channel=channel,
        note=note,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def adjust(db: Session, customer: Customer, *, amount: Decimal, note: str | None) -> BalanceTransaction:
    """手动调整余额（带符号）。不允许调成负数。自身 commit。"""
    delta = _q(amount)
    new_balance = _q(customer.balance) + delta
    if new_balance < 0:
        raise InsufficientBalanceError(customer.balance, -delta)
    customer.balance = new_balance
    txn = BalanceTransaction(
        customer_id=customer.id,
        type="adjust",
        amount=delta,
        bonus_amount=Decimal("0.00"),
        balance_after=customer.balance,
        note=note,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def deduct_for_cost(
    db: Session,
    customer: Customer,
    *,
    amount: Decimal,
    cost_id: int,
    discount_amount: Decimal | int = 0,
) -> None:
    """订单扣储值。amount=实扣（折后）金额；discount_amount=折扣省下的钱（仅记账）。
    余额不足抛 InsufficientBalanceError。**不 commit**。"""
    need = _q(amount)
    if _q(customer.balance) < need:
        raise InsufficientBalanceError(customer.balance, need)
    customer.balance = _q(customer.balance) - need
    disc = _q(discount_amount)
    note = "订单消费"
    if disc > 0:
        note = f"订单消费（会员折扣省 ¥{disc}）"
    db.add(
        BalanceTransaction(
            customer_id=customer.id,
            type="consume",
            amount=-need,
            bonus_amount=Decimal("0.00"),
            discount_amount=disc,
            balance_after=customer.balance,
            cost_id=cost_id,
            note=note,
        )
    )


def deduct_for_boarding(
    db: Session,
    customer: Customer,
    *,
    amount: Decimal,
    cost_id: int,
    note: str,
) -> BalanceTransaction:
    """寄养按天扣费：强制扣减，**允许余额变负**（欠费）。**不 commit**。

    与 deduct_for_cost 的区别：不做余额充足校验，余额可为负。
    由结算流程在单张寄养单的事务内调用，与建单、推进游标同提交。
    """
    need = _q(amount)
    customer.balance = _q(customer.balance) - need
    txn = BalanceTransaction(
        customer_id=customer.id,
        type="consume",
        amount=-need,
        bonus_amount=Decimal("0.00"),
        balance_after=customer.balance,
        cost_id=cost_id,
        note=note,
    )
    db.add(txn)
    return txn


def refund_for_cost(db: Session, customer: Customer, *, amount: Decimal, cost_id: int) -> None:
    """订单（曾扣储值）被删/改时退回余额，记 refund 流水。**不 commit**。"""
    back = _q(amount)
    customer.balance = _q(customer.balance) + back
    db.add(
        BalanceTransaction(
            customer_id=customer.id,
            type="refund",
            amount=back,
            bonus_amount=Decimal("0.00"),
            balance_after=customer.balance,
            cost_id=cost_id,
            note="订单退款",
        )
    )


def list_transactions(
    db: Session, customer_id: int, *, page: int, page_size: int
) -> Tuple[List[BalanceTransaction], int]:
    from sqlalchemy import func

    stmt = (
        select(BalanceTransaction)
        .where(BalanceTransaction.customer_id == customer_id)
        .order_by(BalanceTransaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(stmt).all())
    total = int(
        db.scalar(
            select(func.count(BalanceTransaction.id)).where(
                BalanceTransaction.customer_id == customer_id
            )
        )
        or 0
    )
    return items, total
