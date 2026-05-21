from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate
from app.crud import cost as crud_cost

def get(db: Session, budget_id: int) -> Optional[Budget]:
    budget = db.get(Budget, budget_id)
    if budget:
        spent = _calculate_spent(db, budget)
        budget.spent = spent
        budget.remaining = budget.amount - spent
        budget.overspent = budget.remaining < Decimal(0)
    return budget

def get_by_month(db: Session, year: int, month: int) -> List[Budget]:
    budgets = db.query(Budget).filter(Budget.year == year, Budget.month == month).all()
    # 计算每个预算的已花金额、剩余、是否超支
    for budget in budgets:
        spent = _calculate_spent(db, budget)
        budget.spent = spent
        budget.remaining = budget.amount - spent
        budget.overspent = budget.remaining < Decimal(0)
    return budgets

def get_by_type_target_month(db: Session, type: str, target_id: Optional[str], year: int, month: int) -> Optional[Budget]:
    budget = db.query(Budget).filter(
        Budget.type == type,
        Budget.target_id == target_id,
        Budget.year == year,
        Budget.month == month
    ).first()
    if budget:
        spent = _calculate_spent(db, budget)
        budget.spent = spent
        budget.remaining = budget.amount - spent
        budget.overspent = budget.remaining < Decimal(0)
    return budget

def create(db: Session, obj_in: BudgetCreate) -> Budget:
    obj = Budget(**obj_in.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # 计算花费信息
    spent = _calculate_spent(db, obj)
    obj.spent = spent
    obj.remaining = obj.amount - spent
    obj.overspent = obj.remaining < Decimal(0)
    return obj

def update(db: Session, db_obj: Budget, obj_in: BudgetUpdate) -> Budget:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    # 计算花费信息
    spent = _calculate_spent(db, db_obj)
    db_obj.spent = spent
    db_obj.remaining = db_obj.amount - spent
    db_obj.overspent = db_obj.remaining < Decimal(0)
    return db_obj

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
        end_date = f"{budget.year +1}-01-01"
    else:
        end_date = f"{budget.year}-{budget.month +1:02d}-01"
    if budget.type == "global":
        # 全局总预算：所有花费
        total = crud_cost.get_total_by_date_range(db, start_date, end_date)
    elif budget.type == "pet":
        # 单宠物预算
        total = crud_cost.get_total_by_pet_and_date_range(db, int(budget.target_id), start_date, end_date)
    elif budget.type == "category":
        # 分类预算
        total = crud_cost.get_total_by_category_and_date_range(db, budget.target_id, start_date, end_date)
    else:
        total = Decimal(0)
    return total or Decimal(0)
