from ..app_factory import create_service_app
from ..routes import auth, data, database_entities

app = create_service_app(
    service_name="Auth/Login",
    service_slug="auth-service",
    router_specs=(
        (auth.router, "/api/v1/auth", ("auth-service",)),
        # Compatibility endpoints used by the current frontend session and admin screens.
        (data.router, "/api/v1/data", ("auth-service", "session")),
        (database_entities.router, "/api/v1/database", ("auth-service", "admin-compatibility")),
    ),
)
