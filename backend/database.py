from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .core.config import settings


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    return settings.resolved_database_url


def is_sqlite_database() -> bool:
    return get_database_url().startswith("sqlite")


def _connect_args() -> dict:
    """Return database-driver specific connect arguments."""
    if is_sqlite_database():
        return {"check_same_thread": False}

    # PyMySQL accepts connect_timeout and keeps failed sockets from hanging
    # worker threads during traffic spikes or database failover.
    return {"connect_timeout": settings.db_connect_timeout}


def _engine_kwargs() -> dict:
    """Build SQLAlchemy engine options for local development and production.

    SQLite ignores production pooling because it is only for tests/local demos.
    MySQL/PostgreSQL deployments use queue pooling so the app can handle many
    active users without opening an uncontrolled number of database connections.
    """
    kwargs = {
        "echo": settings.database_echo,
        "pool_pre_ping": True,
        "future": True,
        "connect_args": _connect_args(),
    }

    if not is_sqlite_database():
        kwargs.update(
            {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
                "pool_timeout": settings.db_pool_timeout,
                "pool_recycle": settings.db_pool_recycle,
            }
        )

    return kwargs


engine = create_engine(get_database_url(), **_engine_kwargs())

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


def _create_index_if_missing(connection, inspector, table_name: str, index_name: str, columns: tuple[str, ...], *, unique: bool = False) -> None:
    """Create a small compatibility index only when it does not yet exist.

    This keeps local MySQL databases upgraded after model changes. SQLAlchemy's
    create_all() is intentionally conservative: it creates missing tables but
    does not alter existing tables or add new columns to them.
    """
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name in existing_indexes:
        return

    unique_sql = "UNIQUE " if unique else ""
    column_sql = ", ".join(columns)
    connection.execute(text(f"CREATE {unique_sql}INDEX {index_name} ON {table_name} ({column_sql})"))


def _run_development_schema_upgrades() -> None:
    """Apply safe, idempotent schema upgrades for local/demo databases.

    This function exists because the project is being run directly through
    Uvicorn for school/local development. It prevents startup crashes when a
    user already has an older MySQL database and the code now expects a newer
    nullable column or index.

    For production, keep AUTO_CREATE_DB=false and run the SQL migration under
    backend/scripts/enterprise_scale_migration.sql or a proper Alembic migration.
    """
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        if "orders" in table_names:
            order_columns = {column["name"] for column in inspector.get_columns("orders")}
            if "idempotency_key" not in order_columns:
                connection.execute(text("ALTER TABLE orders ADD COLUMN idempotency_key VARCHAR(120) NULL"))

            # Refresh inspector after ALTER TABLE so following checks use the latest schema.
            inspector = inspect(engine)
            _create_index_if_missing(
                connection,
                inspector,
                "orders",
                "ix_orders_idempotency_key",
                ("idempotency_key",),
                unique=True,
            )
            _create_index_if_missing(
                connection,
                inspector,
                "orders",
                "ix_orders_status_created_at",
                ("status", "created_at"),
            )
            _create_index_if_missing(
                connection,
                inspector,
                "orders",
                "ix_orders_user_created_at",
                ("user_id", "created_at"),
            )

        if "notifications" in table_names:
            inspector = inspect(engine)
            _create_index_if_missing(
                connection,
                inspector,
                "notifications",
                "ix_notifications_user_created_at",
                ("user_id", "created_at"),
            )


def init_db() -> None:
    """Create tables for local development and automated tests.

    Production should run SQL/Alembic migrations and set AUTO_CREATE_DB=false
    to avoid schema work on every worker startup.
    """
    if not settings.auto_create_db:
        return

    # Import models so SQLAlchemy registers table metadata before create_all.
    from . import models  # noqa: F401

    try:
        Base.metadata.create_all(bind=engine)
        _run_development_schema_upgrades()
    except OperationalError as exc:
        print("\nDatabase startup failed.")
        print(f"Database URL in use: {safe_database_url()}")
        print("Most likely cause: MySQL rejected the username/password, the database user has no access,")
        print("or the local schema needs an ALTER permission for the startup compatibility upgrade.")
        print("Check your project-level .env file:")
        print("  DB_HOST=127.0.0.1")
        print("  DB_PORT=3306")
        print("  DB_NAME=finmark_db")
        print("  DB_USER=root")
        print("  DB_PASSWORD=your_real_mysql_password")
        print("Manual fallback: run backend/scripts/enterprise_scale_migration.sql in MySQL Workbench.\n")
        raise exc
    except SQLAlchemyError as exc:
        print("\nDatabase schema startup failed.")
        print(f"Database URL in use: {safe_database_url()}")
        print("Manual fallback: run backend/scripts/enterprise_scale_migration.sql in MySQL Workbench.\n")
        raise exc
