"""Seed the four dedicated enterprise microservice databases.

This script is safe to run repeatedly. It upserts the demo admin account,
roles/permissions, product catalog, sample notification, and optional sample
orders so the four databases have visible data in MySQL Workbench.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.exc import OperationalError, ProgrammingError

from backend.enterprise.databases import (
    AuthSessionLocal,
    InventorySessionLocal,
    NotificationSessionLocal,
    OrderSessionLocal,
    safe_url,
    session_scope,
    service_database_urls,
)
from backend.enterprise.models import (
    AuthAuditLog,
    AuthPermission,
    AuthRole,
    AuthUser,
    InventoryProduct,
    NotificationEntity,
    NotificationInboxEvent,
    OrderEntity,
    OrderItemEntity,
    OrderOutboxEvent,
    OrderStatus,
    OutboxStatus,
    utc_now,
)
from backend.enterprise.services.auth_enterprise_service import seed_auth_database
from backend.enterprise.services.inventory_enterprise_service import seed_inventory_database
from backend.enterprise.services.notification_enterprise_service import seed_notification_database


DEMO_ORDER_NUMBER = "FM-DEMO-0001"
DEMO_ORDER_EVENT_ID = "demo-order-created-0001"


def _count(db, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _print_connection_summary() -> None:
    print("FinMark Enterprise dedicated database seed")
    print("=" * 58)
    for service, url in service_database_urls().items():
        print(f"{service.capitalize():14s}: {url}")
    print("=" * 58)


def _seed_sample_order(include_sample_orders: bool = True) -> None:
    if not include_sample_orders:
        return

    with session_scope(InventorySessionLocal) as inventory_db:
        products = inventory_db.scalars(select(InventoryProduct).order_by(InventoryProduct.id).limit(2)).all()
        if len(products) < 1:
            print("Order DB seed skipped: Inventory DB has no products yet.")
            return
        order_items_seed = []
        for index, product in enumerate(products):
            quantity = 1 if index == 0 else 2
            unit_price = Decimal(str(product.price))
            order_items_seed.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": unit_price * Decimal(quantity),
                }
            )

    subtotal = sum(item["line_total"] for item in order_items_seed)
    discount = Decimal("0.00")
    shipping_fee = Decimal("50.00")
    tax = Decimal("0.00")
    total = subtotal - discount + shipping_fee + tax

    with session_scope(OrderSessionLocal) as order_db:
        existing = order_db.scalar(select(OrderEntity).where(OrderEntity.order_number == DEMO_ORDER_NUMBER))
        if existing is None:
            order = OrderEntity(
                order_number=DEMO_ORDER_NUMBER,
                user_id=1,
                idempotency_key="seed-demo-order-0001",
                customer_name="Demo Customer",
                delivery_address="FinMark Demo Address",
                payment_method="Cash on Delivery",
                status=OrderStatus.PAID.name,
                subtotal=subtotal,
                discount=discount,
                shipping_fee=shipping_fee,
                tax=tax,
                total=total,
            )
            order_db.add(order)
            order_db.flush()
            for item in order_items_seed:
                order_db.add(
                    OrderItemEntity(
                        order_id=order.id,
                        product_id=item["product_id"],
                        product_name=item["product_name"],
                        quantity=item["quantity"],
                        unit_price=item["unit_price"],
                        line_total=item["line_total"],
                    )
                )
            payload = {
                "event_id": DEMO_ORDER_EVENT_ID,
                "event_type": "order.created",
                "aggregate_type": "order",
                "aggregate_id": DEMO_ORDER_NUMBER,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "order_number": DEMO_ORDER_NUMBER,
                    "order_id": order.id,
                    "user_id": 1,
                    "customer_name": "Demo Customer",
                    "total": float(total),
                    "status": "PAID",
                    "source": "seed-script",
                },
            }
            order_db.add(
                OrderOutboxEvent(
                    event_id=DEMO_ORDER_EVENT_ID,
                    event_type="order.created",
                    aggregate_type="order",
                    aggregate_id=DEMO_ORDER_NUMBER,
                    payload_json=json.dumps(payload, default=str),
                    status=OutboxStatus.PUBLISHED,
                    published_at=utc_now(),
                )
            )
        else:
            existing.customer_name = "Demo Customer"
            existing.delivery_address = "FinMark Demo Address"
            existing.status = OrderStatus.PAID.name


def _seed_demo_notification_for_order() -> None:
    with session_scope(NotificationSessionLocal) as notification_db:
        existing = notification_db.scalar(
            select(NotificationEntity).where(
                NotificationEntity.entity_type == "order",
                NotificationEntity.entity_id == DEMO_ORDER_NUMBER,
            )
        )
        if existing is None:
            notification_db.add(
                NotificationEntity(
                    user_id=1,
                    title="Demo order created",
                    message=f"Sample order {DEMO_ORDER_NUMBER} was seeded successfully.",
                    channel="in_app",
                    entity_type="order",
                    entity_id=DEMO_ORDER_NUMBER,
                    is_read=False,
                )
            )
        inbox_exists = notification_db.scalar(
            select(NotificationInboxEvent).where(NotificationInboxEvent.event_id == DEMO_ORDER_EVENT_ID)
        )
        if inbox_exists is None:
            notification_db.add(
                NotificationInboxEvent(
                    event_id=DEMO_ORDER_EVENT_ID,
                    event_type="order.created",
                    payload_json=json.dumps(
                        {
                            "event_id": DEMO_ORDER_EVENT_ID,
                            "event_type": "order.created",
                            "aggregate_type": "order",
                            "aggregate_id": DEMO_ORDER_NUMBER,
                            "payload": {"order_number": DEMO_ORDER_NUMBER, "user_id": 1},
                        }
                    ),
                )
            )


def _reset_demo_data() -> None:
    """Remove only deterministic demo rows created by this script.

    This does not delete product catalog, roles, permissions, or real user data.
    """
    with session_scope(OrderSessionLocal) as order_db:
        demo_order = order_db.scalar(select(OrderEntity).where(OrderEntity.order_number == DEMO_ORDER_NUMBER))
        if demo_order is not None:
            order_db.delete(demo_order)
        order_db.execute(delete(OrderOutboxEvent).where(OrderOutboxEvent.event_id == DEMO_ORDER_EVENT_ID))

    with session_scope(NotificationSessionLocal) as notification_db:
        notification_db.execute(
            delete(NotificationEntity).where(
                NotificationEntity.entity_type == "order",
                NotificationEntity.entity_id == DEMO_ORDER_NUMBER,
            )
        )
        notification_db.execute(delete(NotificationInboxEvent).where(NotificationInboxEvent.event_id == DEMO_ORDER_EVENT_ID))


def _print_counts() -> None:
    print("\nSeed result summary")
    print("-" * 58)
    with session_scope(AuthSessionLocal) as db:
        print("Auth DB:")
        print(f"  auth_users            : {_count(db, AuthUser)}")
        print(f"  auth_roles            : {_count(db, AuthRole)}")
        print(f"  auth_permissions      : {_count(db, AuthPermission)}")
        print(f"  auth_audit_logs       : {_count(db, AuthAuditLog)}")
    with session_scope(InventorySessionLocal) as db:
        print("Inventory DB:")
        print(f"  inventory_products    : {_count(db, InventoryProduct)}")
    with session_scope(OrderSessionLocal) as db:
        print("Order DB:")
        print(f"  order_orders          : {_count(db, OrderEntity)}")
        print(f"  order_items           : {_count(db, OrderItemEntity)}")
        print(f"  order_outbox_events   : {_count(db, OrderOutboxEvent)}")
    with session_scope(NotificationSessionLocal) as db:
        print("Notification DB:")
        print(f"  notification_messages : {_count(db, NotificationEntity)}")
        print(f"  notification_inbox    : {_count(db, NotificationInboxEvent)}")
    print("-" * 58)
    print("Demo login: admin@example.com / Admin@12345")
    print("Open MySQL Workbench, right-click SCHEMAS, then Refresh All.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed FinMark dedicated enterprise databases.")
    parser.add_argument("--reset-demo", action="store_true", help="Delete deterministic sample order/notification rows before seeding.")
    parser.add_argument("--no-sample-orders", action="store_true", help="Seed auth, inventory, and notification only; skip sample order rows.")
    args = parser.parse_args()

    _print_connection_summary()
    try:
        if args.reset_demo:
            print("Resetting deterministic demo order/notification rows...")
            _reset_demo_data()

        with session_scope(AuthSessionLocal) as db:
            seed_auth_database(db)
        with session_scope(InventorySessionLocal) as db:
            seed_inventory_database(db)
        with session_scope(NotificationSessionLocal) as db:
            seed_notification_database(db)

        _seed_sample_order(include_sample_orders=not args.no_sample_orders)
        if not args.no_sample_orders:
            _seed_demo_notification_for_order()

        _print_counts()
    except (OperationalError, ProgrammingError) as exc:
        print("\nDatabase seed failed.")
        print("Most common causes:")
        print("  1. The four databases were not created yet.")
        print("  2. Alembic migrations were not run yet, so tables are missing.")
        print("  3. .env still points to root or to a wrong MySQL password.")
        print("\nRecommended fix:")
        print("  .\\setup-enterprise-mysql.ps1")
        print("  .\\run-enterprise-migrations-mysql.ps1")
        print("  .\\seed-enterprise-mysql.ps1")
        raise exc


if __name__ == "__main__":
    main()
