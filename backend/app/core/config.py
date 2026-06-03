from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite:///./dev.db"
    CORS_ORIGINS: List[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    DEBUG: bool = False

    # 客户分层阈值（按累计贡献金额：充值本金 + 现金消费，不含赠送、不含储值消费避免重复计）
    # 0=新客 / (0,VIP)=回头客 / [VIP,SVIP)=VIP / [SVIP,SUPREME)=SVIP / >=SUPREME=至尊VIP
    VIP_AMOUNT: int = 500
    SVIP_AMOUNT: int = 2000
    SUPREME_AMOUNT: int = 5000

    # 单管理员鉴权（环境变量驱动，不建 users 表）
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = ""        # bcrypt 哈希；空表示未配置
    JWT_SECRET_KEY: str = ""             # >=32 字节随机串；空表示未配置
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720   # 12h

settings = Settings()
