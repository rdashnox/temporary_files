from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..databases import get_notification_db
from ..security.service_auth import require_service_token
from ..security.user_auth import get_current_user
from ..services import notification_enterprise_service as notification_service

router = APIRouter()


@router.get("")
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_notification_db),
):
    return notification_service.list_notifications(db, current_user, unread_only=unread_only, limit=limit, offset=offset)


@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_notification_db)):
    return notification_service.mark_notification_read(db, notification_id, current_user)


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
def mark_all_read(current_user: dict = Depends(get_current_user), db: Session = Depends(get_notification_db)):
    return notification_service.mark_all_read(db, current_user)


@router.post("/internal/events")
def internal_process_event(event_message: dict, service: dict = Depends(require_service_token), db: Session = Depends(get_notification_db)):
    return notification_service.process_integration_event(db, event_message)
