"""
Zach's Liquor Store — Core Configuration
All settings loaded from environment variables with secure defaults.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Zach's Liquor Store"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/zachsliquor"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Security
    secret_key: str = "CHANGE-THIS-IN-PRODUCTION-USE-256-BIT-KEY"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    max_login_attempts: int = 5
    lockout_minutes: int = 15

    # MFA
    mfa_issuer: str = "Zachs Liquor Store"
    mfa_totp_enabled: bool = True

    # SMS (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # Redis (for sessions, rate limiting)
    redis_url: str = "redis://localhost:6379/0"

    # Supplier monitoring
    supplier_check_interval_minutes: int = 60
    breakthru_username: Optional[str] = None
    breakthru_password: Optional[str] = None
    rndc_username: Optional[str] = None
    rndc_password: Optional[str] = None

    # Pricing AI
    default_markup_pct: float = 35.0
    min_margin_pct: float = 20.0

    # Frontend URL (for CORS)
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
