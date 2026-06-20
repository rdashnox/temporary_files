from ..app_factory import create_service_app
from ..routes import inventory

app = create_service_app(
    service_name="Inventory",
    service_slug="inventory-service",
    router_specs=(
        (inventory.router, "/api/v1/inventory", ("inventory-service",)),
    ),
)
