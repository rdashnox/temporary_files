from ..app_factory import create_service_app
from ..routes import orders, shop

app = create_service_app(
    service_name="Order",
    service_slug="order-service",
    router_specs=(
        (orders.router, "/api/v1/orders", ("order-service",)),
        # Legacy checkout facade kept for old clients that still call /shop/checkout.
        (shop.router, "/api/v1/shop", ("shop-legacy", "order-service")),
    ),
)
