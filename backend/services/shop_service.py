"""Legacy Shop facade.

The original project exposed products and checkout through /api/v1/shop.  The
service-oriented refactor now owns those operations in InventoryService and
OrderService.  This module remains as a compatibility facade so old frontend
calls and tests continue to work while new code uses /inventory and /orders.
"""

from sqlalchemy.orm import Session

from ..schemas.shop import CheckoutRequest, CheckoutResponse, Product
from . import inventory_service, order_service


def list_products() -> list[Product]:
    return inventory_service.list_products()


def find_product(product_id: int) -> Product | None:
    return inventory_service.get_product(product_id)


def checkout(
    db: Session,
    checkout_request: CheckoutRequest,
    current_user: dict,
    idempotency_key: str | None = None,
) -> CheckoutResponse:
    return order_service.checkout(db, checkout_request, current_user, idempotency_key=idempotency_key)
