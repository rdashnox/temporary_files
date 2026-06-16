from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _login_headers():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_products_require_authentication():
    response = client.get("/api/v1/shop/products")
    assert response.status_code == 401


def test_list_products_with_authenticated_user():
    response = client.get("/api/v1/shop/products", headers=_login_headers())
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 3
    assert {"id", "name", "price", "stock"}.issubset(products[0].keys())


def test_checkout_returns_order_summary():
    response = client.post(
        "/api/v1/shop/checkout",
        headers=_login_headers(),
        json={
            "customer_name": "Demo User",
            "delivery_address": "123 FinMark Street, Manila",
            "payment_method": "Cash on Delivery",
            "coupon_code": "SAVE10",
            "items": [
                {"product_id": 1, "quantity": 1},
                {"product_id": 5, "quantity": 2},
            ],
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "confirmed"
    assert payload["order_id"].startswith("FM-")
    assert payload["summary"]["discount"] > 0
    assert payload["summary"]["total"] > 0
