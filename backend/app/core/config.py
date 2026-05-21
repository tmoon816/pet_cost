from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    DATABASE_URL: str = "sqlite:///./dev.db"
    CORS_ORIGINS: List[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    DEBUG: bool = False

settings = Settings()
