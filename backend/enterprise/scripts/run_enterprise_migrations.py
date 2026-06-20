"""Run Alembic migrations for all enterprise service databases.

Usage examples:
    python -m backend.enterprise.scripts.run_enterprise_migrations
    python -m backend.enterprise.scripts.run_enterprise_migrations --local
    python -m backend.enterprise.scripts.run_enterprise_migrations --service auth

Use --local when you are testing the enterprise microservice system without
Docker/MySQL. It migrates four SQLite files under data/enterprise-local.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from sqlalchemy.exc import OperationalError
except Exception:  # pragma: no cover - sqlalchemy is installed in normal runtime
    OperationalError = None

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_ROOT = PROJECT_ROOT / "backend" / "enterprise" / "migrations"
SERVICES = ("auth", "order", "inventory", "notification")


def _sqlite_url(path: Path) -> str:
    """Return a SQLAlchemy SQLite URL that works on Windows and Linux."""
    return f"sqlite:///{path.resolve().as_posix()}"


def _enable_local_sqlite_mode() -> None:
    """Point all enterprise service databases to local SQLite files."""
    data_dir = PROJECT_ROOT / "data" / "enterprise-local"
    data_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("ENTERPRISE_MICROSERVICES_ENABLED", "true")
    os.environ.setdefault("DEPLOYMENT_MODE", "local-enterprise-microservices")
    os.environ.setdefault("AUTO_CREATE_DB", "false")
    os.environ.setdefault("SEED_DEMO_DATA", "false")
    os.environ.setdefault("EVENT_BUS_ENABLED", "false")
    os.environ.setdefault("OTEL_ENABLED", "false")
    os.environ["AUTH_DATABASE_URL"] = _sqlite_url(data_dir / "auth.db")
    os.environ["ORDER_DATABASE_URL"] = _sqlite_url(data_dir / "order.db")
    os.environ["INVENTORY_DATABASE_URL"] = _sqlite_url(data_dir / "inventory.db")
    os.environ["NOTIFICATION_DATABASE_URL"] = _sqlite_url(data_dir / "notification.db")


def _load_alembic():
    try:
        from alembic import command
        from alembic.config import Config
        return command, Config
    except ModuleNotFoundError as exc:
        if exc.name == "alembic":
            print("\nERROR: Alembic is not installed in the active Python environment.\n", file=sys.stderr)
            print("Fix it by running these commands from the project root:\n", file=sys.stderr)
            print(r"  .\.venv\Scripts\python.exe -m pip install --upgrade pip", file=sys.stderr)
            print(r"  .\.venv\Scripts\python.exe -m pip install -r requirements.txt", file=sys.stderr)
            print("\nThen run the migration command again:\n", file=sys.stderr)
            print(r"  .\.venv\Scripts\python.exe -m backend.enterprise.scripts.run_enterprise_migrations --local", file=sys.stderr)
            print("\nFor production/MySQL, remove --local and make sure your four database URLs are set.\n", file=sys.stderr)
            raise SystemExit(1) from exc
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run enterprise Alembic migrations.")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local SQLite databases in data/enterprise-local instead of MySQL URLs.",
    )
    parser.add_argument(
        "--service",
        choices=("all", *SERVICES),
        default="all",
        help="Run migrations for one service or all services.",
    )
    parser.add_argument(
        "--revision",
        default="head",
        help="Alembic target revision. Default: head.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.local:
        _enable_local_sqlite_mode()

    command, Config = _load_alembic()
    selected_services = SERVICES if args.service == "all" else (args.service,)

    for service in selected_services:
        config_path = MIGRATION_ROOT / service / "alembic.ini"
        cfg = Config(str(config_path))
        cfg.set_main_option("script_location", str(MIGRATION_ROOT / service))
        print(f"Running Alembic migrations for {service} database to revision {args.revision}...")
        try:
            command.upgrade(cfg, args.revision)
        except ValueError as exc:
            if "invalid interpolation syntax" in str(exc):
                print(f"\nMigration failed for {service} database because the database URL contains an unescaped percent sign (%).", file=sys.stderr)
                print("This commonly happens when a password contains @ and is URL-encoded as %40.", file=sys.stderr)
                print("The migration env.py files must escape % as %% before calling Alembic Config.set_main_option().", file=sys.stderr)
                print("Use the patched project ZIP or update backend/enterprise/migrations/*/env.py with _escape_configparser_percent().\n", file=sys.stderr)
            else:
                print(f"\nMigration failed for {service} database due to a configuration value error.", file=sys.stderr)
            raise
        except Exception as exc:
            print(f"\nMigration failed for {service} database.", file=sys.stderr)
            message = str(exc)
            if "Can't connect to MySQL server" in message or "ConnectionRefusedError" in message or "WinError 10061" in message:
                print("Cause: MySQL is not reachable at the host/port in your .env, usually 127.0.0.1:3306.", file=sys.stderr)
                print("Fix: start MySQL Server/MySQL80/XAMPP/Laragon, or update .env to the correct MySQL port.", file=sys.stderr)
                print(r"Run: .\diagnose-mysql-connection.ps1", file=sys.stderr)
                print(r"Then: .\setup-enterprise-mysql.ps1", file=sys.stderr)
                print(r"Then: .\run-enterprise-migrations-mysql.ps1", file=sys.stderr)
            elif "Access denied" in message:
                print("Cause: MySQL accepted the connection but rejected the username/password.", file=sys.stderr)
                print(r"Run: .\setup-enterprise-mysql.ps1 and confirm the MySQL admin password.", file=sys.stderr)
            elif "Unknown database" in message:
                print("Cause: The four databases have not been created yet.", file=sys.stderr)
                print(r"Run: .\setup-enterprise-mysql.ps1", file=sys.stderr)
            print("Common fixes:", file=sys.stderr)
            print("  1. Install dependencies: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt", file=sys.stderr)
            print("  2. For no-Docker local testing, use: --local", file=sys.stderr)
            print("  3. For MySQL, confirm AUTH_DATABASE_URL, ORDER_DATABASE_URL, INVENTORY_DATABASE_URL, and NOTIFICATION_DATABASE_URL are correct.", file=sys.stderr)
            print("  4. If your password contains @, keep it URL-encoded as %40 in .env; patched Alembic env.py files will handle it safely.", file=sys.stderr)
            print("  5. Make sure the database server is running and the database user has CREATE/ALTER permissions.\n", file=sys.stderr)
            raise


    print("All selected enterprise service database migrations are complete.")


if __name__ == "__main__":
    main()
