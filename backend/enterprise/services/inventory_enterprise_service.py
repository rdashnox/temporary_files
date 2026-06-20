from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ...constants.products import PRODUCTS
from ...schemas.shop import Product
from ..events import IntegrationEvent, event_publisher
from ..models import InventoryOutboxEvent, InventoryProduct, OutboxStatus, utc_now

DEFAULT_LOW_STOCK_THRESHOLD = 12


def product_to_api(product: InventoryProduct) -> Product:
    return Product(
        id=product.id,
        name=product.name,
        category=product.category,
        description=product.description,
        price=float(product.price),
        compare_at_price=float(product.compare_at_price) if product.compare_at_price is not None else None,
        stock=product.stock_quantity,
        rating=float(product.rating),
        badge=product.badge,
        image=product.image,
    )


def list_products(db: Session, category: str | None = None, search: str | None = None, low_stock_only: bool = False) -> list[Product]:
    statement = select(InventoryProduct).where(InventoryProduct.is_active.is_(True)).order_by(InventoryProduct.id)
    if category:
        statement = statement.where(InventoryProduct.category.ilike(category.strip()))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                InventoryProduct.name.ilike(term),
                InventoryProduct.category.ilike(term),
                InventoryProduct.description.ilike(term),
                InventoryProduct.sku.ilike(term),
            )
        )
    if low_stock_only:
        statement = statement.where(InventoryProduct.stock_quantity <= DEFAULT_LOW_STOCK_THRESHOLD)
    return [product_to_api(item) for item in db.scalars(statement).all()]


def get_product(db: Session, product_id: int) -> Product | None:
    product = db.get(InventoryProduct, product_id)
    if product is None or not product.is_active:
        return None
    return product_to_api(product)


def require_product(db: Session, product_id: int) -> Product:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {product_id} was not found.")
    return product


def assert_available(db: Session, product_id: int, quantity: int) -> Product:
    product = require_product(db, product_id)
    if quantity > product.stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {product.stock} item(s) available for {product.name}.")
    return product


def reserve_stock(db: Session, items: list[dict]) -> dict:
    """Reduce stock in the Inventory DB after checkout.

    This endpoint is intended for internal service calls from the Order service.
    It is protected by X-Service-Token in the route layer.
    """
    updated: list[dict] = []
    for item in items:
        product_id = int(item["product_id"])
        quantity = int(item["quantity"])
        product = db.get(InventoryProduct, product_id)
        if product is None or not product.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {product_id} was not found.")
        if product.stock_quantity < quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {product.stock_quantity} item(s) available for {product.name}.")
        product.stock_quantity -= quantity
        updated.append({"product_id": product.id, "name": product.name, "remaining_stock": product.stock_quantity})
        if product.stock_quantity <= DEFAULT_LOW_STOCK_THRESHOLD:
            create_inventory_event(
                db,
                "inventory.low_stock",
                "inventory_product",
                str(product.id),
                {"product_id": product.id, "product_name": product.name, "stock": product.stock_quantity},
            )
    db.commit()
    return {"message": "Stock reserved successfully.", "items": updated}


def stock_snapshot(db: Session, threshold: int = DEFAULT_LOW_STOCK_THRESHOLD) -> dict:
    products = db.scalars(select(InventoryProduct).where(InventoryProduct.is_active.is_(True))).all()
    low_stock = [item for item in products if item.stock_quantity <= threshold]
    return {
        "total_products": len(products),
        "low_stock_count": len(low_stock),
        "low_stock_threshold": threshold,
        "low_stock_products": [product_to_api(item).model_dump() for item in low_stock],
    }


def create_inventory_event(db: Session, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> None:
    event = IntegrationEvent(event_type=event_type, aggregate_type=aggregate_type, aggregate_id=aggregate_id, payload=payload)
    message = event.to_message()
    outbox = InventoryOutboxEvent(
        event_id=message["event_id"],
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload_json=__import__("json").dumps(message, default=str),
        status=OutboxStatus.PENDING,
    )
    db.add(outbox)
    published = event_publisher.publish(event)
    if published:
        outbox.status = OutboxStatus.PUBLISHED
        outbox.published_at = utc_now()


def seed_inventory_database(db: Session) -> None:
    for product in PRODUCTS:
        existing = db.get(InventoryProduct, product.id)
        if existing is None:
            existing = InventoryProduct(id=product.id, sku=f"FM-{product.id:04d}")
            db.add(existing)
        existing.name = product.name
        existing.category = product.category
        existing.description = product.description
        existing.price = Decimal(str(product.price))
        existing.compare_at_price = Decimal(str(product.compare_at_price)) if product.compare_at_price is not None else None
        existing.stock_quantity = product.stock
        existing.rating = Decimal(str(product.rating))
        existing.badge = product.badge
        existing.image = product.image
        existing.is_active = True
    db.commit()
