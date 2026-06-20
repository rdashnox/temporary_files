from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from ..config import enterprise_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validate a user JWT without querying the Auth database.

    This is important for database-per-service architecture: Order, Inventory,
    and Notification services can authorize requests without a cross-DB join.
    Auth service embeds user id, roles, and permissions as token claims.
    """
    try:
        payload = jwt.decode(token, enterprise_settings.secret_key, algorithms=[enterprise_settings.algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": payload.get("uid"),
        "username": payload.get("sub"),
        "email": payload.get("email") or payload.get("sub"),
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", []),
        "is_active": True,
        "is_verified": True,
    }


PERMISSION_ALIASES: dict[str, set[str]] = {
    "users.manage": {"users.read", "users.create", "users.update", "users.delete"},
    "roles.manage": {"roles.read", "roles.create", "roles.update", "roles.delete"},
    "permissions.manage": {"permissions.read", "permissions.create", "permissions.update", "permissions.delete"},
    "orders.manage": {"orders.read", "orders.create", "orders.update", "orders.delete"},
    "inventory.manage": {"inventory.read", "inventory.create", "inventory.update", "inventory.delete"},
    "notifications.manage": {"notifications.read", "notifications.create", "notifications.update", "notifications.delete"},
    "reports.manage": {"reports.read", "reports.create", "reports.update", "reports.delete", "reports.generate"},
    "planning.manage": {"planning.read", "planning.create", "planning.update", "planning.delete"},
    "audit.manage": {"audit.read", "audit.create", "audit.update", "audit.delete"},
}

SUPERUSER_PERMISSIONS = {"users.manage"}
FULL_ACCESS_ROLE_NAMES = {"admin", "administrator", "super admin", "superadmin", "super user", "superuser"}


def _normalize_role_name(role) -> str:
    if isinstance(role, str):
        value = role
    elif isinstance(role, dict):
        value = role.get("name") or role.get("code") or ""
    else:
        value = getattr(role, "name", None) or getattr(role, "code", None) or ""
    return str(value).strip().lower()


def _has_full_access_role(current_user: dict) -> bool:
    return any(_normalize_role_name(role) in FULL_ACCESS_ROLE_NAMES for role in current_user.get("roles", []))


def _expand(permission: str) -> set[str]:
    expanded = {permission}
    expanded.update(PERMISSION_ALIASES.get(permission, set()))
    return expanded


def user_has_permission(current_user: dict, permission: str) -> bool:
    # Admin/Administrator roles must keep full dashboard access even if the
    # permission rows were migrated from an older database without every
    # granular order/inventory/report permission. This is especially important
    # for the Admin Manage Order List after checkout, because the Order Service
    # authorizes /api/v1/orders independently from the Auth database.
    if _has_full_access_role(current_user):
        return True

    user_permissions = {str(permission).lower() for permission in current_user.get("permissions", [])}
    if user_permissions.intersection(SUPERUSER_PERMISSIONS):
        return True
    return bool(user_permissions.intersection(_expand(permission.lower())))


def require_permission(current_user: dict, permission: str) -> None:
    if not user_has_permission(current_user, permission):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
