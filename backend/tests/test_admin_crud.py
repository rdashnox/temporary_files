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


def test_admin_can_crud_users_roles_permissions():
    headers = _headers()

    permission_response = client.post(
        "/api/v1/database/permissions",
        headers=headers,
        json={
            "code": "demo.manage",
            "name": "Manage Demo",
            "module": "demo",
            "description": "Temporary test permission.",
        },
    )
    assert permission_response.status_code == 201
    permission_id = permission_response.json()["id"]

    role_response = client.post(
        "/api/v1/database/roles",
        headers=headers,
        json={
            "name": "Demo Admin Role",
            "description": "Temporary test role.",
            "permission_ids": [permission_id],
        },
    )
    assert role_response.status_code == 201
    role_id = role_response.json()["id"]

    user_response = client.post(
        "/api/v1/database/users",
        headers=headers,
        json={
            "username": "admin-crud-user@example.com",
            "password": "StrongPass123!",
            "is_verified": True,
            "role_ids": [role_id],
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    update_user_response = client.put(
        f"/api/v1/database/users/{user_id}",
        headers=headers,
        json={"full_name": "Admin CRUD User", "is_active": True},
    )
    assert update_user_response.status_code == 200
    assert update_user_response.json()["full_name"] == "Admin CRUD User"

    delete_user_response = client.delete(f"/api/v1/database/users/{user_id}", headers=headers)
    assert delete_user_response.status_code == 200

    delete_role_response = client.delete(f"/api/v1/database/roles/{role_id}", headers=headers)
    assert delete_role_response.status_code == 200

    delete_permission_response = client.delete(f"/api/v1/database/permissions/{permission_id}", headers=headers)
    assert delete_permission_response.status_code == 200


def test_admin_can_crud_orders_reports_planning_and_audit_logs():
    headers = _headers()

    order_response = client.post(
        "/api/v1/database/orders",
        headers=headers,
        json={
            "customer_name": "CRUD Customer",
            "delivery_address": "789 Admin Street, Manila",
            "payment_method": "Cash on Delivery",
            "status": "NEW",
            "items": [
                {"product_id": 101, "product_name": "CRUD Product", "quantity": 2, "unit_price": 1500}
            ],
        },
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    update_order_response = client.put(
        f"/api/v1/database/orders/{order_id}",
        headers=headers,
        json={"status": "PAID"},
    )
    assert update_order_response.status_code == 200
    assert update_order_response.json()["status"] == "PAID"

    report_response = client.post(
        "/api/v1/database/reports",
        headers=headers,
        json={"name": "CRUD Report", "report_type": "sales", "status": "QUEUED", "parameters": {"month": "June"}},
    )
    assert report_response.status_code == 201
    report_id = report_response.json()["id"]

    update_report_response = client.put(
        f"/api/v1/database/reports/{report_id}",
        headers=headers,
        json={"status": "READY", "file_path": "/exports/crud-report.pdf"},
    )
    assert update_report_response.status_code == 200
    assert update_report_response.json()["status"] == "READY"

    planning_response = client.post(
        "/api/v1/database/planning-requests",
        headers=headers,
        json={"title": "CRUD Planning Request", "description": "Created from admin CRUD test.", "priority": "high"},
    )
    assert planning_response.status_code == 201
    planning_id = planning_response.json()["id"]

    update_planning_response = client.put(
        f"/api/v1/database/planning-requests/{planning_id}",
        headers=headers,
        json={"status": "APPROVED"},
    )
    assert update_planning_response.status_code == 200
    assert update_planning_response.json()["status"] == "APPROVED"

    audit_response = client.post(
        "/api/v1/database/audit-logs",
        headers=headers,
        json={"action": "CREATE", "entity_type": "manual_test", "entity_id": "T-001", "detail": "Manual CRUD audit entry."},
    )
    assert audit_response.status_code == 201
    audit_id = audit_response.json()["id"]

    audit_update_response = client.put(
        f"/api/v1/database/audit-logs/{audit_id}",
        headers=headers,
        json={"detail": "Updated manual CRUD audit entry."},
    )
    assert audit_update_response.status_code == 200

    assert client.delete(f"/api/v1/database/audit-logs/{audit_id}", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/database/planning-requests/{planning_id}", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/database/reports/{report_id}", headers=headers).status_code == 200
    assert client.delete(f"/api/v1/database/orders/{order_id}", headers=headers).status_code == 200


def test_granular_role_permissions_can_open_roles_tab():
    from backend.core.security import hash_password
    from backend.database import session_scope
    from backend.models import Permission, Role, User

    with session_scope() as db:
        permission = Permission(
            code="roles.read",
            name="View Roles",
            module="roles",
            description="Can view roles from admin dashboard.",
        )
        db.add(permission)
        db.flush()
        role = Role(name="Role Reader", description="Can open the Roles tab.", permissions=[permission])
        db.add(role)
        db.flush()
        db.add(
            User(
                username="role-reader@example.com",
                email="role-reader@example.com",
                hashed_password=hash_password("RoleReader123!"),
                is_verified=True,
                is_active=True,
                roles=[role],
            )
        )

    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "role-reader@example.com", "password": "RoleReader123!"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    roles_response = client.get("/api/v1/database/roles", headers=headers)
    assert roles_response.status_code == 200
    assert any(role["name"] == "Role Reader" for role in roles_response.json())


def test_customer_role_is_product_dashboard_only():
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "customer@example.com", "password": "Customer123!"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    products_response = client.get("/api/v1/shop/products", headers=headers)
    assert products_response.status_code == 200
    assert len(products_response.json()) > 0

    roles_response = client.get("/api/v1/database/roles", headers=headers)
    assert roles_response.status_code == 403
