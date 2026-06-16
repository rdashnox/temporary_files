from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .data import get_current_user

router = APIRouter()


class Product(BaseModel):
    id: int
    name: str
    category: str
    description: str
    price: float
    compare_at_price: Optional[float] = None
    stock: int
    rating: float
    badge: str
    image: str


class CartItemRequest(BaseModel):
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1, le=99)


class CheckoutRequest(BaseModel):
    items: List[CartItemRequest] = Field(..., min_length=1)
    customer_name: str = Field(..., min_length=2, max_length=80)
    delivery_address: str = Field(..., min_length=5, max_length=180)
    payment_method: str = Field(default="Cash on Delivery", max_length=40)
    coupon_code: Optional[str] = Field(default=None, max_length=20)


class CheckoutItem(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: float
    line_total: float


class CheckoutSummary(BaseModel):
    subtotal: float
    discount: float
    shipping_fee: float
    tax: float
    total: float


class CheckoutResponse(BaseModel):
    order_id: str
    status: str
    message: str
    authenticated_user: str
    checked_out_at: str
    items: List[CheckoutItem]
    summary: CheckoutSummary


PRODUCTS: List[Product] = [
    Product(
        id=1,
        name="FinMark Smart Ledger",
        category="Finance Tools",
        description="A lightweight ledger kit for tracking small-business sales, expenses, and cash flow.",
        price=1499,
        compare_at_price=1899,
        stock=18,
        rating=4.8,
        badge="Best Seller",
        image="📒",
    ),
    Product(
        id=2,
        name="Marketing Launch Pack",
        category="Marketing",
        description="Ready-to-use campaign templates for product launches, retargeting, and weekly reporting.",
        price=2199,
        compare_at_price=2599,
        stock=11,
        rating=4.7,
        badge="Popular",
        image="🚀",
    ),
    Product(
        id=3,
        name="Inventory Starter Bundle",
        category="Operations",
        description="Barcode labels, reorder trackers, and stock movement templates for growing stores.",
        price=1799,
        compare_at_price=None,
        stock=25,
        rating=4.6,
        badge="New",
        image="📦",
    ),
    Product(
        id=4,
        name="Business Analytics Board",
        category="Analytics",
        description="Dashboard widgets for revenue trends, product performance, and conversion monitoring.",
        price=2999,
        compare_at_price=3499,
        stock=8,
        rating=4.9,
        badge="Premium",
        image="📊",
    ),
    Product(
        id=5,
        name="Checkout Optimization Kit",
        category="E-Commerce",
        description="A UX checklist and reporting pack for reducing abandoned carts and improving checkout flow.",
        price=1299,
        compare_at_price=1599,
        stock=16,
        rating=4.5,
        badge="Sale",
        image="🛒",
    ),
    Product(
        id=6,
        name="Customer Care Script Set",
        category="Support",
        description="Reusable response templates for order issues, refunds, shipping delays, and client follow-ups.",
        price=899,
        compare_at_price=None,
        stock=31,
        rating=4.4,
        badge="Starter",
        image="💬",
    ),
]


def _find_product(product_id: int) -> Optional[Product]:
    return next((product for product in PRODUCTS if product.id == product_id), None)


def _round_money(value: float) -> float:
    return round(value + 0.00001, 2)


@router.get("/products", response_model=List[Product])
async def list_products(current_user: dict = Depends(get_current_user)):
    """Return protected product catalog data for the React add-to-cart dashboard."""
    return PRODUCTS


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    checkout_request: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
):
    """Validate cart items and return a demo checkout confirmation."""
    checkout_items: List[CheckoutItem] = []

    for item in checkout_request.items:
        product = _find_product(item.product_id)
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

        line_total = _round_money(product.price * item.quantity)
        checkout_items.append(
            CheckoutItem(
                product_id=product.id,
                name=product.name,
                quantity=item.quantity,
                unit_price=product.price,
                line_total=line_total,
            )
        )

    subtotal = _round_money(sum(item.line_total for item in checkout_items))
    coupon_code = (checkout_request.coupon_code or "").strip().upper()
    discount = _round_money(subtotal * 0.10) if coupon_code == "SAVE10" else 0
    shipping_fee = 0 if subtotal >= 3000 else 150
    taxable_amount = max(subtotal - discount, 0)
    tax = _round_money(taxable_amount * 0.12)
    total = _round_money(taxable_amount + shipping_fee + tax)

    return CheckoutResponse(
        order_id=f"FM-{uuid4().hex[:8].upper()}",
        status="confirmed",
        message="Checkout completed successfully. This is a demo order and no payment was charged.",
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
