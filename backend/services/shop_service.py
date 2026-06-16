from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..constants.products import PRODUCTS
from ..models import AuditAction, Order, OrderItem, OrderStatus
from ..schemas.shop import CheckoutItem, CheckoutRequest, CheckoutResponse, CheckoutSummary, Product
from .audit_service import create_audit_log


def list_products() -> list[Product]:
    return PRODUCTS


def find_product(product_id: int) -> Product | None:
    return next((product for product in PRODUCTS if product.id == product_id), None)


def round_money(value: float) -> float:
    return round(value + 0.00001, 2)


def checkout(db: Session, checkout_request: CheckoutRequest, current_user: dict) -> CheckoutResponse:
    checkout_items: list[CheckoutItem] = []

    for item in checkout_request.items:
        product = find_product(item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item.product_id} was not found.",
            )

        if item.quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock} item(s) available for {product.name}.",
            )

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

    subtotal = round_money(sum(item.line_total for item in checkout_items))
    coupon_code = (checkout_request.coupon_code or "").strip().upper()
    discount = round_money(subtotal * 0.10) if coupon_code == "SAVE10" else 0
    shipping_fee = 0 if subtotal >= 3000 else 150
    taxable_amount = max(subtotal - discount, 0)
    tax = round_money(taxable_amount * 0.12)
    total = round_money(taxable_amount + shipping_fee + tax)
    order_number = f"FM-{uuid4().hex[:8].upper()}"

    order = Order(
        order_number=order_number,
        user_id=current_user.get("id"),
        customer_name=checkout_request.customer_name,
        delivery_address=checkout_request.delivery_address,
        payment_method=checkout_request.payment_method,
        status=OrderStatus.PAID,
        subtotal=Decimal(str(subtotal)),
        discount=Decimal(str(discount)),
        shipping_fee=Decimal(str(shipping_fee)),
        tax=Decimal(str(tax)),
        total=Decimal(str(total)),
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
        action=AuditAction.CHECKOUT,
        entity_type="orders",
        entity_id=order_number,
        detail=f"Checkout completed for {checkout_request.customer_name}.",
    )
    db.commit()

    return CheckoutResponse(
        order_id=order_number,
        status="confirmed",
        message="Checkout completed successfully. Order was saved to the database.",
        authenticated_user=current_user["username"],
        checked_out_at=datetime.now(timezone.utc).isoformat(),
        items=checkout_items,
        summary=CheckoutSummary(
            subtotal=subtotal,
            discount=discount,
            shipping_fee=shipping_fee,
            tax=tax,
            total=total,
        ),
    )
