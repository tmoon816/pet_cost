from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RechargeRequest(BaseModel):
    """手动虚拟充值。amount=实充本金，bonus_amount=赠送（充X送Y）。"""

    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    bonus_amount: Decimal = Field(Decimal(0), ge=0, max_digits=10, decimal_places=2)
    channel: str = Field(..., pattern="^(alipay|wechat|cash)$")
    note: Optional[str] = None


class BalanceAdjustRequest(BaseModel):
    """手动调整余额。amount 带符号：正为增、负为减。"""

    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    note: Optional[str] = None


class BalanceTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    type: str
    amount: Decimal
    bonus_amount: Decimal
    discount_amount: Decimal = Decimal(0)
    balance_after: Decimal
    channel: Optional[str] = None
    cost_id: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime


class BalanceOut(BaseModel):
    """充值/调整后返回最新余额。"""

    customer_id: int
    balance: Decimal
