from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class CostRecord(Base):
    __tablename__ = "cost_records"
    __table_args__ = (
        Index("idx_costs_pet_date", "pet_id", "occurred_on"),
        Index("idx_costs_category", "category_code"),
        Index("idx_costs_occurred", "occurred_on"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id = Column(BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True)
    pet_id = Column(
        BigInteger().with_variant(Integer(), "sqlite"),
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_code = Column(String(30), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    # 会员折扣省下的金额（折后实付记在 amount，这里记优惠额，默认 0）
    discount_amount = Column(Numeric(10, 2), nullable=False, server_default="0")
    # 支付方式：balance=扣储值余额 / cash=现金（不动余额）。历史数据默认 cash。
    pay_method = Column(String(20), nullable=False, server_default="cash")
    occurred_on = Column(Date, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    pet = relationship("Pet", back_populates="costs")
