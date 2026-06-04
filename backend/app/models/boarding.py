from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class BoardingOrder(Base):
    """寄养单：按天自动扣费。

    数据准确性设计：
    - ``settled_through`` 是"已结算到的日期（含）"游标。每日结算只处理
      ``(settled_through, today]`` 区间，天然幂等：重复跑当天不会重复扣。
    - 每天扣费会生成一条 ``cost_records``（category=boarding），并通过
      ``cost_records`` 上 ``(boarding_order_id, occurred_on)`` 唯一约束在
      数据库层兜底，杜绝任何重复扣费。
    - ``total_charged`` 为累计已扣快照，用于对账（应 == 名下寄养日扣费之和）。
    - 余额扣成负数表示欠费，结算照常进行（与普通开单的"余额不足拒绝"不同）。
    """

    __tablename__ = "boarding_orders"
    __table_args__ = (
        Index("idx_boarding_pet", "pet_id"),
        Index("idx_boarding_customer", "customer_id"),
        Index("idx_boarding_status", "status"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id = Column(BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True)
    pet_id = Column(
        BigInteger().with_variant(Integer(), "sqlite"),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 客户冗余存一份：扣费要找钱包，且寄养结算需稳定指向办理时的客户
    customer_id = Column(
        BigInteger().with_variant(Integer(), "sqlite"),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_in_date = Column(Date, nullable=False)            # 入住日（计费第一天）
    expected_days = Column(Integer, nullable=False)         # 约定天数（超出即预警）
    daily_rate = Column(Numeric(10, 2), nullable=False)     # 每日单价
    status = Column(String(20), nullable=False, server_default="active")  # active / closed
    check_out_date = Column(Date, nullable=True)            # 退房日（结算封口）
    settled_through = Column(Date, nullable=True)           # 已结算到的日期（含）；null=尚未扣过
    total_charged = Column(Numeric(10, 2), nullable=False, server_default="0")  # 累计已扣（对账用）
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    pet = relationship("Pet")
    customer = relationship("Customer")
