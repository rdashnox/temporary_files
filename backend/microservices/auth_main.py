from ..enterprise.app_factory import create_enterprise_service_app
from ..enterprise.routes import auth, data, database_compat

app = create_enterprise_service_app(
    service_name="Auth/Login",
    service_slug="auth-service",
    service_key="auth",
    router_specs=(
        (auth.router, "/api/v1/auth", ("auth-service",)),
        (data.router, "/api/v1/data", ("auth-service", "session")),
        (database_compat.router, "/api/v1/database", ("auth-service", "database-compat")),
    ),
)
