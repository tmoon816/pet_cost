from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...crud import boarding as crud_boarding
from ...crud import customer as crud_customer
from ...crud import pet as crud_pet
from ...models import BoardingOrder, Customer, Pet
from ...schemas.boarding import (
    BoardingAlert,
    BoardingClose,
    BoardingCreate,
    BoardingOut,
    BoardingSettleResult,
)

router = APIRouter(prefix="/boarding", tags=["boarding"])


def _enrich(db: Session, order: BoardingOrder, today: date | None = None) -> dict:
    """给寄养单补充展示用计算字段。"""
    today = today or date.today()
    pet = db.get(Pet, order.pet_id)
    customer = db.get(Customer, order.customer_id)

    # 已住天数：closed 用退房日，否则用今天；含入住日当天
    end = order.check_out_date if (order.status == "closed" and order.check_out_date) else today
    days_stayed = max(0, (end - order.check_in_date).days + (0 if order.status == "closed" else 1))
    if order.status == "closed" and order.check_out_date:
        days_stayed = max(0, (order.check_out_date - order.check_in_date).days)

    overdue_days = max(0, days_stayed - order.expected_days) if order.status == "active" else 0
    data = BoardingOut.model_validate(order).model_dump()
    data["pet_name"] = pet.name if pet else None
    data["customer_name"] = customer.name if customer else None
    data["days_stayed"] = days_stayed
    data["is_overdue"] = overdue_days > 0
    data["overdue_days"] = overdue_days
    data["customer_balance"] = customer.balance if customer else None
    return data


@router.get("", response_model=list[BoardingOut])
def list_boarding(
    status: str | None = Query(None, pattern="^(active|closed)$"),
    customer_id: int | None = None,
    db: Session = Depends(get_db),
):
    orders = crud_boarding.list_all(db, status=status, customer_id=customer_id)
    return [_enrich(db, o) for o in orders]


@router.post("", response_model=BoardingOut, status_code=201)
def create_boarding(data: BoardingCreate, db: Session = Depends(get_db)):
    pet = crud_pet.get(db, data.pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="pet_not_found")
    customer = crud_customer.get(db, pet.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="customer_not_found")
    order = crud_boarding.create(
        db,
        pet_id=data.pet_id,
        customer_id=pet.customer_id,
        check_in_date=data.check_in_date,
        expected_days=data.expected_days,
        daily_rate=data.daily_rate,
        note=data.note,
    )
    return _enrich(db, order)


@router.post("/{boarding_id}/close", response_model=BoardingOut)
def close_boarding(boarding_id: int, data: BoardingClose, db: Session = Depends(get_db)):
    order = crud_boarding.get(db, boarding_id)
    if order is None:
        raise HTTPException(status_code=404, detail="boarding_not_found")
    if order.status == "closed":
        raise HTTPException(status_code=400, detail="already_closed")
    if data.check_out_date < order.check_in_date:
        raise HTTPException(status_code=400, detail="checkout_before_checkin")
    order = crud_boarding.close(db, order, check_out_date=data.check_out_date)
    return _enrich(db, order)


@router.post("/settle", response_model=BoardingSettleResult)
def settle_boarding(db: Session = Depends(get_db)):
    """手动触发：把所有在住寄养单结算到今天。结算引擎幂等，可随时重复调用。"""
    return crud_boarding.settle_all_active(db)


@router.get("/alerts", response_model=list[BoardingAlert])
def boarding_alerts(db: Session = Depends(get_db)):
    """寄养提醒：超期未退 / 余额欠费（负）。供顶部铃铛展示。"""
    today = date.today()
    alerts: list[dict] = []
    orders = crud_boarding.list_all(db, status="active")
    for o in orders:
        info = _enrich(db, o, today)
        pet_name = info["pet_name"] or f"宠物#{o.pet_id}"
        cust_name = info["customer_name"] or f"客户#{o.customer_id}"
        if info["is_overdue"]:
            alerts.append({
                "type": "overdue",
                "boarding_id": o.id,
                "pet_id": o.pet_id,
                "pet_name": pet_name,
                "customer_id": o.customer_id,
                "customer_name": cust_name,
                "message": f"{pet_name} 寄养已超约定 {info['overdue_days']} 天，仍在持续扣费",
                "overdue_days": info["overdue_days"],
            })
        bal = info["customer_balance"]
        if bal is not None and bal < 0:
            alerts.append({
                "type": "arrears",
                "boarding_id": o.id,
                "pet_id": o.pet_id,
                "pet_name": pet_name,
                "customer_id": o.customer_id,
                "customer_name": cust_name,
                "message": f"{cust_name} 余额已欠费 ¥{abs(bal):.2f}（{pet_name} 寄养中）",
                "balance": bal,
            })
    return alerts


@router.delete("/{boarding_id}", status_code=204)
def delete_boarding(boarding_id: int, db: Session = Depends(get_db)):
    order = crud_boarding.get(db, boarding_id)
    if order is None:
        raise HTTPException(status_code=404, detail="boarding_not_found")
    crud_boarding.remove(db, order)
