"""Seed demo data（演示数据）。

Run with: ``uv run python -m app.seed``

幂等：每次运行先清空 boarding_orders / balance_transactions / cost_records /
pets / customers，再重新灌入一批。cost_categories / recharge_packages 由
Alembic 管理，不在此清空。

覆盖功能：客户/宠物/消费订单 + 储值充值 + 寄养（在住/超期/欠费多状态），
让客户打开系统即可看到所有功能的演示数据。
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, select

from .core.database import SessionLocal
from .crud import balance as balance_crud
from .crud import boarding as boarding_crud
from .models import (
    BalanceTransaction,
    BoardingOrder,
    CostCategory,
    CostRecord,
    Customer,
    Pet,
)


CUSTOMER_PROFILES = [
    {"name": "张伟", "phone": "13800001001", "note": "会员积分 3200，常带毛毛来洗澡"},
    {"name": "李娜", "phone": "13900002002", "note": "VIP 会员，最近收养了一只流浪猫"},
    {"name": "王强", "phone": "13700003003", "note": "两只金毛，每月全套护理 + 定期寄养"},
    {"name": "刘洋", "phone": "13600004004", "note": "长期寄养客户，出差频繁"},
    {"name": "陈静", "phone": "13500005005", "note": "新会员，刚办了储值卡"},
]

PET_TEMPLATES = [
    [
        {"name": "毛毛", "species": "dog", "breed": "柯基", "gender": "male"},
    ],
    [
        {"name": "豆豆", "species": "cat", "breed": "中华田园猫", "gender": "female"},
        {"name": "皮皮", "species": "cat", "breed": "英短", "gender": "male"},
    ],
    [
        {"name": "大金", "species": "dog", "breed": "金毛", "gender": "male"},
        {"name": "小金", "species": "dog", "breed": "金毛", "gender": "female"},
    ],
    [
        {"name": "豆腐", "species": "dog", "breed": "比熊", "gender": "female"},
    ],
    [
        {"name": "奶糖", "species": "cat", "breed": "布偶", "gender": "female"},
    ],
]


def _random_amount(rng: random.Random) -> Decimal:
    cents = rng.randint(1000, 50000)
    return Decimal(cents) / Decimal(100)


def _random_date_within(rng: random.Random, days_back: int = 180) -> date:
    today = date.today()
    delta = rng.randint(0, days_back)
    return today - timedelta(days=delta)


def run() -> None:
    rng = random.Random(42)

    with SessionLocal() as db:
        category_codes = list(db.scalars(select(CostCategory.code)).all())
        if not category_codes:
            raise RuntimeError(
                "cost_categories is empty — run `alembic upgrade head` first."
            )
        # 普通消费用的分类（排除 boarding，寄养费由寄养流程单独生成）
        normal_codes = [c for c in category_codes if c != "boarding"] or category_codes

        # 清空（注意顺序：先子后父）。boarding_orders 删除会级联删其寄养扣费记录
        db.execute(delete(BoardingOrder))
        db.execute(delete(BalanceTransaction))
        db.execute(delete(CostRecord))
        db.execute(delete(Pet))
        db.execute(delete(Customer))
        db.commit()

        # 客户
        customers: list[Customer] = []
        for profile in CUSTOMER_PROFILES:
            obj = Customer(**profile)
            db.add(obj)
            customers.append(obj)
        db.flush()

        # 宠物
        pets: list[Pet] = []
        pets_by_customer: dict[int, list[Pet]] = {}
        for customer, pet_specs in zip(customers, PET_TEMPLATES):
            pets_by_customer[customer.id] = []
            for spec in pet_specs:
                pet = Pet(customer_id=customer.id, **spec, birthday=_random_date_within(rng, 1500))
                db.add(pet)
                pets.append(pet)
                pets_by_customer[customer.id].append(pet)
        db.flush()

        # 普通消费订单（现金 / 部分储值）
        cost_records: list[CostRecord] = []
        for pet in pets:
            count = rng.randint(6, 12)
            for _ in range(count):
                pay = "balance" if rng.random() < 0.3 else "cash"
                cost_records.append(
                    CostRecord(
                        pet_id=pet.id,
                        category_code=rng.choice(normal_codes),
                        amount=_random_amount(rng),
                        occurred_on=_random_date_within(rng, 180),
                        pay_method=pay,
                        note=None,
                    )
                )
        db.add_all(cost_records)
        db.commit()

        # 储值充值：给前 4 个客户充值（含赠送），制造储值流水
        recharge_plan = [
            (customers[0], Decimal("1000"), Decimal("200"), "wechat"),
            (customers[1], Decimal("2000"), Decimal("600"), "alipay"),
            (customers[2], Decimal("500"), Decimal("50"), "cash"),
            (customers[4], Decimal("500"), Decimal("50"), "wechat"),
        ]
        for cust, amount, bonus, channel in recharge_plan:
            balance_crud.recharge(
                db, cust, amount=amount, bonus_amount=bonus, channel=channel,
                note="开业活动充值",
            )

        # 寄养单：覆盖 在住正常 / 在住超期 / 已退房 三种状态
        today = date.today()
        boarding_specs = [
            # 刘洋的豆腐：在住，5天前入住，约定10天（正常在住）
            (pets_by_customer[customers[3].id][0], today - timedelta(days=5), 10, Decimal("80")),
            # 王强的大金：在住，12天前入住，约定7天（已超期，持续扣费）
            (pets_by_customer[customers[2].id][0], today - timedelta(days=12), 7, Decimal("100")),
            # 陈静的奶糖：在住，3天前入住，约定30天（长期寄养，余额会被扣成欠费）
            (pets_by_customer[customers[4].id][0], today - timedelta(days=3), 30, Decimal("120")),
        ]
        boarding_count = 0
        for pet, check_in, days, rate in boarding_specs:
            order = boarding_crud.create(
                db,
                pet_id=pet.id,
                customer_id=pet.customer_id,
                check_in_date=check_in,
                expected_days=days,
                daily_rate=rate,
                note="演示寄养单",
                settle_today=True,
                today=today,
            )
            boarding_count += 1
            _ = order

        # 一条已退房的寄养单（张伟的毛毛，上个月住了5天）
        last_in = today - timedelta(days=40)
        closed_order = boarding_crud.create(
            db,
            pet_id=pets_by_customer[customers[0].id][0].id,
            customer_id=customers[0].id,
            check_in_date=last_in,
            expected_days=5,
            daily_rate=Decimal("80"),
            note="演示已退房寄养单",
            settle_today=False,
            today=today,
        )
        boarding_crud.close(db, closed_order, check_out_date=last_in + timedelta(days=5))
        boarding_count += 1

        print(
            f"Seeded: {len(customers)} customers, {len(pets)} pets, "
            f"{len(cost_records)} normal cost records, "
            f"{len(recharge_plan)} recharges, {boarding_count} boarding orders"
        )


if __name__ == "__main__":
    run()
