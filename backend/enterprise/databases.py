"""Database engines and session dependencies for separated databases.

The original prototype used one shared database. Enterprise mode uses four
separate SQLAlchemy engines, four independent DeclarativeBase classes, and four
session dependencies. There are intentionally no cross-database foreign keys.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import enterprise_settings


class AuthBase(DeclarativeBase):
    pass


class OrderBase(DeclarativeBase):
    pass


class InventoryBase(DeclarativeBase):
    pass


class NotificationBase(DeclarativeBase):
    pass


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _engine_kwargs(database_url: str) -> dict:
    kwargs = {
        "echo": enterprise_settings.database_echo,
        "pool_pre_ping": True,
        "future": True,
    }
    if _is_sqlite(database_url):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            {
                "connect_args": {"connect_timeout": enterprise_settings.db_connect_timeout},
                "pool_size": enterprise_settings.db_pool_size,
                "max_overflow": enterprise_settings.db_max_overflow,
                "pool_timeout": enterprise_settings.db_pool_timeout,
                "pool_recycle": enterprise_settings.db_pool_recycle,
            }
        )
    return kwargs


def _make_engine(database_url: str) -> Engine:
    return create_engine(database_url, **_engine_kwargs(database_url))


auth_engine = _make_engine(enterprise_settings.auth_database_url)
order_engine = _make_engine(enterprise_settings.order_database_url)
inventory_engine = _make_engine(enterprise_settings.inventory_database_url)
notification_engine = _make_engine(enterprise_settings.notification_database_url)

AuthSessionLocal = sessionmaker(bind=auth_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
OrderSessionLocal = sessionmaker(bind=order_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
InventorySessionLocal = sessionmaker(bind=inventory_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
NotificationSessionLocal = sessionmaker(bind=notification_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def _session_dependency(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    db = factory()
    try:
        yield db
    finally:
        db.close()


def get_auth_db() -> Generator[Session, None, None]:
    yield from _session_dependency(AuthSessionLocal)


def get_order_db() -> Generator[Session, None, None]:
    yield from _session_dependency(OrderSessionLocal)


def get_inventory_db() -> Generator[Session, None, None]:
    yield from _session_dependency(InventorySessionLocal)


def get_notification_db() -> Generator[Session, None, None]:
    yield from _session_dependency(NotificationSessionLocal)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_engine_for_service(service_name: str) -> Engine:
    engines = {
        "auth": auth_engine,
        "order": order_engine,
        "inventory": inventory_engine,
        "notification": notification_engine,
    }
    return engines[service_name]


def safe_url(url: str) -> str:
    try:
        return str(make_url(url).render_as_string(hide_password=True))
    except Exception:
        return "<invalid database url>"


def service_database_urls() -> dict[str, str]:
    return {
        "auth": safe_url(enterprise_settings.auth_database_url),
        "order": safe_url(enterprise_settings.order_database_url),
        "inventory": safe_url(enterprise_settings.inventory_database_url),
        "notification": safe_url(enterprise_settings.notification_database_url),
    }


def init_enterprise_databases() -> None:
    """Create tables only for local/demo use.

    Production should run Alembic migrations from backend/enterprise/migrations
    and keep AUTO_CREATE_DB=false.
    """
    from . import models  # noqa: F401

    if not enterprise_settings.auto_create_db:
        return

    AuthBase.metadata.create_all(bind=auth_engine)
    OrderBase.metadata.create_all(bind=order_engine)
    InventoryBase.metadata.create_all(bind=inventory_engine)
    NotificationBase.metadata.create_all(bind=notification_engine)
