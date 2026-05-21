from sqlalchemy import Column, BigInteger, String, Integer, DECIMAL, DateTime, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        Index("idx_budgets_year_month", "year", "month"),
        Index("idx_budgets_type_target", "type", "target_id"),
        UniqueConstraint("type", "target_id", "year", "month", name="uk_budgets_unique"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
    )
    id = Column(BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True)
    type = Column(String(20), nullable=False, comment="预算类型：global/pet/category")
    target_id = Column(String(50), nullable=True, comment="预算目标ID：pet_id或category_code，global时为null")
    year = Column(Integer, nullable=False, comment="预算年份")
    month = Column(Integer, nullable=False, comment="预算月份（1-12）")
    amount = Column(DECIMAL(10, 2), nullable=False, comment="预算金额")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
