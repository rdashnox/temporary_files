"""Initialize separated enterprise databases for local/demo deployment.

Production should use Alembic migration commands documented in
ENTERPRISE_MICROSERVICES_FULL_REPORT.md.
"""

from __future__ import annotations

from backend.enterprise.databases import (
    AuthSessionLocal,
    InventorySessionLocal,
    NotificationSessionLocal,
    OrderSessionLocal,
    init_enterprise_databases,
    session_scope,
    service_database_urls,
)
from backend.enterprise.services.auth_enterprise_service import seed_auth_database
from backend.enterprise.services.inventory_enterprise_service import seed_inventory_database
from backend.enterprise.services.notification_enterprise_service import seed_notification_database


def main() -> None:
    print("Initializing enterprise databases:")
    for service, url in service_database_urls().items():
        print(f"  - {service}: {url}")
    init_enterprise_databases()
    with session_scope(AuthSessionLocal) as db:
        seed_auth_database(db)
    with session_scope(InventorySessionLocal) as db:
        seed_inventory_database(db)
    with session_scope(NotificationSessionLocal) as db:
        seed_notification_database(db)
    # Order DB has no required seed rows.
    with session_scope(OrderSessionLocal):
        pass
    print("Enterprise databases are ready.")
    print("Demo admin account: admin@example.com / Admin@12345")


if __name__ == "__main__":
    main()
