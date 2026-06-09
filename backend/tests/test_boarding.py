"""寄养按天扣费 —— 数据准确性是测试重点。

覆盖：单日扣费、幂等（重复结算不重扣）、跨多天补扣、余额扣成负数、
超期判定、退房封口、对账一致、唯一约束兜底。
"""
from datetime import date
from decimal import Decimal

import pytest

from app.crud import boarding as crud_boarding
from app.models import BoardingOrder, CostRecord, Customer, Pet


@pytest.fixture
def setup_pet(db_session):
    """建一个客户 + 宠物 + 初始余额，返回 (SessionLocal, customer_id, pet_id)。"""
    Session = db_session
    db = Session()
    try:
        c = Customer(name="寄养客户", balance=Decimal("300.00"))
        db.add(c)
        db.flush()
        p = Pet(name="球球", customer_id=c.id)
        db.add(p)
        db.commit()
        return Session, c.id, p.id
    finally:
        db.close()


def _make_order(db, pet_id, customer_id, check_in, days, rate):
    return crud_boarding.create(
        db,
        pet_id=pet_id,
        customer_id=customer_id,
        check_in_date=check_in,
        expected_days=days,
        daily_rate=Decimal(rate),
        note=None,
        settle_today=False,
    )


def test_single_day_charge(setup_pet):
    Session, cid, pid = setup_pet
    db = Session()
    try:
        order = _make_order(db, pid, cid, date(2026, 6, 1), 10, "50.00")
        # 结算到入住当天：扣 1 天
        charged = crud_boarding.settle_one(db, order, today=date(2026, 6, 1))
        assert charged == 1

        db.refresh(order)
        assert order.settled_through == date(2026, 6, 1)
        assert order.total_charged == Decimal("50.00")

        customer = db.get(Customer, cid)
        assert customer.balance == Decimal("250.00")  # 300 - 50

        costs = db.query(CostRecord).filter(CostRecord.boarding_order_id == order.id).all()
        assert len(costs) == 1
        assert costs[0].amount == Decimal("50.00")
        assert costs[0].pay_method == "balance"
        assert costs[0].category_code == "boarding"
    finally:
        db.close()


def test_idempotent_resettle_same_day(setup_pet):
    """同一天重复结算不重复扣费 —— 核心数据准确性保证。"""
    Session, cid, pid = setup_pet
    db = Session()
    try:
        order = _make_order(db, pid, cid, date(2026, 6, 1), 10, "50.00")
        crud_boarding.settle_one(db, order, today=date(2026, 6, 3))  # 扣 3 天 = 150
        crud_boarding.settle_one(db, order, today=date(2026, 6, 3))  # 再跑，应 0 新扣
        crud_boarding.settle_one(db, order, today=date(2026, 6, 3))

        db.refresh(order)
        customer = db.get(Customer, cid)
        costs = db.query(CostRecord).filter(CostRecord.boarding_order_id == order.id).all()
        assert len(costs) == 3                      # 仍是 3 条，没重复
        assert order.total_charged == Decimal("150.00")
        assert customer.balance == Decimal("150.00")  # 300 - 150
    finally:
        db.close()


def test_multi_day_catch_up(setup_pet):
    """关机几天后开机：一次性补扣欠下的天数。"""
    Session, cid, pid = setup_pet
    db = Session()
    try:
        order = _make_order(db, pid, cid, date(2026, 6, 1), 10, "30.00")
        crud_boarding.settle_one(db, order, today=date(2026, 6, 1))  # 第1天
        # 跳到 6/5 才再结算，应补扣 6/2~6/5 共 4 天
        charged = crud_boarding.settle_one(db, order, today=date(2026, 6, 5))
        assert charged == 4

        db.refresh(order)
        assert order.settled_through == date(2026, 6, 5)
        assert order.total_charged == Decimal("150.00")  # 5 天 * 30
        days = sorted(
            c.occurred_on for c in
            db.query(CostRecord).filter(CostRecord.boarding_order_id == order.id).all()
        )
        assert days == [date(2026, 6, d) for d in range(1, 6)]
    finally:
        db.close()


def test_balance_goes_negative(setup_pet):
    """余额不足继续扣，允许变负（欠费）。"""
    Session, cid, pid = setup_pet
    db = Session()
    try:
        # 余额 300，每天 100，住 5 天 => 应扣 500，余额 -200
        order = _make_order(db, pid, cid, date(2026, 6, 1), 5, "100.00")
        crud_boarding.settle_one(db, order, today=date(2026, 6, 5))

        db.refresh(order)
        customer = db.get(Customer, cid)
        assert order.total_charged == Decimal("500.00")
        assert customer.balance == Decimal("-200.00")
    finally:
        db.close()


def test_overdue_continues_charging(setup_pet):
    """超过约定天数仍继续扣费。"""
    Session, cid, pid = setup_pet
    db = Session()
    try:
        # 约定 3 天，但结算到第 6 天 => 扣 6 天
        order = _make_order(db, pid, cid, date(2026, 6, 1), 3, "20.00")
        crud_boarding.settle_one(db, order, today=date(2026, 6, 6))
        db.refresh(order)
        assert order.total_charged == Decimal("120.00")  # 6 天 * 20
    finally:
        db.close()


def test_close_charges_until_day_before_checkout(setup_pet):
    """退房：住到退房日前一天计费，退房当天不计费。"""
    Session, cid, pid = setup_pet
    db = Session()
    try:
        order = _make_order(db, pid, cid, date(2026, 6, 1), 10, "40.00")
        crud_boarding.settle_one(db, order, today=date(2026, 6, 2))  # 先扣 6/1, 6/2
        # 6/4 退房 => 应再补 6/3，不扣 6/4
        crud_boarding.close(db, order, check_out_date=date(2026, 6, 4))

        db.refresh(order)
        assert order.status == "closed"
        days = sorted(
            c.occurred_on for c in
            db.query(CostRecord).filter(CostRecord.boarding_order_id == order.id).all()
        )
        assert days == [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]
        assert order.total_charged == Decimal("120.00")  # 3 天 * 40

        # 退房后再结算不应有任何新扣费
        crud_boarding.settle_one(db, order, today=date(2026, 6, 10))
        db.refresh(order)
        assert order.total_charged == Decimal("120.00")
    finally:
        db.close()


def test_reconcile_snapshot_matches_actual(setup_pet):
    """对账：累计快照 == 实际扣费之和。"""
    Session, cid, pid = setup_pet
    db = Session()
    try:
        order = _make_order(db, pid, cid, date(2026, 6, 1), 10, "33.33")
        crud_boarding.settle_one(db, order, today=date(2026, 6, 4))
        snapshot, actual = crud_boarding.reconcile(db, order)
        assert snapshot == actual
        assert actual == Decimal("133.32")  # 4 * 33.33
    finally:
        db.close()


def test_settle_all_active(setup_pet):
    """批量结算所有在住单。"""
    Session, cid, pid = setup_pet
    db = Session()
    try:
        _make_order(db, pid, cid, date(2026, 6, 1), 10, "50.00")
        result = crud_boarding.settle_all_active(db, today=date(2026, 6, 2))
        assert result["orders_processed"] == 1
        assert result["days_charged"] == 2
        assert result["errors"] == []
    finally:
        db.close()
