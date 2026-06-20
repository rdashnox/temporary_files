from fastapi import APIRouter, Depends, Query, Response

from ..core.config import settings
from ..dependencies.auth import get_current_user
from ..schemas.shop import Product
from ..services import inventory_service

router = APIRouter()


def _set_product_cache_headers(response: Response) -> None:
    # Product catalog reads are high-frequency and mostly static in this
    # version, so short private caching reduces backend load per user session.
    response.headers["Cache-Control"] = f"private, max-age={settings.product_cache_max_age_seconds}"


@router.get("/products", response_model=list[Product])
def list_products(
    response: Response,
    category: str | None = Query(default=None, max_length=80),
    search: str | None = Query(default=None, max_length=120),
    low_stock_only: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
):
    """Product catalog service endpoint used by the storefront and inventory dashboard."""
    _set_product_cache_headers(response)
    return inventory_service.list_products(category=category, search=search, low_stock_only=low_stock_only)


@router.get("/products/{product_id}", response_model=Product)
def get_product(response: Response, product_id: int, current_user: dict = Depends(get_current_user)):
    """Return one catalog item and fail consistently when the item does not exist."""
    _set_product_cache_headers(response)
    return inventory_service.require_product(product_id)


@router.get("/stock/summary")
def get_stock_summary(
    threshold: int = Query(default=12, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """Return inventory summary information for dashboard cards and alert rules."""
    return inventory_service.stock_snapshot(threshold)
