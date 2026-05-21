from sqlalchemy import Column, Integer, String

from ..core.database import Base


class CostCategory(Base):
    __tablename__ = "cost_categories"
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    code = Column(String(30), primary_key=True)
    label = Column(String(30), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0, server_default="0")
