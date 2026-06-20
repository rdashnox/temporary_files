from fastapi import HTTPException, status

from ..constants.products import PRODUCTS
from ..schemas.shop import Product


DEFAULT_LOW_STOCK_THRESHOLD = 12


def list_products(
    category: str | None = None,
    search: str | None = None,
    low_stock_only: bool = False,
) -> list[Product]:
    """Return catalog products with optional filters for inventory views."""
    products = PRODUCTS

    if category:
        normalized_category = category.strip().lower()
        products = [product for product in products if product.category.lower() == normalized_category]

    if search:
        term = search.strip().lower()
        products = [
            product
            for product in products
            if term in product.name.lower()
            or term in product.category.lower()
            or term in product.description.lower()
        ]

    if low_stock_only:
        products = [product for product in products if product.stock <= DEFAULT_LOW_STOCK_THRESHOLD]

    return products


def get_product(product_id: int) -> Product | None:
    return next((product for product in PRODUCTS if product.id == product_id), None)


def require_product(product_id: int) -> Product:
    product = get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} was not found.",
        )
    return product


def assert_available(product_id: int, quantity: int) -> Product:
    """Validate a product exists and has enough stock for an order request."""
    product = require_product(product_id)
    if quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.stock} item(s) available for {product.name}.",
        )
    return product


def list_low_stock_products(threshold: int = DEFAULT_LOW_STOCK_THRESHOLD) -> list[Product]:
    return [product for product in PRODUCTS if product.stock <= threshold]


def stock_snapshot(threshold: int = DEFAULT_LOW_STOCK_THRESHOLD) -> dict:
    """Small read model for dashboards and notification rules."""
    low_stock_products = list_low_stock_products(threshold)
    return {
        "total_products": len(PRODUCTS),
        "low_stock_count": len(low_stock_products),
        "low_stock_threshold": threshold,
        "low_stock_products": [product.model_dump() for product in low_stock_products],
    }
