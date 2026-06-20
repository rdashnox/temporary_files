from ..app_factory import create_service_app
from ..routes import notifications

app = create_service_app(
    service_name="Notification",
    service_slug="notification-service",
    router_specs=(
        (notifications.router, "/api/v1/notifications", ("notification-service",)),
    ),
)
