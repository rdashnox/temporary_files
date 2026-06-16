from typing import List, Optional

from pydantic import BaseModel, Field


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
