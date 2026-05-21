from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime

class BudgetBase(BaseModel):
    type: str = Field(..., description="预算类型：global/pet/category", max_length=20)
    target_id: Optional[str] = Field(None, description="预算目标ID，pet_id或category_code", max_length=50)
    year: int = Field(..., ge=2020, le=2100, description="预算年份")
    month: int = Field(..., ge=1, le=12, description="预算月份")
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="预算金额")

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2, description="预算金额")

class Budget(BudgetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spent: Decimal = Field(..., description="已花费金额")
    remaining: Decimal = Field(..., description="剩余金额")
    overspent: bool = Field(..., description="是否超支")
    created_at: datetime
    updated_at: datetime
