from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import httpx
from fastapi import HTTPException, status
from sqlalchemy import String, cast, delete, desc, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, noload, selectinload

from ...schemas.database_entities import OrderCreate, OrderItemCreate, OrderUpdate
from ...schemas.shop import CheckoutItem, CheckoutRequest, CheckoutResponse, CheckoutSummary
from ...services.pricing_service import calculate_checkout_summary
from ..databases import InventorySessionLocal, session_scope
from ..events import IntegrationEvent, event_publisher
from ..models import OrderEntity, OrderItemEntity, OrderOutboxEvent, OrderStatus, OutboxStatus, utc_now
from ..security.service_auth import create_service_token
from .inventory_enterprise_service import assert_available as db_assert_available


def iso(value):
    return value.isoformat() if value else None


def money(value) -> float:
    return float(value or 0)


def enum_to_api(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "name"):
        return value.name
    cleaned = str(value).strip()
    if not cleaned:
        return None
    return cleaned.upper()


def status_to_storage(value) -> str:
    """Store order status as uppercase text.

    Earlier demo SQL scripts inserted lowercase values such as ``paid`` and
    ``completed`` while SQLAlchemy Enum columns expected enum names such as
    ``PAID``. That caused unfiltered Admin Order List reads to fail when old
    lowercase rows existed. Keeping the model as a plain string and normalizing
    here makes the service tolerant of both old and new data.
    """
    if value is None:
        return OrderStatus.NEW.name
    if hasattr(value, "name"):
        return value.name
    cleaned = str(value).strip()
    if not cleaned:
        return OrderStatus.NEW.name
    return cleaned.upper()


def enum_from_input(enum_cls, value: str | None, default=None):
    if value is None:
        return default
    cleaned = value.strip()
    if not cleaned:
        return default
    if cleaned.upper() in enum_cls.__members__:
        return enum_cls[cleaned.upper()]
    for member in enum_cls:
        if member.value.lower() == cleaned.lower():
            return member
    allowed = ", ".join(member.name for member in enum_cls)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status '{value}'. Allowed: {allowed}.")


def _normalize_key(header_key: str | None, body_key: str | None) -> str | None:
    key = (header_key or body_key or "").strip()
    return key or None


def order_to_dict(order: OrderEntity) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "delivery_address": order.delivery_address,
        "payment_method": order.payment_method,
        "status": enum_to_api(order.status),
        "subtotal": money(order.subtotal),
        "discount": money(order.discount),
        "shipping_fee": money(order.shipping_fee),
        "tax": money(order.tax),
        "total": money(order.total),
        "created_at": iso(order.created_at),
        "updated_at": iso(order.updated_at),
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": money(item.unit_price),
                "line_total": money(item.line_total),
            }
            for item in order.items
        ],
    }


def _checkout_response_from_order(order: OrderEntity, current_user: dict, message: str = "Checkout successful") -> CheckoutResponse:
    items = [
        CheckoutItem(
            product_id=item.product_id,
            name=item.product_name,
            quantity=item.quantity,
            unit_price=money(item.unit_price),
            line_total=money(item.line_total),
        )
        for item in order.items
    ]
    summary = CheckoutSummary(
        subtotal=money(order.subtotal),
        discount=money(order.discount),
        shipping_fee=money(order.shipping_fee),
        tax=money(order.tax),
        total=money(order.total),
    )
    return CheckoutResponse(
        order_id=order.order_number,
        status=enum_to_api(order.status) or "PAID",
        message=message,
        authenticated_user=current_user.get("username", "unknown"),
        checked_out_at=iso(order.created_at) or datetime.now(timezone.utc).isoformat(),
        items=items,
        summary=summary,
    )


def _get_existing_checkout(db: Session, idempotency_key: str | None, current_user: dict) -> OrderEntity | None:
    if not idempotency_key:
        return None
    return db.scalar(
        select(OrderEntity).where(
            OrderEntity.idempotency_key == idempotency_key,
            OrderEntity.user_id == current_user.get("id"),
        )
    )


def _fetch_product_from_inventory_service(product_id: int, quantity: int) -> dict | None:
    inventory_url = os.getenv("INVENTORY_SERVICE_URL", "").rstrip("/")
    if not inventory_url:
        return None
    token = create_service_token("order-service", audience="finmark-internal")
    try:
        response = httpx.get(
            f"{inventory_url}/api/v1/inventory/internal/products/{product_id}",
            params={"quantity": quantity},
            headers={"X-Service-Token": token},
            timeout=httpx.Timeout(5.0, connect=2.0),
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError:
        return None


def _reserve_stock_in_inventory_service(items: list[dict]) -> None:
    inventory_url = os.getenv("INVENTORY_SERVICE_URL", "").rstrip("/")
    if not inventory_url:
        return
    token = create_service_token("order-service", audience="finmark-internal")
    try:
        response = httpx.post(
            f"{inventory_url}/api/v1/inventory/internal/reserve-stock",
            json={"items": items},
            headers={"X-Service-Token": token},
            timeout=httpx.Timeout(10.0, connect=2.0),
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError:
        # Broker/outbox still records order events. In production, configure
        # INVENTORY_SERVICE_URL and monitor this path.
        return


def _build_checkout_items(checkout_request: CheckoutRequest) -> list[CheckoutItem]:
    items: list[CheckoutItem] = []
    for item in checkout_request.items:
        product = _fetch_product_from_inventory_service(item.product_id, item.quantity)
        if product is None:
            # Local fallback so no-Docker mode works even without internal HTTP config.
            # This still uses the Inventory DB, not the Order DB.
            with session_scope(InventorySessionLocal) as inventory_db:
                product_model = db_assert_available(inventory_db, item.product_id, item.quantity)
                product = product_model.model_dump()
        line_total = round(float(product["price"]) * item.quantity, 2)
        items.append(
            CheckoutItem(
                product_id=item.product_id,
                name=product["name"],
                quantity=item.quantity,
                unit_price=float(product["price"]),
                line_total=line_total,
            )
        )
    return items


def create_order_event(db: Session, order: OrderEntity, current_user: dict) -> None:
    payload = {
        "order_number": order.order_number,
        "order_id": order.id,
        "user_id": current_user.get("id"),
        "customer_name": order.customer_name,
        "total": money(order.total),
        "status": enum_to_api(order.status),
    }
    event = IntegrationEvent("order.created", "order", order.order_number, payload)
    message = event.to_message()
    outbox = OrderOutboxEvent(
        event_id=message["event_id"],
        event_type="order.created",
        aggregate_type="order",
        aggregate_id=order.order_number,
        payload_json=json.dumps(message, default=str),
        status=OutboxStatus.PENDING,
    )
    db.add(outbox)
    published = event_publisher.publish(event)
    if published:
        outbox.status = OutboxStatus.PUBLISHED
        outbox.published_at = utc_now()


def checkout(db: Session, checkout_request: CheckoutRequest, current_user: dict, idempotency_key: str | None = None) -> CheckoutResponse:
    normalized_key = _normalize_key(idempotency_key, checkout_request.idempotency_key)
    existing = _get_existing_checkout(db, normalized_key, current_user)
    if existing:
        return _checkout_response_from_order(existing, current_user, "Checkout request was already processed. Returning the original order.")

    checkout_items = _build_checkout_items(checkout_request)
    summary = calculate_checkout_summary(checkout_items, checkout_request.coupon_code)
    order = OrderEntity(
        order_number=f"FM-{uuid4().hex[:8].upper()}",
        user_id=current_user.get("id"),
        idempotency_key=normalized_key,
        customer_name=checkout_request.customer_name,
        delivery_address=checkout_request.delivery_address,
        payment_method=checkout_request.payment_method,
        status=status_to_storage(OrderStatus.PAID),
        subtotal=Decimal(str(summary.subtotal)),
        discount=Decimal(str(summary.discount)),
        shipping_fee=Decimal(str(summary.shipping_fee)),
        tax=Decimal(str(summary.tax)),
        total=Decimal(str(summary.total)),
    )
    db.add(order)
    db.flush()
    for item in checkout_items:
        db.add(
            OrderItemEntity(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.name,
                quantity=item.quantity,
                unit_price=Decimal(str(item.unit_price)),
                line_total=Decimal(str(item.line_total)),
            )
        )
    create_order_event(db, order, current_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _get_existing_checkout(db, normalized_key, current_user)
        if existing:
            return _checkout_response_from_order(existing, current_user, "Checkout request was already processed. Returning the original order.")
        raise

    _reserve_stock_in_inventory_service([{"product_id": item.product_id, "quantity": item.quantity} for item in checkout_items])
    db.refresh(order)
    return _checkout_response_from_order(order, current_user)


def list_orders(db: Session, limit: int = 25, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(OrderEntity).order_by(desc(OrderEntity.created_at))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                OrderEntity.order_number.ilike(term),
                OrderEntity.customer_name.ilike(term),
                cast(OrderEntity.status, String).ilike(term),
            )
        )
    return [order_to_dict(order) for order in db.scalars(statement.offset(offset).limit(limit)).all()]


def _get_order_fresh(db: Session, order_id: int) -> OrderEntity:
    """Load an order and its items from the current database state.

    Admin edit operations replace child order_items rows. On MySQL, stale ORM
    relationship state can remain in the Session after a bulk child-row update.
    This helper forces a fresh load with populate_existing so API responses do
    not accidentally read deleted/stale child objects.
    """
    order = db.scalar(
        select(OrderEntity)
        .options(selectinload(OrderEntity.items))
        .where(OrderEntity.id == order_id)
        .execution_options(populate_existing=True)
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id {order_id} was not found.")
    return order


def get_order(db: Session, order_id: int) -> dict:
    return order_to_dict(_get_order_fresh(db, order_id))


def _get_order_for_update(db: Session, order_id: int) -> OrderEntity:
    """Load only the parent order row for update operations.

    The OrderEntity.items relationship uses selectin loading for normal reads,
    but edit operations delete/replace child rows. Loading the child collection
    before replacement can leave stale/deleted item instances in the Session on
    MySQL. This update-specific loader disables relationship loading.
    """
    order = db.scalar(
        select(OrderEntity)
        .options(noload(OrderEntity.items))
        .where(OrderEntity.id == order_id)
        .execution_options(populate_existing=True)
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id {order_id} was not found.")
    return order


def _item_decimal(value) -> Decimal:
    """Convert user/API numeric values to Decimal safely for MySQL Numeric columns."""
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _recalculate_order_totals(order: OrderEntity) -> None:
    """Recompute totals after order-level charges or items change."""
    subtotal = _item_decimal(order.subtotal)
    discount = _item_decimal(order.discount)
    shipping_fee = _item_decimal(order.shipping_fee)
    tax = _item_decimal(order.tax)
    order.total = max(subtotal - discount, Decimal("0.00")) + shipping_fee + tax


def _normalized_item_tuple(product_id, product_name, quantity, unit_price) -> tuple[int, str, int, str]:
    return (
        int(product_id),
        str(product_name or "").strip(),
        int(quantity),
        str(_item_decimal(unit_price).quantize(Decimal("0.01"))),
    )


def _submitted_items_match_existing(db: Session, order_id: int, items: list[OrderItemCreate]) -> bool:
    """Return True when the edit payload has the same item set already stored.

    The Admin form often sends the full item list even when the user only
    changes the order status/customer fields. Skipping a no-op child-row
    replacement avoids unnecessary MySQL DELETE/INSERT work and prevents edit
    failures caused by stale child relationship state in long-running local
    service processes.
    """
    existing_rows = db.execute(
        select(
            OrderItemEntity.product_id,
            OrderItemEntity.product_name,
            OrderItemEntity.quantity,
            OrderItemEntity.unit_price,
        )
        .where(OrderItemEntity.order_id == order_id)
        .order_by(OrderItemEntity.product_id)
    ).all()
    if len(existing_rows) != len(items or []):
        return False
    existing = sorted(
        _normalized_item_tuple(row.product_id, row.product_name, row.quantity, row.unit_price)
        for row in existing_rows
    )
    submitted = sorted(
        _normalized_item_tuple(row.product_id, row.product_name, row.quantity, row.unit_price)
        for row in (items or [])
    )
    return existing == submitted


def _sync_subtotal_from_existing_items(db: Session, order: OrderEntity) -> None:
    subtotal = db.scalar(
        select(func.coalesce(func.sum(OrderItemEntity.line_total), 0)).where(OrderItemEntity.order_id == order.id)
    )
    order.subtotal = _item_decimal(subtotal)
    _recalculate_order_totals(order)


def _replace_items(db: Session, order: OrderEntity, items: list[OrderItemCreate]):
    """Synchronize order items safely without triggering duplicate keys.

    The Admin edit form sends the full item list on every save. Earlier builds
    solved this by deleting all child rows and reinserting them, but long-running
    Uvicorn workers can still keep stale ORM relationship state. MySQL then sees
    an attempted INSERT for the same ``(order_id, product_id)`` and raises:

        Duplicate entry '<order_id>-<product_id>' for key 'uq_order_item_product'

    This implementation avoids that failure by treating ``product_id`` as the
    natural key inside one order:

    * validate and de-duplicate the submitted payload first;
    * UPDATE existing rows when the product already exists in the order;
    * INSERT only products that are genuinely new;
    * DELETE products removed from the submitted item list;
    * expire the relationship so the API response reloads fresh rows.

    Because unchanged products are updated in place, MySQL never receives a
    duplicate INSERT for an existing ``order_id/product_id`` pair.
    """
    cleaned_items: list[OrderItemCreate] = []
    subtotal = Decimal("0.00")
    seen_products: set[int] = set()

    for payload in items or []:
        product_id = int(payload.product_id)
        if product_id in seen_products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate product_id {product_id} in order items. Each product may appear only once per order.",
            )
        seen_products.add(product_id)

        product_name = str(payload.product_name or "").strip()
        if not product_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing product_name for product_id {product_id}.",
            )
        if int(payload.quantity) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quantity for product_id {product_id} must be at least 1.",
            )

        unit_price = _item_decimal(payload.unit_price)
        line_total = Decimal(int(payload.quantity)) * unit_price
        subtotal += line_total
        cleaned_items.append(payload)

    existing_rows = db.scalars(
        select(OrderItemEntity).where(OrderItemEntity.order_id == order.id)
    ).all()
    existing_by_product = {int(row.product_id): row for row in existing_rows}
    submitted_product_ids = {int(payload.product_id) for payload in cleaned_items}

    # Delete rows that were removed from the submitted order items.
    products_to_remove = set(existing_by_product) - submitted_product_ids
    if products_to_remove:
        db.execute(
            delete(OrderItemEntity)
            .where(
                OrderItemEntity.order_id == order.id,
                OrderItemEntity.product_id.in_(products_to_remove),
            )
            .execution_options(synchronize_session=False)
        )
        db.flush()

    # Update existing rows in place and insert only genuinely new products.
    for payload in cleaned_items:
        product_id = int(payload.product_id)
        quantity = int(payload.quantity)
        unit_price = _item_decimal(payload.unit_price)
        line_total = Decimal(quantity) * unit_price
        existing = existing_by_product.get(product_id)
        if existing is not None:
            existing.product_name = str(payload.product_name).strip()
            existing.quantity = quantity
            existing.unit_price = unit_price
            existing.line_total = line_total
        else:
            db.add(
                OrderItemEntity(
                    order_id=order.id,
                    product_id=product_id,
                    product_name=str(payload.product_name).strip(),
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

    order.subtotal = subtotal
    _recalculate_order_totals(order)
    db.flush()
    # Ensure order_to_dict() returns the current child rows after commit.
    db.expire(order, ["items"])


def create_order(db: Session, order_create: OrderCreate, current_user: dict) -> dict:
    order = OrderEntity(
        order_number=f"ORD-{uuid4().hex[:8].upper()}",
        user_id=current_user.get("id"),
        customer_name=order_create.customer_name,
        delivery_address=order_create.delivery_address,
        payment_method=order_create.payment_method,
        status=status_to_storage(enum_from_input(OrderStatus, order_create.status, OrderStatus.NEW)),
        discount=order_create.discount,
        shipping_fee=order_create.shipping_fee,
        tax=order_create.tax,
    )
    db.add(order)
    db.flush()
    _replace_items(db, order, order_create.items)
    create_order_event(db, order, current_user)
    db.commit()
    db.refresh(order)
    return order_to_dict(order)


def update_order(db: Session, order_id: int, order_update: OrderUpdate, current_user: dict) -> dict:
    order = _get_order_for_update(db, order_id)

    try:
        for field in ["customer_name", "delivery_address", "payment_method", "discount", "shipping_fee", "tax"]:
            value = getattr(order_update, field)
            if value is not None:
                setattr(order, field, value)

        if order_update.status is not None:
            order.status = status_to_storage(enum_from_input(OrderStatus, order_update.status, order.status))

        if order_update.items is not None:
            # Synchronize in place. This is safe for both unchanged item lists
            # and true item edits because existing products are updated instead
            # of deleted/reinserted.
            _replace_items(db, order, order_update.items)
        else:
            _recalculate_order_totals(order)
            db.flush()

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unable to update order because the item list violates an order constraint. "
                "Make sure each product appears only once in the order items JSON."
            ),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to update order due to a database error: {exc.__class__.__name__}: {str(exc)[:300]}",
        ) from exc
    except Exception as exc:
        db.rollback()
        # Convert unexpected update failures to a useful API message instead of
        # a generic 500 Internal Server Error. This is especially helpful in
        # Windows/local MySQL where stale service processes can hide the true
        # backend exception from PowerShell Invoke-RestMethod.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to update order: {exc.__class__.__name__}: {str(exc)[:300]}",
        ) from exc

    # Important: return a fresh copy after commit. The update path replaces
    # order_items rows, so relationship state from before the delete/insert can
    # be stale inside the current Session.
    db.expire_all()
    return order_to_dict(_get_order_fresh(db, order_id))


def delete_order(db: Session, order_id: int, current_user: dict) -> dict:
    order = db.get(OrderEntity, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id {order_id} was not found.")
    db.delete(order)
    db.commit()
    return {"message": "Order deleted successfully.", "id": order_id}
