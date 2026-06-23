from __future__ import annotations

import json
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from ..models import NotificationEntity, NotificationInboxEvent


def iso(value):
    return value.isoformat() if value else None


def notification_to_dict(notification: NotificationEntity) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "title": notification.title,
        "message": notification.message,
        "channel": notification.channel,
        "entity_type": notification.entity_type,
        "entity_id": notification.entity_id,
        "is_read": notification.is_read,
        "created_at": iso(notification.created_at),
    }


def create_notification(
    db: Session,
    *,
    user_id: int | None,
    title: str,
    message: str,
    channel: str = "in_app",
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> NotificationEntity:
    notification = NotificationEntity(
        user_id=user_id,
        title=title,
        message=message,
        channel=channel,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(notification)
    db.flush()
    return notification


def process_integration_event(db: Session, event_message: dict) -> dict:
    event_id = event_message.get("event_id")
    if not event_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="event_id is required")
    existing = db.scalar(select(NotificationInboxEvent).where(NotificationInboxEvent.event_id == event_id))
    if existing:
        return {"message": "Event already processed.", "event_id": event_id, "idempotent": True}

    event_type = event_message.get("event_type")
    payload = event_message.get("payload", {})

    if event_type == "order.created":
        total = Decimal(str(payload.get("total", 0)))
        create_notification(
            db,
            user_id=payload.get("user_id"),
            title="Order created",
            message=f"Order {payload.get('order_number')} for {payload.get('customer_name')} was created with total PHP {float(total):,.2f}.",
            channel="in_app",
            entity_type="orders",
            entity_id=str(payload.get("order_number")),
        )
    elif event_type == "order.updated":
        changed_fields = payload.get("changed_fields") or []
        changed_label = ", ".join(changed_fields) if changed_fields else "order details"
        create_notification(
            db,
            user_id=payload.get("actor_user_id") or payload.get("user_id"),
            title="Order updated",
            message=(
                f"Order {payload.get('order_number')} was updated to {payload.get('status')} "
                f"by {payload.get('actor_username') or 'an administrator'} ({changed_label})."
            ),
            channel="in_app",
            entity_type="orders",
            entity_id=str(payload.get("order_number")),
        )
    elif event_type == "inventory.low_stock":
        create_notification(
            db,
            user_id=None,
            title="Low stock alert",
            message=f"{payload.get('product_name')} is down to {payload.get('stock')} unit(s). Consider restocking.",
            channel="in_app",
            entity_type="inventory",
            entity_id=str(payload.get("product_id")),
        )
    else:
        create_notification(
            db,
            user_id=None,
            title="System event received",
            message=f"Event {event_type} was received by the notification service.",
            channel="in_app",
            entity_type="events",
            entity_id=event_id,
        )

    db.add(
        NotificationInboxEvent(
            event_id=event_id,
            event_type=event_type or "unknown",
            payload_json=json.dumps(event_message, default=str),
        )
    )
    db.commit()
    return {"message": "Event processed.", "event_id": event_id, "event_type": event_type}


def list_notifications(db: Session, current_user: dict, unread_only: bool = False, limit: int = 25, offset: int = 0) -> list[dict]:
    user_id = current_user.get("id")
    statement = select(NotificationEntity).where(or_(NotificationEntity.user_id == user_id, NotificationEntity.user_id.is_(None)))
    if unread_only:
        statement = statement.where(NotificationEntity.is_read.is_(False))
    statement = statement.order_by(desc(NotificationEntity.created_at)).offset(offset).limit(limit)
    return [notification_to_dict(item) for item in db.scalars(statement).all()]


def mark_notification_read(db: Session, notification_id: int, current_user: dict) -> dict:
    user_id = current_user.get("id")
    notification = db.get(NotificationEntity, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification was not found.")
    if notification.user_id not in (None, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot modify this notification.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification_to_dict(notification)


def mark_all_read(db: Session, current_user: dict) -> dict:
    user_id = current_user.get("id")
    notifications = db.scalars(
        select(NotificationEntity).where(
            or_(NotificationEntity.user_id == user_id, NotificationEntity.user_id.is_(None)),
            NotificationEntity.is_read.is_(False),
        )
    ).all()
    for notification in notifications:
        notification.is_read = True
    db.commit()
    return {"message": "Notifications marked as read.", "updated": len(notifications)}


def seed_notification_database(db: Session) -> None:
    exists = db.scalar(select(NotificationEntity).limit(1))
    if exists is None:
        create_notification(
            db,
            user_id=None,
            title="Enterprise notification service ready",
            message="Notification DB is separated and ready to consume events.",
            channel="in_app",
            entity_type="system",
            entity_id="notification-service",
        )
        db.commit()
