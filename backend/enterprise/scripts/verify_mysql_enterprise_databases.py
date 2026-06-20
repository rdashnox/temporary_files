"""Verify FinMark enterprise MySQL databases and tables.

Run from the project root:
    python -m backend.enterprise.scripts.verify_mysql_enterprise_databases
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.enterprise.databases import (
    auth_engine,
    inventory_engine,
    notification_engine,
    order_engine,
    safe_url,
)

SERVICE_ENGINES = {
    "Auth DB": auth_engine,
    "Order DB": order_engine,
    "Inventory DB": inventory_engine,
    "Notification DB": notification_engine,
}


def main() -> None:
    print("FinMark Enterprise MySQL database verification")
    print("=" * 56)
    all_ready = True

    for label, engine in SERVICE_ENGINES.items():
        print(f"\n{label}")
        print(f"  URL: {safe_url(str(engine.url))}")
        try:
            with engine.connect() as connection:
                current_db = connection.execute(text("SELECT DATABASE()")).scalar()
                tables = [row[0] for row in connection.exec_driver_sql("SHOW TABLES").fetchall()]
        except SQLAlchemyError as exc:
            all_ready = False
            print("  Status: NOT READY")
            print(f"  Error: {exc}")
            continue

        print("  Status: READY")
        print(f"  Connected schema: {current_db}")
        print(f"  Table count: {len(tables)}")
        if tables:
            for table_name in tables:
                print(f"    - {table_name}")
        else:
            all_ready = False
            print("  Warning: No tables found. Run .\\run-enterprise-migrations-mysql.ps1")

    print("\n" + "=" * 56)
    if all_ready:
        print("All four dedicated enterprise databases are reachable and have tables.")
        print("Open MySQL Workbench, then refresh the SCHEMAS panel to view them.")
    else:
        print("One or more databases need attention. Review the messages above.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
