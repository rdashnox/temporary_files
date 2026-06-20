from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..databases import get_auth_db, get_inventory_db, get_notification_db, get_order_db
from ...schemas.database_entities import OrderCreate, OrderUpdate
from ..models import (
    AuthAuditLog,
    AuthPermission,
    AuthRole,
    AuthUser,
    InventoryProduct,
    NotificationEntity,
    OrderEntity,
)
from ..security.user_auth import get_current_user, require_permission, user_has_permission
from ..services import order_enterprise_service as order_service

router = APIRouter()


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _paginate(query, *, limit: int, offset: int, search: str | None = None, search_columns: tuple = ()):  # noqa: ANN001
    if search and search_columns:
        pattern = f"%{search.strip()}%"
        from sqlalchemy import or_

        query = query.where(or_(*[column.ilike(pattern) for column in search_columns]))
    return query.limit(limit).offset(offset)


def _role_to_dict(role: AuthRole) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "permissions": [permission.code for permission in role.permissions],
    }


def _permission_to_dict(permission: AuthPermission) -> dict:
    return {
        "id": permission.id,
        "code": permission.code,
        "name": permission.name,
        "module": permission.module,
        "description": permission.description,
    }


def _user_to_dict(user: AuthUser) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "roles": [role.name for role in user.roles if role.is_active],
        "permissions": sorted({permission.code for role in user.roles for permission in role.permissions if role.is_active}),
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }


@router.get("/me")
def read_current_database_user(current_user: dict = Depends(get_current_user)):
    """Compatibility endpoint used by the React frontend after login.

    In the full enterprise system, the Auth Service owns the session/user identity.
    This endpoint preserves the old /database/me frontend contract while still
    returning JWT claims from the Auth microservice.
    """
    return current_user


@router.get("/summary")
def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    auth_db: Session = Depends(get_auth_db),
    order_db: Session = Depends(get_order_db),
    inventory_db: Session = Depends(get_inventory_db),
    notification_db: Session = Depends(get_notification_db),
):
    summary = {
        "users": _count(auth_db, AuthUser),
        "roles": _count(auth_db, AuthRole),
        "permissions": _count(auth_db, AuthPermission),
        "audit-logs": _count(auth_db, AuthAuditLog),
        "orders": _count(order_db, OrderEntity),
        "products": _count(inventory_db, InventoryProduct),
        "notifications": _count(notification_db, NotificationEntity),
        "reports": 0,
        "planning-requests": 0,
    }
    permission_map = {
        "users": "users.read",
        "roles": "roles.read",
        "permissions": "permissions.read",
        "audit-logs": "audit.read",
        "orders": "orders.read",
        "products": "inventory.read",
        "notifications": "notifications.read",
        "reports": "reports.read",
        "planning-requests": "planning.read",
    }
    return {key: value for key, value in summary.items() if user_has_permission(current_user, permission_map.get(key, key))}


@router.get("/users")
def list_users(
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_auth_db),
):
    require_permission(current_user, "users.read")
    query = select(AuthUser).order_by(AuthUser.id)
    query = _paginate(query, limit=limit, offset=offset, search=search, search_columns=(AuthUser.username, AuthUser.email, AuthUser.full_name))
    return [_user_to_dict(user) for user in db.scalars(query).all()]


@router.get("/roles")
def list_roles(
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_auth_db),
):
    require_permission(current_user, "roles.read")
    query = select(AuthRole).order_by(AuthRole.id)
    query = _paginate(query, limit=limit, offset=offset, search=search, search_columns=(AuthRole.name, AuthRole.description))
    return [_role_to_dict(role) for role in db.scalars(query).all()]


@router.get("/permissions")
def list_permissions(
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_auth_db),
):
    require_permission(current_user, "permissions.read")
    query = select(AuthPermission).order_by(AuthPermission.id)
    query = _paginate(query, limit=limit, offset=offset, search=search, search_columns=(AuthPermission.code, AuthPermission.name, AuthPermission.module))
    return [_permission_to_dict(permission) for permission in db.scalars(query).all()]

@router.get("/orders")
@router.get("/orders/", include_in_schema=False)
def list_orders_compat(
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    """Compatibility endpoint for the Admin CRUD dashboard.

    Checkout writes orders to the dedicated Order Service database through
    /api/v1/orders/checkout. Older admin screens requested /api/v1/database/orders.
    Keep that route working, but read from finmark_order_db so newly checked-out
    orders appear immediately in Manage Order List.
    """
    require_permission(current_user, "orders.read")
    return order_service.list_orders(db, limit=limit, offset=offset, search=search)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
@router.post("/orders/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_order_compat(
    order_create: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    require_permission(current_user, "orders.manage")
    return order_service.create_order(db, order_create, current_user)




@router.get("/orders/debug/summary")
@router.get("/orders/debug-summary", include_in_schema=False)
def order_debug_summary_compat(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    """Compatibility diagnostic endpoint for Admin Order List checks.

    Some local setups still probe /api/v1/database/orders/debug/summary. Keep it
    wired to the dedicated Order DB so the diagnostic script works across older
    and newer frontend/gateway builds.
    """
    require_permission(current_user, "orders.read")
    latest = db.scalar(select(OrderEntity).order_by(OrderEntity.created_at.desc()).limit(1))
    return {
        "status": "ok",
        "service": "database-compat-order-service",
        "database": "finmark_order_db",
        "table": "order_orders",
        "total_orders": int(db.scalar(select(func.count()).select_from(OrderEntity)) or 0),
        "latest_order": order_service.order_to_dict(latest) if latest else None,
        "message": "Compatibility debug route reads from the dedicated Order DB.",
    }



@router.get("/orders/latest")
@router.get("/orders/latest/", include_in_schema=False)
def latest_orders_compat(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    require_permission(current_user, "orders.read")
    return order_service.list_orders(db, limit=limit, offset=0)


@router.get("/orders/{order_id}")
def get_order_compat(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    require_permission(current_user, "orders.read")
    return order_service.get_order(db, order_id)


@router.put("/orders/{order_id}")
@router.patch("/orders/{order_id}", include_in_schema=False)
def update_order_compat(
    order_id: int,
    order_update: OrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    require_permission(current_user, "orders.manage")
    return order_service.update_order(db, order_id, order_update, current_user)


@router.delete("/orders/{order_id}")
def delete_order_compat(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_order_db),
):
    require_permission(current_user, "orders.manage")
    return order_service.delete_order(db, order_id, current_user)

