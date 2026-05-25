from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    label: str = Field(..., max_length=30)
    sort_order: int = 0
    default_amount: Optional[Decimal] = Field(
        None, max_digits=10, decimal_places=2, ge=0
    )


class CategoryCreate(CategoryBase):
    code: str = Field(..., max_length=30)


class CategoryUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=30)
    sort_order: Optional[int] = None
    default_amount: Optional[Decimal] = Field(
        None, max_digits=10, decimal_places=2, ge=0
    )


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    code: str
