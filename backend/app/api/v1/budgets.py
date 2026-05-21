from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.budget import Budget, BudgetCreate, BudgetUpdate
from app.crud import budget as crud_budget

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.get("", response_model=List[Budget])
def list_budgets(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """查询指定年月的所有预算"""
    return crud_budget.get_by_month(db, year=year, month=month)

@router.get("/{budget_id}", response_model=Budget)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """查询单个预算详情"""
    budget = crud_budget.get(db, budget_id=budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="budget_not_found")
    return budget

@router.post("", response_model=Budget)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db)
):
    """新建预算，同一目标同一月份重复创建返回409"""
    existing = crud_budget.get_by_type_target_month(db, type=data.type, target_id=data.target_id, year=data.year, month=data.month)
    if existing:
        raise HTTPException(status_code=409, detail="budget_already_exists")
    return crud_budget.create(db, obj_in=data)

@router.patch("/{budget_id}", response_model=Budget)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    db: Session = Depends(get_db)
):
    """更新预算金额"""
    budget = crud_budget.get(db, budget_id=budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="budget_not_found")
    return crud_budget.update(db, db_obj=budget, obj_in=data)

@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """删除预算"""
    budget = crud_budget.get(db, budget_id=budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="budget_not_found")
    crud_budget.remove(db, id=budget_id)
