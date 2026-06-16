from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .core.config import settings


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    return settings.resolved_database_url


def is_sqlite_database() -> bool:
    return get_database_url().startswith("sqlite")


def _connect_args() -> dict:
    """SQLite needs a special thread flag; MySQL does not."""
    if is_sqlite_database():
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    get_database_url(),
    echo=settings.database_echo,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args(),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides one database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Small helper for scripts and startup tasks."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def safe_database_url() -> str:
    """Return the active database URL without exposing the password."""
    try:
        return str(make_url(get_database_url()).render_as_string(hide_password=True))
    except Exception:
        return "<invalid database url>"


def init_db() -> None:
    """Create tables for local development.

    For production, replace this create_all approach with Alembic migrations.
    """
    # Import models so SQLAlchemy registers table metadata before create_all.
    from . import models  # noqa: F401

    try:
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        print("\nDatabase startup failed.")
        print(f"Database URL in use: {safe_database_url()}")
        print("Most likely cause: MySQL rejected the username/password or the database user has no access.")
        print("Check your project-level .env file:")
        print("  DB_HOST=127.0.0.1")
        print("  DB_PORT=3306")
        print("  DB_NAME=finmark_db")
        print("  DB_USER=root")
        print("  DB_PASSWORD=your_real_mysql_password")
        print("Alternative: use a dedicated app user from backend/scripts/fix_mysql_access_denied.sql\n")
        raise exc
