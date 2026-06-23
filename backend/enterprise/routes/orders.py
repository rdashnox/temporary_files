from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Path, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ...schemas.database_entities import OrderCreate, OrderUpdate
from ...schemas.shop import CheckoutRequest, CheckoutResponse
from ..databases import get_order_db
from ..security.user_auth import get_current_user, require_permission
from ..models import OrderEntity
from ..services import order_enterprise_service as order_service

router = APIRouter()


def pagination(
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
):
    return {"limit": limit, "offset": offset, "search": search}


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    checkout_request: CheckoutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    return order_service.checkout(db, checkout_request, current_user, idempotency_key=idempotency_key)


def _list_orders_impl(page: dict, current_user: dict, db: Session):
    require_permission(current_user, "orders.read")
    return order_service.list_orders(db, **page)


@router.get("")
@router.get("/", include_in_schema=False)
def list_orders(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    """List orders from the dedicated Order DB.

    Both /api/v1/orders and /api/v1/orders/ are supported because the React
    Admin Dashboard, local Python gateway, and Nginx gateway can normalize
    trailing slashes differently. Supporting both prevents checkout from writing
    to finmark_order_db while Manage Order List accidentally receives 404/empty
    results from a slash mismatch.
    """
    return _list_orders_impl(page, current_user, db)


def _create_order_impl(order_create: OrderCreate, current_user: dict, db: Session):
    require_permission(current_user, "orders.manage")
    return order_service.create_order(db, order_create, current_user)


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_order(
    order_create: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    return _create_order_impl(order_create, current_user, db)


@router.get("/latest")
def latest_orders(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    require_permission(current_user, "orders.read")
    return order_service.list_orders(db, limit=limit, offset=0)


def _order_debug_summary_impl(current_user: dict, db: Session) -> dict:
    require_permission(current_user, "orders.read")
    latest = db.scalar(select(OrderEntity).order_by(desc(OrderEntity.created_at)).limit(1))
    return {
        "status": "ok",
        "service": "order-service",
        "database": "finmark_order_db",
        "table": "order_orders",
        "total_orders": int(db.scalar(select(func.count()).select_from(OrderEntity)) or 0),
        "latest_order": order_service.order_to_dict(latest) if latest else None,
        "supported_list_routes": [
            "/api/v1/orders",
            "/api/v1/orders/",
            "/api/v1/database/orders",
            "/api/v1/database/orders/",
        ],
        "message": "This endpoint confirms whether the Admin Manage Order List can see rows from the dedicated Order DB.",
    }


@router.get("/debug/summary")
@router.get("/debug-summary", include_in_schema=False)
@router.get("/summary/debug", include_in_schema=False)
def order_debug_summary(current_user: dict = Depends(get_current_user), db: Session = Depends(get_order_db)):
    """Return Order Service diagnostics from the dedicated Order DB.

    Multiple aliases are intentionally supported because older local gateways or
    browser caches may still request the old debug path. This keeps the
    diagnostic script from failing with 404 while users are updating ZIP builds.
    """
    return _order_debug_summary_impl(current_user, db)


@router.get("/{order_id}")
def get_order(order_id: int = Path(..., ge=1), current_user: dict = Depends(get_current_user), db: Session = Depends(get_order_db)):
    require_permission(current_user, "orders.read")
    return order_service.get_order(db, order_id)


@router.put("/{order_id}")
@router.patch("/{order_id}", include_in_schema=False)
def update_order(order_id: int = Path(..., ge=1), order_update: OrderUpdate = ..., current_user: dict = Depends(get_current_user), db: Session = Depends(get_order_db)):
    require_permission(current_user, "orders.manage")
    return order_service.update_order(db, order_id, order_update, current_user)


@router.delete("/{order_id}")
def delete_order(order_id: int = Path(..., ge=1), current_user: dict = Depends(get_current_user), db: Session = Depends(get_order_db)):
    require_permission(current_user, "orders.manage")
    return order_service.delete_order(db, order_id, current_user)
