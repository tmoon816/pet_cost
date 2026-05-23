from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, event, func
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..core.pinyin import to_initials, to_pinyin


class Pet(Base):
    __tablename__ = "pets"
    __table_args__ = (
        Index("idx_pets_customer", "customer_id"),
        Index("idx_pets_name_pinyin", "name_pinyin"),
        Index("idx_pets_name_initials", "name_initials"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id = Column(BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True)
    customer_id = Column(
        BigInteger().with_variant(Integer(), "sqlite"),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(50), nullable=False)
    name_pinyin = Column(String(255), nullable=False, server_default="")
    name_initials = Column(String(50), nullable=False, server_default="")
    species = Column(String(20), nullable=True)
    breed = Column(String(50), nullable=True)
    gender = Column(String(10), nullable=True)
    birthday = Column(Date, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="pets")
    costs = relationship(
        "CostRecord",
        back_populates="pet",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


def _sync_pet_pinyin(_mapper, _connection, target: Pet) -> None:
    target.name_pinyin = to_pinyin(target.name)
    target.name_initials = to_initials(target.name)


event.listen(Pet, "before_insert", _sync_pet_pinyin)
event.listen(Pet, "before_update", _sync_pet_pinyin)
