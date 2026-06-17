from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..controllers import auth_controller
from ..database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Validate the bearer token and return the current verified user."""
    user = auth_controller.get_current_user_from_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or unverified access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Backward-compatible aliases for older backend code and newer granular SQL seeds.
# Example: old code may ask for roles.manage, while the latest seed grants
# roles.create / roles.update / roles.delete. Both styles should work.
PERMISSION_ALIASES: dict[str, set[str]] = {
    "users.manage": {"users.create", "users.update", "users.delete"},
    "roles.manage": {"roles.create", "roles.update", "roles.delete"},
    "permissions.manage": {"permissions.create", "permissions.update", "permissions.delete"},
    "orders.manage": {"orders.create", "orders.update", "orders.delete"},
    "reports.manage": {"reports.create", "reports.update", "reports.delete", "reports.generate"},
    "planning.manage": {"planning.create", "planning.update", "planning.delete", "planning.approve", "planning.reject", "planning_requests.create", "planning_requests.update", "planning_requests.delete", "planning_requests.approve", "planning_requests.reject"},
    "planning.read": {"planning_requests.read"},
    "audit.read": {"audit_logs.read"},
    "audit.manage": {"audit_logs.create", "audit_logs.update", "audit_logs.delete"},
}

SUPERUSER_PERMISSIONS = {"users.manage", "users.create", "users.update", "users.delete"}


def _expand_permission(permission: str) -> set[str]:
    expanded = {permission}
    expanded.update(PERMISSION_ALIASES.get(permission, set()))
    return expanded


def user_has_permission(current_user: dict, permission: str) -> bool:
    """Return True if the user has the requested permission or a compatible alias."""
    user_permissions = set(current_user.get("permissions", []))
    if user_permissions.intersection(SUPERUSER_PERMISSIONS):
        return True
    return bool(user_permissions.intersection(_expand_permission(permission)))


def require_permission(current_user: dict, permission: str) -> None:
    if not user_has_permission(current_user, permission):
        allowed = sorted(_expand_permission(permission))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission}. Accepted permissions: {', '.join(allowed)}",
        )


def require_any_permission(current_user: dict, permissions: list[str] | tuple[str, ...]) -> None:
    if any(user_has_permission(current_user, permission) for permission in permissions):
        return
    readable = ", ".join(permissions)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Missing permission. One of these is required: {readable}",
    )
