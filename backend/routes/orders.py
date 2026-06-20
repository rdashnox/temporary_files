from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, require_permission
from ..schemas.database_entities import OrderCreate, OrderUpdate
from ..schemas.shop import CheckoutRequest, CheckoutResponse
from ..services import order_service

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
    db: Session = Depends(get_db),
):
    """Checkout entry point for the Order service with retry-safe idempotency."""
    return order_service.checkout(db, checkout_request, current_user, idempotency_key=idempotency_key)


@router.get("")
def list_orders(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.read")
    return order_service.list_orders(db, **page)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(
    order_create: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.manage")
    return order_service.create_order(db, order_create, current_user)


@router.get("/{order_id}")
def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.read")
    return order_service.get_order(db, order_id)


@router.put("/{order_id}")
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.manage")
    return order_service.update_order(db, order_id, order_update, current_user)


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.manage")
    return order_service.delete_order(db, order_id, current_user)
