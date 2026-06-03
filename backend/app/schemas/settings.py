from decimal import Decimal

from pydantic import BaseModel, Field


class TierConfigOut(BaseModel):
    vip_amount: Decimal
    svip_amount: Decimal
    supreme_amount: Decimal
    vip_discount: int
    svip_discount: int
    supreme_discount: int


class TierConfigUpdate(BaseModel):
    """折扣率为付款百分比：98=98折，90=9折。"""

    vip_amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    svip_amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    supreme_amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    vip_discount: int = Field(..., ge=50, le=100)
    svip_discount: int = Field(..., ge=50, le=100)
    supreme_discount: int = Field(..., ge=50, le=100)
