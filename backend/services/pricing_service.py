from ..schemas.shop import CheckoutItem, CheckoutSummary


FREE_SHIPPING_THRESHOLD = 3000
STANDARD_SHIPPING_FEE = 150
VAT_RATE = 0.12
COUPON_DISCOUNTS = {
    "SAVE10": 0.10,
}


def round_money(value: float) -> float:
    """Round currency values consistently for all order services."""
    return round(value + 0.00001, 2)


def calculate_checkout_summary(items: list[CheckoutItem], coupon_code: str | None = None) -> CheckoutSummary:
    """Centralize order pricing rules so routes do not duplicate calculations."""
    subtotal = round_money(sum(item.line_total for item in items))
    normalized_coupon = (coupon_code or "").strip().upper()
    discount_rate = COUPON_DISCOUNTS.get(normalized_coupon, 0)
    discount = round_money(subtotal * discount_rate)
    shipping_fee = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING_FEE
    taxable_amount = max(subtotal - discount, 0)
    tax = round_money(taxable_amount * VAT_RATE)
    total = round_money(taxable_amount + shipping_fee + tax)

    return CheckoutSummary(
        subtotal=subtotal,
        discount=discount,
        shipping_fee=shipping_fee,
        tax=tax,
        total=total,
    )
