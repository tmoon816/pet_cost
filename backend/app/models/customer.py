from sqlalchemy import BigInteger, Column, DateTime, Index, Integer, Numeric, String, Text, event, func
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..core.pinyin import to_initials, to_pinyin


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index("idx_customers_phone", "phone"),
        Index("idx_customers_name", "name"),
        Index("idx_customers_name_pinyin", "name_pinyin"),
        Index("idx_customers_name_initials", "name_initials"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id = Column(BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    name_pinyin = Column(String(255), nullable=False, server_default="")
    name_initials = Column(String(50), nullable=False, server_default="")
    phone = Column(String(20), nullable=True)
    note = Column(Text, nullable=True)
    balance = Column(Numeric(10, 2), nullable=False, server_default="0")  # 储值余额（含赠送）
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    pets = relationship(
        "Pet",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    balance_transactions = relationship(
        "BalanceTransaction",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


def _sync_customer_pinyin(_mapper, _connection, target: Customer) -> None:
    target.name_pinyin = to_pinyin(target.name)
    target.name_initials = to_initials(target.name)


event.listen(Customer, "before_insert", _sync_customer_pinyin)
event.listen(Customer, "before_update", _sync_customer_pinyin)
