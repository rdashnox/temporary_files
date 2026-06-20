from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import String, cast, desc, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import AuditAction, Order, OrderItem, OrderStatus
from ..schemas.database_entities import OrderCreate, OrderItemCreate, OrderUpdate
from ..schemas.shop import CheckoutItem, CheckoutRequest, CheckoutResponse, CheckoutSummary
from .audit_service import create_audit_log
from .common import (
    EntityNotFound,
    actor_from_current_user,
    enum_from_input,
    enum_to_api,
    iso,
    money,
    paginate,
)
from .inventory_service import assert_available
from .notification_service import notify_order_created
from .pricing_service import calculate_checkout_summary, round_money


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "idempotency_key": order.idempotency_key,
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


def _build_checkout_items(checkout_request: CheckoutRequest) -> list[CheckoutItem]:
    checkout_items: list[CheckoutItem] = []
    for item in checkout_request.items:
        product = assert_available(item.product_id, item.quantity)
        line_total = round_money(product.price * item.quantity)
        checkout_items.append(
            CheckoutItem(
                product_id=product.id,
                name=product.name,
                quantity=item.quantity,
                unit_price=product.price,
                line_total=line_total,
            )
        )
    return checkout_items


def _normalize_idempotency_key(header_key: str | None, body_key: str | None) -> str | None:
    key = (header_key or body_key or "").strip()
    if not key:
        return None
    if len(key) > 120:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not exceed 120 characters.",
        )
    return key


def _get_existing_checkout(db: Session, idempotency_key: str | None, current_user: dict) -> Order | None:
    if not idempotency_key:
        return None

    return db.scalar(
        select(Order).where(
            Order.idempotency_key == idempotency_key,
            Order.user_id == current_user.get("id"),
        )
    )


def _checkout_response_from_order(
    order: Order,
    current_user: dict,
    *,
    message: str = "Checkout completed successfully. Order was saved to the database.",
) -> CheckoutResponse:
    checkout_items = [
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
        status="confirmed",
        message=message,
        authenticated_user=current_user["username"],
        checked_out_at=iso(order.created_at) or datetime.now(timezone.utc).isoformat(),
        items=checkout_items,
        summary=summary,
    )


def checkout(
    db: Session,
    checkout_request: CheckoutRequest,
    current_user: dict,
    idempotency_key: str | None = None,
) -> CheckoutResponse:
    """Create an order from cart items with retry-safe idempotency.

    Responsibilities are intentionally delegated:
    inventory_service validates stock, pricing_service calculates totals,
    notification_service creates business events, and audit_service records traceability.
    """
    normalized_key = _normalize_idempotency_key(idempotency_key, checkout_request.idempotency_key)
    existing_order = _get_existing_checkout(db, normalized_key, current_user)
    if existing_order is not None:
        return _checkout_response_from_order(
            existing_order,
            current_user,
            message="Checkout request was already processed. Returning the original order.",
        )

    checkout_items = _build_checkout_items(checkout_request)
    summary = calculate_checkout_summary(checkout_items, checkout_request.coupon_code)
    order_number = f"FM-{uuid4().hex[:8].upper()}"

    order = Order(
        order_number=order_number,
        user_id=current_user.get("id"),
        idempotency_key=normalized_key,
        customer_name=checkout_request.customer_name,
        delivery_address=checkout_request.delivery_address,
        payment_method=checkout_request.payment_method,
        status=OrderStatus.PAID,
        subtotal=Decimal(str(summary.subtotal)),
        discount=Decimal(str(summary.discount)),
        shipping_fee=Decimal(str(summary.shipping_fee)),
        tax=Decimal(str(summary.tax)),
        total=Decimal(str(summary.total)),
    )
    db.add(order)
    db.flush()

    for checkout_item in checkout_items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=checkout_item.product_id,
                product_name=checkout_item.name,
                quantity=checkout_item.quantity,
                unit_price=Decimal(str(checkout_item.unit_price)),
                line_total=Decimal(str(checkout_item.line_total)),
            )
        )

    create_audit_log(
        db,
        actor=actor_from_current_user(db, current_user),
        action=AuditAction.CHECKOUT,
        entity_type="orders",
        entity_id=order_number,
        detail=f"Checkout completed for {checkout_request.customer_name}.",
    )
    notify_order_created(
        db,
        order_number=order_number,
        customer_name=checkout_request.customer_name,
        total=order.total,
        user_id=current_user.get("id"),
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_order = _get_existing_checkout(db, normalized_key, current_user)
        if existing_order is not None:
            return _checkout_response_from_order(
                existing_order,
                current_user,
                message="Checkout request was already processed. Returning the original order.",
            )
        raise

    return _checkout_response_from_order(order, current_user)


def _recalculate_order_totals(order: Order):
    subtotal = sum((item.line_total for item in order.items), Decimal("0.00"))
    order.subtotal = subtotal
    order.total = max(subtotal - order.discount, Decimal("0.00")) + order.shipping_fee + order.tax


def _replace_order_items(db: Session, order: Order, items: list[OrderItemCreate]):
    order.items.clear()
    db.flush()
    for payload in items:
        line_total = Decimal(payload.quantity) * payload.unit_price
        order.items.append(
            OrderItem(
                product_id=payload.product_id,
                product_name=payload.product_name,
                quantity=payload.quantity,
                unit_price=payload.unit_price,
                line_total=line_total,
            )
        )
    _recalculate_order_totals(order)


def list_orders(db: Session, limit: int = 25, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(Order).order_by(desc(Order.created_at))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Order.order_number.ilike(term),
                Order.customer_name.ilike(term),
                cast(Order.status, String).ilike(term),
            )
        )
    orders = db.scalars(paginate(statement, limit, offset)).all()
    return [order_to_dict(order) for order in orders]


def get_order(db: Session, order_id: int) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise EntityNotFound("Order", order_id)
    return order_to_dict(order)


def create_order(db: Session, order_create: OrderCreate, current_user: dict) -> dict:
    order = Order(
        order_number=f"ORD-{uuid4().hex[:8].upper()}",
        user_id=current_user.get("id"),
        customer_name=order_create.customer_name,
        delivery_address=order_create.delivery_address,
        payment_method=order_create.payment_method,
        status=enum_from_input(OrderStatus, order_create.status, OrderStatus.NEW),
        discount=order_create.discount,
        shipping_fee=order_create.shipping_fee,
        tax=order_create.tax,
    )
    db.add(order)
    db.flush()
    _replace_order_items(db, order, order_create.items)
    create_audit_log(
        db,
        actor=actor_from_current_user(db, current_user),
        action=AuditAction.CREATE,
        entity_type="orders",
        entity_id=order.order_number,
        detail=f"Created order {order.order_number}.",
    )
    notify_order_created(
        db,
        order_number=order.order_number,
        customer_name=order.customer_name,
        total=order.total,
        user_id=current_user.get("id"),
    )
    db.commit()
    db.refresh(order)
    return order_to_dict(order)


def update_order(db: Session, order_id: int, order_update: OrderUpdate, current_user: dict) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise EntityNotFound("Order", order_id)
    for field in ["customer_name", "delivery_address", "payment_method", "discount", "shipping_fee", "tax"]:
        value = getattr(order_update, field)
        if value is not None:
            setattr(order, field, value)
    if order_update.status is not None:
        order.status = enum_from_input(OrderStatus, order_update.status, order.status)
    if order_update.items is not None:
        _replace_order_items(db, order, order_update.items)
    else:
        _recalculate_order_totals(order)
    create_audit_log(
        db,
        actor=actor_from_current_user(db, current_user),
        action=AuditAction.UPDATE,
        entity_type="orders",
        entity_id=order.order_number,
        detail=f"Updated order {order.order_number}.",
    )
    db.commit()
    db.refresh(order)
    return order_to_dict(order)


def delete_order(db: Session, order_id: int, current_user: dict) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise EntityNotFound("Order", order_id)
    order_number = order.order_number
    db.delete(order)
    create_audit_log(
        db,
        actor=actor_from_current_user(db, current_user),
        action=AuditAction.DELETE,
        entity_type="orders",
        entity_id=order_number,
        detail=f"Deleted order {order_number}.",
    )
    db.commit()
    return {"message": "Order deleted successfully.", "id": order_id}
