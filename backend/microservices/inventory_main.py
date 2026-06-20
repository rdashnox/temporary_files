from ..enterprise.app_factory import create_enterprise_service_app
from ..enterprise.routes import inventory

app = create_enterprise_service_app(
    service_name="Inventory",
    service_slug="inventory-service",
    service_key="inventory",
    router_specs=((inventory.router, "/api/v1/inventory", ("inventory-service",)),),
)
