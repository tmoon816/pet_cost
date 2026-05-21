from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    label: str = Field(..., max_length=30)
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    code: str = Field(..., max_length=30)


class CategoryUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=30)
    sort_order: Optional[int] = None


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    code: str
