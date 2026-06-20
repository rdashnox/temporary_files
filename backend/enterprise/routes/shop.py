from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from ...schemas.shop import CheckoutRequest, CheckoutResponse, Product
from ..config import enterprise_settings
from ..databases import get_inventory_db, get_order_db
from ..security.user_auth import get_current_user
from ..services import inventory_enterprise_service, order_enterprise_service

router = APIRouter()


@router.get("/products", response_model=list[Product])
def list_products(response: Response, current_user: dict = Depends(get_current_user), db: Session = Depends(get_inventory_db)):
    response.headers["Cache-Control"] = f"private, max-age={enterprise_settings.product_cache_max_age_seconds}"
    return inventory_enterprise_service.list_products(db)


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    checkout_request: CheckoutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    return order_enterprise_service.checkout(db, checkout_request, current_user, idempotency_key=idempotency_key)
