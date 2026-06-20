import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Always load the project-level .env file, even when uvicorn is started from backend/.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_list_env(name: str, default: str) -> List[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from the project-level .env file.

    The app supports two database configuration styles:
    1. DATABASE_URL=... for production/deployment platforms.
    2. DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME for local MySQL Workbench.

    If DATABASE_URL is present, it wins. Otherwise, resolved_database_url is built
    from the separated DB_* values.
    """

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    email_token_expire_minutes: int
    password_reset_token_expire_minutes: int
    frontend_origins: List[str]
    frontend_base_url: str

    database_url: str | None
    db_driver: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    database_echo: bool
    seed_demo_data: bool
    auto_create_db: bool
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout: int
    db_pool_recycle: int
    db_connect_timeout: int
    app_environment: str
    allowed_hosts: List[str]
    gzip_minimum_size: int
    threadpool_tokens: int
    product_cache_max_age_seconds: int
    deployment_mode: str
    service_replicas: int
    service_instance_name: str

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        username = quote_plus(self.db_user)
        password = quote_plus(self.db_password)

        if self.db_driver.startswith("sqlite"):
            return f"sqlite:///{self.db_name}"

        return (
            f"{self.db_driver}://{username}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings(
        secret_key=os.getenv(
            "SECRET_KEY",
            "change-this-development-secret-key-before-production-use",
        ),
        algorithm=os.getenv("ALGORITHM", "HS256"),
        access_token_expire_minutes=_get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 15),
        refresh_token_expire_days=_get_int_env("REFRESH_TOKEN_EXPIRE_DAYS", 7),
        email_token_expire_minutes=_get_int_env("EMAIL_TOKEN_EXPIRE_MINUTES", 60),
        password_reset_token_expire_minutes=_get_int_env(
            "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 15
        ),
        frontend_origins=_get_list_env(
            "FRONTEND_ORIGINS",
            "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
        ),
        frontend_base_url=os.getenv("FRONTEND_BASE_URL", "http://localhost:5173"),
        database_url=os.getenv("DATABASE_URL") or None,
        db_driver=os.getenv("DB_DRIVER", "mysql+pymysql"),
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=_get_int_env("DB_PORT", 3306),
        db_name=os.getenv("DB_NAME", "finmark_db"),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", ""),
        database_echo=_get_bool_env("DATABASE_ECHO", False),
        seed_demo_data=_get_bool_env("SEED_DEMO_DATA", True),
        auto_create_db=_get_bool_env("AUTO_CREATE_DB", True),
        db_pool_size=_get_int_env("DB_POOL_SIZE", 20),
        db_max_overflow=_get_int_env("DB_MAX_OVERFLOW", 40),
        db_pool_timeout=_get_int_env("DB_POOL_TIMEOUT", 30),
        db_pool_recycle=_get_int_env("DB_POOL_RECYCLE", 1800),
        db_connect_timeout=_get_int_env("DB_CONNECT_TIMEOUT", 10),
        app_environment=os.getenv("APP_ENV", "development"),
        allowed_hosts=_get_list_env("ALLOWED_HOSTS", "*"),
        gzip_minimum_size=_get_int_env("GZIP_MINIMUM_SIZE", 1000),
        threadpool_tokens=_get_int_env("THREADPOOL_TOKENS", 100),
        product_cache_max_age_seconds=_get_int_env("PRODUCT_CACHE_MAX_AGE_SECONDS", 60),
        deployment_mode=os.getenv("DEPLOYMENT_MODE", "single-app"),
        service_replicas=_get_int_env("SERVICE_REPLICAS", 3),
        service_instance_name=os.getenv("SERVICE_INSTANCE_NAME", ""),
    )


settings = get_settings()
