from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def register_payload(username="newuser@example.com", password="StrongPass123!"):
    return {
        "username": username,
        "password": password,
        "confirm_password": password,
    }


def login(username, password):
    return client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def test_register_requires_strong_password():
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload("weak-password@example.com", "password"),
    )

    assert response.status_code == 400
    assert "uppercase" in response.json()["detail"]


def test_register_requires_matching_passwords():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "mismatch@example.com",
            "password": "StrongPass123!",
            "confirm_password": "Different123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords do not match"


def test_registration_email_verification_login_and_protected_route():
    username = "verified-flow@example.com"
    password = "StrongPass123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json=register_payload(username, password),
    )
    assert register_response.status_code == 201
    verification_token = register_response.json()["verification_token"]

    login_before_verify = login(username, password)
    assert login_before_verify.status_code == 403

    verify_response = client.get(f"/api/v1/auth/verify-email?token={verification_token}")
    assert verify_response.status_code == 200

    login_response = login(username, password)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data["access_token"]
    assert token_data["refresh_token"]
    assert token_data["token_type"] == "bearer"

    protected_response = client.get(
        "/api/v1/data/protected",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert protected_response.status_code == 200
    assert protected_response.json()["authenticated_user"] == username

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_data["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]


def test_duplicate_registration_returns_conflict():
    username = "duplicate@example.com"
    password = "StrongPass123!"

    first_response = client.post(
        "/api/v1/auth/register",
        json=register_payload(username, password),
    )
    second_response = client.post(
        "/api/v1/auth/register",
        json=register_payload(username, password),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_forgot_password_and_reset_password_flow():
    username = "reset-flow@example.com"
    old_password = "StrongPass123!"
    new_password = "NewStrongPass123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json=register_payload(username, old_password),
    )
    verification_token = register_response.json()["verification_token"]
    client.get(f"/api/v1/auth/verify-email?token={verification_token}")

    forgot_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"username": username},
    )
    assert forgot_response.status_code == 200
    reset_token = forgot_response.json()["reset_token"]

    reset_response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )
    assert reset_response.status_code == 200

    old_login_response = login(username, old_password)
    assert old_login_response.status_code == 401

    new_login_response = login(username, new_password)
    assert new_login_response.status_code == 200


def test_protected_route_rejects_invalid_token():
    response = client.get(
        "/api/v1/data/protected",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_business_modules_route_returns_dashboard_view_model_for_verified_user():
    login_response = login("user@example.com", "Password123!")
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/data/business-modules",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["dashboard_load_target_seconds"] == 3
    assert data["summary"]["ordersToday"] <= data["metadata"]["daily_order_capacity_target"]
    assert "financialPerformance" in data["bi"]
    assert data["orders"]["statuses"]
    assert data["access"]["roles"]
    assert data["marketing"]["funnel"]


def test_password_is_stored_as_bcrypt_hash_not_plain_text():
    from sqlalchemy import select

    from backend.database import SessionLocal
    from backend.models import User

    username = "hash-check@example.com"
    password = "StrongPass123!"

    response = client.post("/api/v1/auth/register", json=register_payload(username, password))
    assert response.status_code == 201

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == username))

    assert user is not None
    assert user.hashed_password != password
    assert user.hashed_password.startswith("$2b$")


def test_database_roles_permissions_and_me_routes_are_protected():
    login_response = login("user@example.com", "Password123!")
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    me_response = client.get("/api/v1/database/me", headers=headers)
    assert me_response.status_code == 200
    assert "Admin" in me_response.json()["roles"]
    assert "orders.read" in me_response.json()["permissions"]

    roles_response = client.get("/api/v1/database/roles", headers=headers)
    permissions_response = client.get("/api/v1/database/permissions", headers=headers)

    assert roles_response.status_code == 200
    assert permissions_response.status_code == 200
    assert any(role["name"] == "Admin" for role in roles_response.json())
    assert any(permission["code"] == "audit.read" for permission in permissions_response.json())
