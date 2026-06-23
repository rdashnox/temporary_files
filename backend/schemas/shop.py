from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_PAYMENT_METHODS = {"Cash on Delivery", "Bank Transfer", "GCash"}


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _required_text(value: str | None, field_name: str) -> str:
    cleaned = _clean_optional(value)
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


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
    model_config = ConfigDict(str_strip_whitespace=True)

    items: List[CartItemRequest] = Field(..., min_length=1)
    customer_name: str = Field(..., min_length=2, max_length=80)
    delivery_address: str = Field(..., min_length=5, max_length=180)
    payment_method: str = Field(default="Cash on Delivery", max_length=40)
    coupon_code: Optional[str] = Field(default=None, max_length=20)
    # Optional retry-safety key. The frontend also sends this as an
    # Idempotency-Key header so checkout retries do not create duplicate orders.
    idempotency_key: Optional[str] = Field(default=None, max_length=120)

    @field_validator("customer_name")
    @classmethod
    def customer_name_required(cls, value: str):
        return _required_text(value, "Customer name")

    @field_validator("delivery_address")
    @classmethod
    def delivery_address_required(cls, value: str):
        return _required_text(value, "Delivery address")

    @field_validator("payment_method")
    @classmethod
    def valid_payment_method(cls, value: str):
        cleaned = _required_text(value, "Payment method")
        if cleaned not in ALLOWED_PAYMENT_METHODS:
            raise ValueError(f"Invalid payment method. Allowed values: {', '.join(sorted(ALLOWED_PAYMENT_METHODS))}.")
        return cleaned

    @field_validator("coupon_code", "idempotency_key")
    @classmethod
    def clean_optional_text(cls, value: str | None):
        return _clean_optional(value)

    @model_validator(mode="after")
    def unique_checkout_products(self):
        seen: set[int] = set()
        duplicates: set[int] = set()
        for item in self.items:
            if item.product_id in seen:
                duplicates.add(item.product_id)
            seen.add(item.product_id)
        if duplicates:
            raise ValueError(f"Duplicate product_id values are not allowed in checkout: {', '.join(map(str, sorted(duplicates)))}.")
        return self


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
