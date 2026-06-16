from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.engine import make_url

from backend.core.config import settings


def _safe_database_url() -> str:
    try:
        return str(make_url(settings.resolved_database_url).render_as_string(hide_password=True))
    except Exception:
        return "<invalid database url>"


def main() -> None:
    print(f"Testing database URL: {_safe_database_url()}")

    try:
        engine = create_engine(settings.resolved_database_url, pool_pre_ping=True, future=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful.")
    except OperationalError as exc:
        print("Database connection failed.")
        print("Most common fix: update DB_USER and DB_PASSWORD in your project-level .env file.")
        print("Example separated .env values:")
        print("DB_HOST=127.0.0.1")
        print("DB_PORT=3306")
        print("DB_NAME=finmark_db")
        print("DB_USER=root")
        print("DB_PASSWORD=your_real_mysql_password")
        print("Alternative: run backend/scripts/fix_mysql_access_denied.sql and use finmark_app.")
        print(f"Original error: {exc}")
        raise SystemExit(1) from exc
    except SQLAlchemyError as exc:
        print("Database connection failed with a SQLAlchemy error.")
        print(f"Original error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
