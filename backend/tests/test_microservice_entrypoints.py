from fastapi.testclient import TestClient

from backend.microservices.auth_main import app as auth_app
from backend.microservices.inventory_main import app as inventory_app
from backend.microservices.notification_main import app as notification_app
from backend.microservices.order_main import app as order_app


def test_microservice_entrypoints_expose_service_identity():
    service_apps = [
        (auth_app, "auth-service"),
        (order_app, "order-service"),
        (inventory_app, "inventory-service"),
        (notification_app, "notification-service"),
    ]

    for app, expected_service in service_apps:
        with TestClient(app) as client:
            response = client.get("/api/v1/service-info")
            assert response.status_code == 200
            body = response.json()
            assert body["service"] == expected_service
            assert body["target_replicas_per_microservice"] == 3
            assert body["backup_nodes_after_one_failure"] == 2
