from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    name: str = Field(..., max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CustomerListItem(CustomerOut):
    """T-008: 列表项额外携带 has_cost（首次有消费即老客）。
    T-015: 额外返回 total_amount（名下所有宠物累计消费，无消费为 0）。
    """

    has_cost: bool = False
    total_amount: Decimal = Decimal(0)


class CustomerWithPets(CustomerOut):
    pets: List["PetOut"] = []


class CustomerSummary(BaseModel):
    """T-007：客户详情页聚合卡片。无消费时 last_visit_at 为 None、金额 0、计数 0。"""

    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    total_amount: Decimal
    last_visit_at: Optional[datetime] = None
    cost_count: int


from .pet import PetOut  # noqa: E402  resolve forward ref

CustomerWithPets.model_rebuild()
