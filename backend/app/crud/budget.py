from typing import Optional, List, Any, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.crud import cost as crud_cost


def _to_dict_with_spent(db: Session, budget: Budget) -> Dict[str, Any]:
    """把 ORM 对象 + 计算字段打包成 dict 返回，避免动态属性挂载污染 ORM。"""
    spent = _calculate_spent(db, budget)
    remaining = budget.amount - spent
    return {
        "id": budget.id,
        "type": budget.type,
        "target_id": budget.target_id,
        "year": budget.year,
        "month": budget.month,
        "amount": budget.amount,
        "spent": spent,
        "remaining": remaining,
        "overspent": remaining < Decimal(0),
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
    }


def get(db: Session, budget_id: int) -> Optional[Dict[str, Any]]:
    budget = db.get(Budget, budget_id)
    if budget is None:
        return None
    return _to_dict_with_spent(db, budget)


def get_by_month(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    budgets = db.query(Budget).filter(Budget.year == year, Budget.month == month).all()
    return [_to_dict_with_spent(db, b) for b in budgets]


def get_by_type_target_month(
    db: Session,
    type: str,
    target_id: Optional[str],
    year: int,
    month: int,
) -> Optional[Dict[str, Any]]:
    budget = db.query(Budget).filter(
        Budget.type == type,
        Budget.target_id == target_id,
        Budget.year == year,
        Budget.month == month,
    ).first()
    if budget is None:
        return None
    return _to_dict_with_spent(db, budget)


def create(db: Session, obj_in: BudgetCreate) -> Dict[str, Any]:
    obj = Budget(**obj_in.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _to_dict_with_spent(db, obj)


def update(db: Session, budget_id: int, obj_in: BudgetUpdate) -> Optional[Dict[str, Any]]:
    db_obj = db.get(Budget, budget_id)
    if db_obj is None:
        return None
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return _to_dict_with_spent(db, db_obj)


def remove(db: Session, id: int) -> bool:
    obj = db.get(Budget, id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def _calculate_spent(db: Session, budget: Budget) -> Decimal:
    start_date = f"{budget.year}-{budget.month:02d}-01"
    if budget.month == 12:
        end_date = f"{budget.year + 1}-01-01"
    else:
        end_date = f"{budget.year}-{budget.month + 1:02d}-01"
    if budget.type == "global":
        total = crud_cost.get_total_by_date_range(db, start_date, end_date)
    elif budget.type == "pet":
        total = crud_cost.get_total_by_pet_and_date_range(
            db, int(budget.target_id), start_date, end_date
        )
    elif budget.type == "category":
        total = crud_cost.get_total_by_category_and_date_range(
            db, budget.target_id, start_date, end_date
        )
    else:
        total = Decimal(0)
    return total or Decimal(0)
