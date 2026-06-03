from sqlalchemy import (
    BigInteger,
    Column,
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


class BalanceTransaction(Base):
    """储值流水账本（append-only）。

    每一笔余额变动都留痕，含变动后余额快照，保证可对账、可追溯。
    `amount` 为对余额的带符号增量：充值/退款为正，消费为负。
    `cost_id` 仅作审计引用，**不建外键**——订单删除后流水仍需保留。
    """

    __tablename__ = "balance_transactions"
    __table_args__ = (
        Index("idx_baltxn_customer", "customer_id"),
        Index("idx_baltxn_created", "created_at"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id = Column(BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True)
    customer_id = Column(
        BigInteger().with_variant(Integer(), "sqlite"),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    # recharge=充值 / consume=消费扣款 / refund=退款 / adjust=手动调整
    type = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)            # 带符号增量
    bonus_amount = Column(Numeric(10, 2), nullable=False, server_default="0")  # 充值赠送部分
    discount_amount = Column(Numeric(10, 2), nullable=False, server_default="0")  # 会员折扣省下的钱（消费时）
    balance_after = Column(Numeric(10, 2), nullable=False)     # 变动后余额快照
    channel = Column(String(20), nullable=True)                # alipay/wechat/cash（仅充值）
    cost_id = Column(BigInteger().with_variant(Integer(), "sqlite"), nullable=True)  # 审计引用，无 FK
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    customer = relationship("Customer", back_populates="balance_transactions")
