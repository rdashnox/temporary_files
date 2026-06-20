from ..enterprise.app_factory import create_enterprise_service_app
from ..enterprise.routes import orders, shop

app = create_enterprise_service_app(
    service_name="Order",
    service_slug="order-service",
    service_key="order",
    router_specs=(
        (orders.router, "/api/v1/orders", ("order-service",)),
        (shop.router, "/api/v1/shop", ("shop-legacy", "order-service")),
    ),
)
