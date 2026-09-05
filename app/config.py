"""Application configuration — all secrets come from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Maalim API"
    ENVIRONMENT: str = "development"  # development | production
    SECRET_KEY: str = "dev-secret-change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    DATABASE_URL: str = "sqlite:///./maalim.db"  # sqlite dev; postgres in prod
    CORS_ORIGINS: str = "*"  # comma-separated list in production
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
