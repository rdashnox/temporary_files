"""Publish pending outbox events from Order and Inventory databases."""

from __future__ import annotations

import json

from sqlalchemy import select

from backend.enterprise.databases import InventorySessionLocal, OrderSessionLocal, session_scope
from backend.enterprise.events import IntegrationEvent, event_publisher
from backend.enterprise.models import InventoryOutboxEvent, OrderOutboxEvent, OutboxStatus, utc_now


def _publish_rows(factory, model, service_name: str) -> int:
    count = 0
    with session_scope(factory) as db:
        rows = db.scalars(select(model).where(model.status == OutboxStatus.PENDING).limit(100)).all()
        for row in rows:
            payload = json.loads(row.payload_json)
            event = IntegrationEvent(
                event_type=payload["event_type"],
                aggregate_type=payload["aggregate_type"],
                aggregate_id=payload["aggregate_id"],
                payload=payload["payload"],
                event_id=payload["event_id"],
                occurred_at=payload.get("occurred_at", ""),
            )
            row.attempts += 1
            if event_publisher.publish(event):
                row.status = OutboxStatus.PUBLISHED
                row.published_at = utc_now()
                count += 1
        print(f"{service_name}: published {count} event(s).")
    return count


def main() -> None:
    _publish_rows(OrderSessionLocal, OrderOutboxEvent, "order")
    _publish_rows(InventorySessionLocal, InventoryOutboxEvent, "inventory")


if __name__ == "__main__":
    main()
