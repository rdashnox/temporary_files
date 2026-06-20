from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ...schemas.shop import Product
from ..config import enterprise_settings
from ..databases import get_inventory_db
from ..security.service_auth import require_service_token
from ..security.user_auth import get_current_user, require_permission
from ..services import inventory_enterprise_service as inventory_service

router = APIRouter()


class ReserveStockItem(BaseModel):
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)


class ReserveStockRequest(BaseModel):
    items: list[ReserveStockItem] = Field(..., min_length=1)


@router.get("/products", response_model=list[Product])
def list_products(
    response: Response,
    category: str | None = Query(default=None, max_length=80),
    search: str | None = Query(default=None, max_length=120),
    low_stock_only: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_inventory_db),
):
    response.headers["Cache-Control"] = f"private, max-age={enterprise_settings.product_cache_max_age_seconds}"
    return inventory_service.list_products(db, category=category, search=search, low_stock_only=low_stock_only)


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_inventory_db)):
    return inventory_service.require_product(db, product_id)


@router.get("/stock/summary")
def stock_summary(
    threshold: int = Query(default=12, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_inventory_db),
):
    require_permission(current_user, "inventory.read")
    return inventory_service.stock_snapshot(db, threshold)


@router.get("/internal/products/{product_id}", response_model=Product)
def internal_get_product(
    product_id: int,
    quantity: int = Query(default=1, ge=1),
    service: dict = Depends(require_service_token),
    db: Session = Depends(get_inventory_db),
):
    return inventory_service.assert_available(db, product_id, quantity)


@router.post("/internal/reserve-stock")
def internal_reserve_stock(
    request: ReserveStockRequest,
    service: dict = Depends(require_service_token),
    db: Session = Depends(get_inventory_db),
):
    return inventory_service.reserve_stock(db, [item.model_dump() for item in request.items])
