from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.security import hash_password, validate_password_strength, verify_password
from ..config import enterprise_settings
from ..models import AuditAction, AuthAuditLog, AuthPermission, AuthRole, AuthUser


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < now_utc()


def _frontend_link(path: str, token: str) -> str:
    return f"{enterprise_settings.frontend_base_url.rstrip('/')}/{path}?token={token}"


def _audit(db: Session, user: AuthUser | None, action: AuditAction, entity_type: str, entity_id: str | None, detail: str):
    db.add(
        AuthAuditLog(
            actor_user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
        )
    )


def safe_user(user: AuthUser) -> dict:
    permissions = sorted(
        {
            permission.code
            for role in user.roles
            for permission in role.permissions
            if role.is_active
        }
    )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "roles": [role.name for role in user.roles if role.is_active],
        "permissions": permissions,
    }


def get_user_model_by_username(db: Session, username: str) -> AuthUser | None:
    normalized = _normalize_username(username)
    return db.scalar(select(AuthUser).where(or_(AuthUser.username == normalized, AuthUser.email == normalized)))


def get_user_by_username(db: Session, username: str) -> Optional[dict]:
    user = get_user_model_by_username(db, username)
    return safe_user(user) if user else None


def _default_role(db: Session) -> AuthRole:
    role = db.scalar(select(AuthRole).where(AuthRole.name == "Staff"))
    if role is None:
        role = AuthRole(name="Staff", description="Default customer/staff role")
        db.add(role)
        db.flush()
    return role


def _create_verification_token(user: AuthUser) -> str:
    token = token_urlsafe(32)
    user.verification_token = token
    user.verification_token_expires_at = now_utc() + timedelta(minutes=enterprise_settings.email_token_expire_minutes)
    return token


def _create_password_reset_token(user: AuthUser) -> str:
    token = token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_token_expires_at = now_utc() + timedelta(minutes=enterprise_settings.password_reset_token_expire_minutes)
    return token


def register_user(db: Session, username: str, password: str, confirm_password: str) -> dict:
    normalized = _normalize_username(username)
    if get_user_model_by_username(db, normalized):
        raise ValueError("User already exists")
    if password != confirm_password:
        raise ValueError("Passwords do not match")
    errors = validate_password_strength(password)
    if errors:
        raise ValueError(" ".join(errors))

    user = AuthUser(
        username=normalized,
        email=normalized,
        hashed_password=hash_password(password),
        is_verified=False,
        is_active=True,
        roles=[_default_role(db)],
    )
    db.add(user)
    try:
        db.flush()
        token = _create_verification_token(user)
        _audit(db, user, AuditAction.CREATE, "auth_users", str(user.id), "User registered.")
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("User already exists") from exc

    return {
        "username": normalized,
        "verification_token": token,
        "verification_link": _frontend_link("verify-email.html", token),
    }


def verify_email(db: Session, token: str) -> dict:
    user = db.scalar(select(AuthUser).where(AuthUser.verification_token == token))
    if not user:
        raise ValueError("Invalid verification token")
    if _is_expired(user.verification_token_expires_at):
        raise ValueError("Verification link has expired")
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    _audit(db, user, AuditAction.VERIFY_EMAIL, "auth_users", str(user.id), "Email verified.")
    db.commit()
    db.refresh(user)
    return safe_user(user)


def resend_verification_email(db: Session, username: str) -> dict:
    user = get_user_model_by_username(db, username)
    if not user:
        raise ValueError("User not found")
    if user.is_verified:
        raise ValueError("User is already verified")
    token = _create_verification_token(user)
    db.commit()
    return {
        "username": user.username,
        "verification_token": token,
        "verification_link": _frontend_link("verify-email.html", token),
    }


def request_password_reset(db: Session, username: str) -> dict:
    user = get_user_model_by_username(db, username)
    if not user or not user.is_active:
        return {"username": _normalize_username(username), "reset_token": None, "reset_link": None}
    token = _create_password_reset_token(user)
    db.commit()
    return {"username": user.username, "reset_token": token, "reset_link": _frontend_link("reset-password.html", token)}


def reset_password(db: Session, token: str, new_password: str, confirm_password: str) -> dict:
    if new_password != confirm_password:
        raise ValueError("Passwords do not match")
    errors = validate_password_strength(new_password)
    if errors:
        raise ValueError(" ".join(errors))
    user = db.scalar(select(AuthUser).where(AuthUser.password_reset_token == token))
    if not user:
        raise ValueError("Invalid password reset token")
    if _is_expired(user.password_reset_token_expires_at):
        raise ValueError("Password reset link has expired")
    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_token_expires_at = None
    _audit(db, user, AuditAction.PASSWORD_RESET, "auth_users", str(user.id), "Password reset.")
    db.commit()
    db.refresh(user)
    return safe_user(user)


def create_jwt_token(username: str, token_type: str, expires_delta: timedelta, extra_claims: dict | None = None) -> str:
    expires_at = now_utc() + expires_delta
    claims = {"sub": _normalize_username(username), "exp": expires_at, "type": token_type}
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, enterprise_settings.secret_key, algorithm=enterprise_settings.algorithm)


def decode_token(token: str, expected_type: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, enterprise_settings.secret_key, algorithms=[enterprise_settings.algorithm])
    except JWTError:
        return None
    if payload.get("type") != expected_type or not payload.get("sub"):
        return None
    return payload


def create_token_pair(username_or_user) -> dict:
    if isinstance(username_or_user, dict):
        username = username_or_user["username"]
        access_claims = {
            "uid": username_or_user.get("id"),
            "email": username_or_user.get("email"),
            "roles": username_or_user.get("roles", []),
            "permissions": username_or_user.get("permissions", []),
        }
    else:
        username = str(username_or_user)
        access_claims = {}

    return {
        "access_token": create_jwt_token(
            username,
            "access",
            timedelta(minutes=enterprise_settings.access_token_expire_minutes),
            access_claims,
        ),
        "refresh_token": create_jwt_token(
            username,
            "refresh",
            timedelta(days=enterprise_settings.refresh_token_expire_days),
        ),
        "token_type": "bearer",
    }


def verify_login(db: Session, username: str, password: str) -> Optional[dict]:
    user = get_user_model_by_username(db, username)
    if not user or not user.is_active:
        return None
    if not user.is_verified:
        raise PermissionError("Please verify your email before logging in.")
    if not verify_password(password, user.hashed_password):
        return None
    user.last_login_at = now_utc()
    _audit(db, user, AuditAction.LOGIN, "auth_users", str(user.id), "User logged in.")
    db.commit()
    db.refresh(user)
    return safe_user(user)


def authenticate_user(db: Session, username: str, password: str):
    user = verify_login(db, username, password)
    return create_token_pair(user) if user else False


def refresh_access_token(db: Session, refresh_token: str) -> Optional[dict]:
    payload = decode_token(refresh_token, "refresh")
    if not payload:
        return None
    user = get_user_by_username(db, payload["sub"])
    if not user or not user.get("is_verified") or not user.get("is_active"):
        return None
    return create_token_pair(user)


def user_from_access_token(db: Session, token: str) -> Optional[dict]:
    payload = decode_token(token, "access")
    if not payload:
        return None
    user = get_user_by_username(db, payload["sub"])
    if not user or not user.get("is_verified") or not user.get("is_active"):
        return None
    return user


def seed_auth_database(db: Session) -> None:
    permission_specs = [
        ("users.read", "Read users", "auth"),
        ("users.manage", "Manage users", "auth"),
        ("roles.read", "Read roles", "auth"),
        ("roles.manage", "Manage roles", "auth"),
        ("permissions.read", "Read permissions", "auth"),
        ("permissions.manage", "Manage permissions", "auth"),
        ("orders.read", "Read orders", "order"),
        ("orders.manage", "Manage orders", "order"),
        ("inventory.read", "Read inventory", "inventory"),
        ("inventory.manage", "Manage inventory", "inventory"),
        ("products.read", "Read products", "inventory"),
        ("products.manage", "Manage products", "inventory"),
        ("dashboard.admin", "Open Admin Dashboard", "dashboard"),
        ("dashboard.products", "Open Product Dashboard", "dashboard"),
        ("product_dashboard.access", "Access Product Dashboard", "dashboard"),
        ("notifications.read", "Read notifications", "notification"),
        ("notifications.manage", "Manage notifications", "notification"),
        ("reports.read", "Read reports", "report"),
        ("reports.manage", "Manage reports", "report"),
        ("planning.read", "Read planning requests", "planning"),
        ("planning.manage", "Manage planning requests", "planning"),
        ("audit.read", "Read audit logs", "audit"),
        ("audit.manage", "Manage audit logs", "audit"),
    ]
    permissions: dict[str, AuthPermission] = {}
    for code, name, module in permission_specs:
        permission = db.scalar(select(AuthPermission).where(AuthPermission.code == code))
        if permission is None:
            permission = AuthPermission(code=code, name=name, module=module)
            db.add(permission)
            db.flush()
        permissions[code] = permission

    admin_role = db.scalar(select(AuthRole).where(AuthRole.name == "Administrator"))
    if admin_role is None:
        admin_role = AuthRole(name="Administrator", description="Full system administrator")
        db.add(admin_role)
        db.flush()
    admin_role.permissions = list(permissions.values())

    staff_role = db.scalar(select(AuthRole).where(AuthRole.name == "Staff"))
    if staff_role is None:
        staff_role = AuthRole(name="Staff", description="Default staff/customer role")
        db.add(staff_role)
        db.flush()
    staff_role.permissions = [
        permissions["orders.read"],
        permissions["inventory.read"],
        permissions["products.read"],
        permissions["dashboard.products"],
        permissions["notifications.read"],
    ]

    admin = get_user_model_by_username(db, "admin@example.com")
    if admin is None:
        admin = AuthUser(
            username="admin@example.com",
            email="admin@example.com",
            full_name="System Administrator",
            hashed_password=hash_password("Admin@12345"),
            is_active=True,
            is_verified=True,
            roles=[admin_role],
        )
        db.add(admin)
    else:
        # Classroom/demo repair: repeated project updates reuse the same MySQL DB.
        # If an older seed left a different password hash or unverified account,
        # login with the documented demo credentials would fail. Keep this account
        # deterministic for local defense/demo use.
        admin.username = "admin@example.com"
        admin.email = "admin@example.com"
        admin.full_name = admin.full_name or "System Administrator"
        admin.hashed_password = hash_password("Admin@12345")
        admin.is_active = True
        admin.is_verified = True
        admin.verification_token = None
        admin.verification_token_expires_at = None
        if admin_role not in admin.roles:
            admin.roles.append(admin_role)
    db.commit()
