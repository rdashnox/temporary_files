from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..services import notification_service

router = APIRouter()


@router.get("")
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return in-app notifications for the authenticated user."""
    return notification_service.list_notifications(
        db,
        current_user,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark one notification as read."""
    return notification_service.mark_notification_read(db, notification_id, current_user)


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
def mark_all_read(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all user-visible notifications as read."""
    return notification_service.mark_all_read(db, current_user)
