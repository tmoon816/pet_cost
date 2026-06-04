from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    Numeric,
    String,
    func,
)

from ..core.database import Base


class RechargePackage(Base):
    """充值套餐（预设方案）。

    店长在「套餐充值」页选一个套餐 + 一个客户即可完成充值：
      到账余额 = price（实付本金） + bonus_amount（赠送金额）
      gifts 为随充赠送的实物商品清单，仅记入流水备注，不进余额。

    套餐本身可启用/停用、排序、标记推荐档（前端高亮）。
    """

    __tablename__ = "recharge_packages"
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id = Column(BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)                       # 套餐名：基础 / Pro / Max
    subtitle = Column(String(100), nullable=True)                   # 一句话卖点
    price = Column(Numeric(10, 2), nullable=False)                  # 实付本金
    bonus_amount = Column(Numeric(10, 2), nullable=False, server_default="0")  # 赠送金额
    gifts = Column(JSON, nullable=False, default=list)              # 赠品清单 ["猫砂1袋", ...]
    highlights = Column(JSON, nullable=False, default=list)         # 卖点列表 ["专属顾问", ...]
    badge = Column(String(20), nullable=True)                       # 角标：最受欢迎 / 超值
    is_recommended = Column(Boolean, nullable=False, server_default="0")  # 推荐档高亮
    is_active = Column(Boolean, nullable=False, server_default="1")
    sort_order = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
