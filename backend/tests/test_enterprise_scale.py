from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _headers():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_ready_and_scale_profile_endpoints():
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers["x-request-id"]
    assert health.headers["x-process-time-ms"]

    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    profile = client.get("/api/v1/scale/profile")
    assert profile.status_code == 200
    assert profile.json()["target_active_users"] == 1000


def test_products_use_short_private_cache_headers():
    response = client.get("/api/v1/inventory/products", headers=_headers())
    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("private, max-age=")


def test_checkout_idempotency_key_prevents_duplicate_orders():
    headers = _headers()
    idempotency_key = f"checkout-test-{uuid4()}"
    payload = {
        "customer_name": "Idempotent Customer",
        "delivery_address": "1000 Scale Avenue, Manila",
        "payment_method": "Cash on Delivery",
        "idempotency_key": idempotency_key,
        "items": [{"product_id": 1, "quantity": 1}],
    }

    first = client.post(
        "/api/v1/orders/checkout",
        headers={**headers, "Idempotency-Key": idempotency_key},
        json=payload,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/orders/checkout",
        headers={**headers, "Idempotency-Key": idempotency_key},
        json=payload,
    )
    assert second.status_code == 201
    assert second.json()["order_id"] == first.json()["order_id"]
    assert "already processed" in second.json()["message"]
