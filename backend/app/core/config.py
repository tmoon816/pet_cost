from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite:///./dev.db"
    CORS_ORIGINS: List[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    DEBUG: bool = False

    # P-006: 客户分层阈值（消费记录数）。0 单=first_visit，1~VIP_THRESHOLD-1=returning，>=VIP_THRESHOLD=vip
    VIP_THRESHOLD: int = 5

settings = Settings()
