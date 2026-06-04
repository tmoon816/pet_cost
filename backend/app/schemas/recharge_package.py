from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RechargePackageBase(BaseModel):
    name: str = Field(..., max_length=50)
    subtitle: Optional[str] = Field(None, max_length=100)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    bonus_amount: Decimal = Field(Decimal(0), ge=0, max_digits=10, decimal_places=2)
    gifts: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    badge: Optional[str] = Field(None, max_length=20)
    is_recommended: bool = False
    is_active: bool = True
    sort_order: int = 0


class RechargePackageCreate(RechargePackageBase):
    pass


class RechargePackageUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    subtitle: Optional[str] = Field(None, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    bonus_amount: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    gifts: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    badge: Optional[str] = Field(None, max_length=20)
    is_recommended: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class RechargePackageOut(RechargePackageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PackageCheckoutRequest(BaseModel):
    """按套餐给指定客户充值。channel = 线下收款渠道。"""

    customer_id: int = Field(..., gt=0)
    channel: str = Field(..., pattern="^(alipay|wechat|cash)$")
    note: Optional[str] = None


class PackageCheckoutResult(BaseModel):
    customer_id: int
    customer_name: str
    package_id: int
    package_name: str
    paid_amount: Decimal      # 实付本金
    bonus_amount: Decimal     # 赠送金额
    credited: Decimal         # 实际到账 = paid + bonus
    gifts: List[str]
    balance: Decimal          # 充值后余额
    transaction_id: int
