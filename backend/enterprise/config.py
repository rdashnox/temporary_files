"""Enterprise microservice configuration.

This module keeps the enterprise deployment settings separate from the original
single-app settings so the project can run in two modes:

1. normal school/local FastAPI app, and
2. full enterprise microservices with one database per service.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List
from urllib.parse import quote_plus

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _list(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _mysql_url(db_name: str) -> str:
    driver = os.getenv("DB_DRIVER", "mysql+pymysql")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = _int("DB_PORT", 3306)
    user = quote_plus(os.getenv("DB_USER", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    return f"{driver}://{user}:{password}@{host}:{port}/{db_name}"


@dataclass(frozen=True)
class EnterpriseSettings:
    enterprise_microservices_enabled: bool
    app_environment: str
    frontend_origins: List[str]
    frontend_base_url: str
    service_replicas: int
    service_instance_name: str
    service_auth_secret: str
    service_auth_algorithm: str
    service_token_expire_minutes: int
    event_bus_enabled: bool
    rabbitmq_url: str
    otel_enabled: bool
    otel_service_namespace: str
    otel_exporter_otlp_endpoint: str
    database_echo: bool
    auto_create_db: bool
    seed_demo_data: bool
    db_pool_size: int
    db_max_overflow: int
    db_pool_timeout: int
    db_pool_recycle: int
    db_connect_timeout: int
    gzip_minimum_size: int
    threadpool_tokens: int
    product_cache_max_age_seconds: int
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    email_token_expire_minutes: int
    password_reset_token_expire_minutes: int
    auth_database_url: str
    order_database_url: str
    inventory_database_url: str
    notification_database_url: str


@lru_cache
def get_enterprise_settings() -> EnterpriseSettings:
    return EnterpriseSettings(
        enterprise_microservices_enabled=_bool("ENTERPRISE_MICROSERVICES_ENABLED", True),
        app_environment=os.getenv("APP_ENV", "development"),
        frontend_origins=_list(
            "FRONTEND_ORIGINS",
            "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
        ),
        frontend_base_url=os.getenv("FRONTEND_BASE_URL", "http://localhost:5173"),
        service_replicas=_int("SERVICE_REPLICAS", 3),
        service_instance_name=os.getenv("SERVICE_INSTANCE_NAME", "local-dev"),
        service_auth_secret=os.getenv(
            "SERVICE_AUTH_SECRET",
            "change-this-service-to-service-secret-before-production-use",
        ),
        service_auth_algorithm=os.getenv("SERVICE_AUTH_ALGORITHM", "HS256"),
        service_token_expire_minutes=_int("SERVICE_TOKEN_EXPIRE_MINUTES", 10),
        event_bus_enabled=_bool("EVENT_BUS_ENABLED", True),
        rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/%2F"),
        otel_enabled=_bool("OTEL_ENABLED", False),
        otel_service_namespace=os.getenv("OTEL_SERVICE_NAMESPACE", "finmark"),
        otel_exporter_otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317"),
        database_echo=_bool("DATABASE_ECHO", False),
        auto_create_db=_bool("AUTO_CREATE_DB", True),
        seed_demo_data=_bool("SEED_DEMO_DATA", True),
        db_pool_size=_int("DB_POOL_SIZE", 10),
        db_max_overflow=_int("DB_MAX_OVERFLOW", 20),
        db_pool_timeout=_int("DB_POOL_TIMEOUT", 30),
        db_pool_recycle=_int("DB_POOL_RECYCLE", 1800),
        db_connect_timeout=_int("DB_CONNECT_TIMEOUT", 10),
        gzip_minimum_size=_int("GZIP_MINIMUM_SIZE", 1000),
        threadpool_tokens=_int("THREADPOOL_TOKENS", 100),
        product_cache_max_age_seconds=_int("PRODUCT_CACHE_MAX_AGE_SECONDS", 60),
        secret_key=os.getenv("SECRET_KEY", "change-this-development-secret-key-before-production-use"),
        algorithm=os.getenv("ALGORITHM", "HS256"),
        access_token_expire_minutes=_int("ACCESS_TOKEN_EXPIRE_MINUTES", 15),
        refresh_token_expire_days=_int("REFRESH_TOKEN_EXPIRE_DAYS", 7),
        email_token_expire_minutes=_int("EMAIL_TOKEN_EXPIRE_MINUTES", 60),
        password_reset_token_expire_minutes=_int("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 15),
        auth_database_url=os.getenv("AUTH_DATABASE_URL") or _mysql_url("finmark_auth_db"),
        order_database_url=os.getenv("ORDER_DATABASE_URL") or _mysql_url("finmark_order_db"),
        inventory_database_url=os.getenv("INVENTORY_DATABASE_URL") or _mysql_url("finmark_inventory_db"),
        notification_database_url=os.getenv("NOTIFICATION_DATABASE_URL") or _mysql_url("finmark_notification_db"),
    )


enterprise_settings = get_enterprise_settings()
