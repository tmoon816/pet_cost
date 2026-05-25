from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CostBase(BaseModel):
    pet_id: int
    category_code: str = Field(..., max_length=30)
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    occurred_on: date
    note: Optional[str] = None


class CostCreate(CostBase):
    pass


class CostUpdate(BaseModel):
    pet_id: Optional[int] = None
    category_code: Optional[str] = Field(None, max_length=30)
    amount: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    occurred_on: Optional[date] = None
    note: Optional[str] = None


class CostBatchCreate(BaseModel):
    """T-029: 同金额同分类同日期，给多只宠物批量开单（事务原子）。"""

    pet_ids: List[int] = Field(..., min_length=1, max_length=20)
    category_code: str = Field(..., max_length=30)
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    occurred_on: date
    note: Optional[str] = None


class CostOut(CostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
