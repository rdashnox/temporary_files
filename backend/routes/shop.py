"""Backward-compatible shop routes.

New service-oriented endpoints are:
- /api/v1/inventory/products
- /api/v1/orders/checkout

These routes are intentionally kept so existing clients do not break.
"""

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..schemas.shop import CheckoutRequest, CheckoutResponse, Product
from ..services import shop_service

router = APIRouter()


@router.get("/products", response_model=list[Product])
def list_products(response: Response, current_user: dict = Depends(get_current_user)):
    response.headers["Cache-Control"] = f"private, max-age={settings.product_cache_max_age_seconds}"
    return shop_service.list_products()


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    checkout_request: CheckoutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return shop_service.checkout(db, checkout_request, current_user, idempotency_key=idempotency_key)
