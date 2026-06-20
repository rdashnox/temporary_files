from ..enterprise.app_factory import create_enterprise_service_app
from ..enterprise.routes import notifications

app = create_enterprise_service_app(
    service_name="Notification",
    service_slug="notification-service",
    service_key="notification",
    router_specs=((notifications.router, "/api/v1/notifications", ("notification-service",)),),
)
