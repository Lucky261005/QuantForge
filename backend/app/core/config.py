"""Application configuration, loaded from environment variables / .env."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET_KEY = "dev-secret-key-change-in-production-please"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "QuantForge"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Security ---
    SECRET_KEY: str = Field(default=_DEFAULT_SECRET_KEY)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_COOKIE_ENABLED: bool = False  # opt-in httpOnly refresh-token cookie, alongside the bearer-token flow
    AUTH_COOKIE_SECURE: bool = True  # requires HTTPS; only disable for plain-HTTP local dev

    @model_validator(mode="after")
    def _reject_default_secret_in_production(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == _DEFAULT_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY is still set to its development default while ENVIRONMENT=production. "
                "Set a real, random SECRET_KEY before starting the app in production."
            )
        return self

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./quantforge.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT_SECONDS: int = 30

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- Email (no provider wired up) ---
    # Outside production, outgoing emails are written as files here instead of sent,
    # like a local mail catcher. Production sends nothing until a provider is added.
    DEV_OUTBOX_DIR: str = "dev_outbox"
    FRONTEND_URL: str = "http://localhost:3000"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # --- Market data providers ---
    ALPHA_VANTAGE_API_KEY: str | None = None
    POLYGON_API_KEY: str | None = None
    MARKET_DATA_CACHE_TTL_SECONDS: int = 3600
    MAX_CSV_UPLOAD_BYTES: int = 5 * 1024 * 1024

    # --- Indian broker/exchange market data providers ---
    # Real implementations behind the same MarketDataProvider interface as Yahoo/Alpha
    # Vantage/Polygon; each activates automatically once its credentials are set. None
    # were tested against the live APIs in this build (no broker accounts available).
    KITE_API_KEY: str | None = None
    KITE_ACCESS_TOKEN: str | None = None  # obtained via Kite Connect's daily login flow
    UPSTOX_ACCESS_TOKEN: str | None = None  # OAuth2 access token from Upstox's login flow
    ANGEL_ONE_API_KEY: str | None = None
    ANGEL_ONE_JWT_TOKEN: str | None = None  # obtained via SmartAPI's /loginByPassword
    ANGEL_ONE_CLIENT_CODE: str | None = None

    # --- Rate limiting ---
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_DATA_DOWNLOAD: str = "20/minute"
    RATE_LIMIT_DEFAULT: str = "200/minute"
    # Backtest creation can trigger a Celery job or, if the broker is unreachable, a
    # synchronous in-request simulation — capped tighter than the app default so it
    # can't be used to exhaust worker/API capacity.
    RATE_LIMIT_BACKTEST_CREATE: str = "20/minute"
    RATE_LIMIT_WRITE: str = "60/minute"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
