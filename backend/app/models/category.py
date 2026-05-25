from sqlalchemy import Column, Integer, Numeric, String

from ..core.database import Base


class CostCategory(Base):
    __tablename__ = "cost_categories"
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    code = Column(String(30), primary_key=True)
    label = Column(String(30), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
    default_amount = Column(Numeric(10, 2), nullable=True)
