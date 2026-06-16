import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load the project-level .env file regardless of where uvicorn is started.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_list_env(name: str, default: str) -> List[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    email_token_expire_minutes: int
    password_reset_token_expire_minutes: int
    frontend_origins: List[str]
    frontend_base_url: str


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
    )


settings = get_settings()
