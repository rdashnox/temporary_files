from .app_factory import create_service_app
from .core.config import settings
from .routes import auth, data, database_entities, inventory, notifications, orders, shop

app = create_service_app(
    service_name="Platform",
    service_slug="platform-monolith",
    router_specs=(
        (auth.router, "/api/v1/auth", ("auth",)),
        (data.router, "/api/v1/data", ("data",)),
        (inventory.router, "/api/v1/inventory", ("inventory-service",)),
        (orders.router, "/api/v1/orders", ("order-service",)),
        (notifications.router, "/api/v1/notifications", ("notification-service",)),
        (shop.router, "/api/v1/shop", ("shop-legacy",)),
        (database_entities.router, "/api/v1/database", ("database",)),
    ),
)


@app.get("/api/v1/scale/profile")
def scale_profile():
    """Expose non-sensitive scalability configuration for deployment checks."""
    return {
        "target_active_users": 1000,
        "deployment_mode": settings.deployment_mode,
        "service_replicas": settings.service_replicas,
        "microservice_topology": {
            "auth-service": settings.service_replicas,
            "order-service": settings.service_replicas,
            "inventory-service": settings.service_replicas,
            "notification-service": settings.service_replicas,
        },
        "recommended_production_workers": "2 to 4 per service replica, then verify with load test",
        "database_pool_size_per_worker": settings.db_pool_size,
        "database_max_overflow_per_worker": settings.db_max_overflow,
        "threadpool_tokens_per_worker": settings.threadpool_tokens,
        "product_cache_max_age_seconds": settings.product_cache_max_age_seconds,
        "notes": [
            "Use the included microservice Docker Compose file for local 3-node service testing.",
            "Use the included Kubernetes manifests for cloud deployments with 3 replicas per service.",
            "Run loadtests/locustfile.py against the Nginx/API gateway before real user traffic.",
        ],
    }
