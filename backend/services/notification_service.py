from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from ..models import Notification
from ..schemas.notification import NotificationCreate
from .common import iso


def notification_to_dict(notification: Notification) -> dict:
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


def create_notification(db: Session, notification_create: NotificationCreate) -> Notification:
    """Create an in-app notification without committing the caller's transaction."""
    notification = Notification(**notification_create.model_dump())
    db.add(notification)
    db.flush()
    return notification


def notify_order_created(
    db: Session,
    *,
    order_number: str,
    customer_name: str,
    total: Decimal,
    user_id: int | None = None,
) -> Notification:
    return create_notification(
        db,
        NotificationCreate(
            user_id=user_id,
            title="Order created",
            message=f"Order {order_number} for {customer_name} was created with total PHP {float(total):,.2f}.",
            channel="in_app",
            entity_type="orders",
            entity_id=order_number,
        ),
    )


def notify_low_stock(db: Session, *, product_name: str, stock: int, user_id: int | None = None) -> Notification:
    return create_notification(
        db,
        NotificationCreate(
            user_id=user_id,
            title="Low stock alert",
            message=f"{product_name} is down to {stock} unit(s). Consider restocking.",
            channel="in_app",
            entity_type="inventory",
            entity_id=product_name,
        ),
    )


def list_notifications(
    db: Session,
    current_user: dict,
    *,
    unread_only: bool = False,
    limit: int = 25,
    offset: int = 0,
) -> list[dict]:
    """Return user-specific and global notifications for the authenticated account."""
    user_id = current_user.get("id")
    statement = select(Notification).where(
        or_(Notification.user_id == user_id, Notification.user_id.is_(None))
    )
    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))
    statement = statement.order_by(desc(Notification.created_at)).offset(offset).limit(limit)
    return [notification_to_dict(item) for item in db.scalars(statement).all()]


def mark_notification_read(db: Session, notification_id: int, current_user: dict) -> dict:
    user_id = current_user.get("id")
    notification = db.get(Notification, notification_id)
    if notification is None:
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
        select(Notification).where(
            or_(Notification.user_id == user_id, Notification.user_id.is_(None)),
            Notification.is_read.is_(False),
        )
    ).all()
    for notification in notifications:
        notification.is_read = True
    db.commit()
    return {"message": "Notifications marked as read.", "updated": len(notifications)}
