from sqlalchemy import Column, DateTime, String, Text, func

from ..core.database import Base


class AppSetting(Base):
    """通用键值配置表。当前用于客户分层阈值与折扣（key 见 crud/settings.py）。

    value 统一存字符串，按 key 自行解析（数值类 key 存十进制字符串）。
    """

    __tablename__ = "app_settings"
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
