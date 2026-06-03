"""客户分层阈值 + 折扣率配置。

存储在 app_settings 键值表；缺失时回退到 config.py 默认值。
折扣率语义：付款百分比（50~100）。98 = 98折（付 98%），90 = 9折。
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from ..core.config import settings as cfg
from ..models import AppSetting

# 阈值 key（金额，元）
K_VIP_AMOUNT = "tier_vip_amount"
K_SVIP_AMOUNT = "tier_svip_amount"
K_SUPREME_AMOUNT = "tier_supreme_amount"
# 折扣率 key（付款百分比 50~100）
K_VIP_DISCOUNT = "discount_vip"
K_SVIP_DISCOUNT = "discount_svip"
K_SUPREME_DISCOUNT = "discount_supreme"

_DEFAULTS: dict[str, str] = {
    K_VIP_AMOUNT: str(cfg.VIP_AMOUNT),
    K_SVIP_AMOUNT: str(cfg.SVIP_AMOUNT),
    K_SUPREME_AMOUNT: str(cfg.SUPREME_AMOUNT),
    K_VIP_DISCOUNT: "98",
    K_SVIP_DISCOUNT: "95",
    K_SUPREME_DISCOUNT: "90",
}


def _read_raw(db: Session) -> dict[str, str]:
    rows = {s.key: s.value for s in db.query(AppSetting).all()}
    merged = dict(_DEFAULTS)
    merged.update({k: v for k, v in rows.items() if k in _DEFAULTS})
    return merged


def get_tier_config(db: Session) -> dict:
    """返回结构化分层配置（数值已转型），供 API 与分层逻辑共用。"""
    raw = _read_raw(db)
    return {
        "vip_amount": Decimal(raw[K_VIP_AMOUNT]),
        "svip_amount": Decimal(raw[K_SVIP_AMOUNT]),
        "supreme_amount": Decimal(raw[K_SUPREME_AMOUNT]),
        "vip_discount": int(raw[K_VIP_DISCOUNT]),
        "svip_discount": int(raw[K_SVIP_DISCOUNT]),
        "supreme_discount": int(raw[K_SUPREME_DISCOUNT]),
    }


def classify(contribution: Decimal | float | int, tier: dict) -> str:
    """按金额 + 传入的阈值分层。tier 来自 get_tier_config。"""
    amount = Decimal(contribution or 0)
    if amount <= 0:
        return "first_visit"
    if amount >= tier["supreme_amount"]:
        return "supreme"
    if amount >= tier["svip_amount"]:
        return "svip"
    if amount >= tier["vip_amount"]:
        return "vip"
    return "regular"


def discount_for_type(customer_type: str, tier: dict) -> int:
    """该层级的付款百分比（50~100）。无折扣层级返回 100。"""
    if customer_type == "vip":
        return tier["vip_discount"]
    if customer_type == "svip":
        return tier["svip_discount"]
    if customer_type == "supreme":
        return tier["supreme_discount"]
    return 100


def update_tier_config(db: Session, payload: dict) -> dict:
    """校验后写入。payload 含 6 个字段（见 schemas.settings.TierConfigUpdate）。

    业务约束：0 < vip < svip < supreme；折扣率 50~100。
    """
    va = Decimal(str(payload["vip_amount"]))
    sa = Decimal(str(payload["svip_amount"]))
    pa = Decimal(str(payload["supreme_amount"]))
    if not (0 < va < sa < pa):
        raise ValueError("amount_order_invalid")
    for d in (payload["vip_discount"], payload["svip_discount"], payload["supreme_discount"]):
        if not (50 <= int(d) <= 100):
            raise ValueError("discount_range_invalid")

    mapping = {
        K_VIP_AMOUNT: _fmt(va),
        K_SVIP_AMOUNT: _fmt(sa),
        K_SUPREME_AMOUNT: _fmt(pa),
        K_VIP_DISCOUNT: str(int(payload["vip_discount"])),
        K_SVIP_DISCOUNT: str(int(payload["svip_discount"])),
        K_SUPREME_DISCOUNT: str(int(payload["supreme_discount"])),
    }
    for key, value in mapping.items():
        row = db.get(AppSetting, key)
        if row is None:
            db.add(AppSetting(key=key, value=value))
        else:
            row.value = value
    db.commit()
    return get_tier_config(db)


def _fmt(d: Decimal) -> str:
    """整数金额去掉小数尾巴，存得干净。"""
    if d == d.to_integral_value():
        return str(int(d))
    return str(d)
