from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PetBase(BaseModel):
    customer_id: int
    name: str = Field(..., max_length=50)
    species: Optional[str] = Field(None, max_length=20)
    breed: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=10)
    birthday: Optional[date] = None
    note: Optional[str] = None


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    customer_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=50)
    species: Optional[str] = Field(None, max_length=20)
    breed: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=10)
    birthday: Optional[date] = None
    note: Optional[str] = None


class PetOut(PetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PetListItem(PetOut):
    """列表项：在 PetOut 基础上附加最近一次到店时间（按 cost_records.occurred_on 取 MAX）
    和主人姓名（避免前端只显示客户 ID）。

    无任何消费记录时 last_visit_at 为 None，前端展示"—"。
    """

    last_visit_at: Optional[date] = None
    customer_name: Optional[str] = None
