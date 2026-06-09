from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BoardingCreate(BaseModel):
    pet_id: int = Field(..., gt=0)
    check_in_date: date
    expected_days: int = Field(..., gt=0, le=3650)
    daily_rate: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    note: Optional[str] = None


class BoardingClose(BaseModel):
    check_out_date: date


class BoardingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    customer_id: int
    check_in_date: date
    expected_days: int
    daily_rate: Decimal
    status: str
    check_out_date: Optional[date] = None
    settled_through: Optional[date] = None
    total_charged: Decimal
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 计算字段（CRUD/路由注入）
    pet_name: Optional[str] = None
    customer_name: Optional[str] = None
    days_stayed: Optional[int] = None      # 已住天数（截至今天 / 退房日）
    is_overdue: Optional[bool] = None      # 是否已超约定天数
    overdue_days: Optional[int] = None     # 超出天数
    customer_balance: Optional[Decimal] = None  # 客户当前余额（负=欠费）


class BoardingSettleResult(BaseModel):
    orders_processed: int
    days_charged: int
    errors: List[int] = []


class BoardingAlert(BaseModel):
    """寄养相关提醒：超期 / 欠费。供顶部铃铛展示。"""

    type: str          # overdue / arrears
    boarding_id: int
    pet_id: int
    pet_name: str
    customer_id: int
    customer_name: str
    message: str
    overdue_days: Optional[int] = None
    balance: Optional[Decimal] = None
