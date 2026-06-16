from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import (
    create_jwt_token,
    decode_token,
    hash_password,
    now_utc,
    validate_password_strength,
    verify_password,
)
from ..models import AuditAction, Role, User
from .audit_service import create_audit_log


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < now_utc()


def _build_frontend_link(path: str, token: str) -> str:
    base_url = settings.frontend_base_url.rstrip("/")
    return f"{base_url}/{path}?token={token}"


def safe_user(user: User) -> dict:
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


def get_user_model_by_username(db: Session, username: str) -> User | None:
    normalized_username = _normalize_username(username)
    return db.scalar(
        select(User).where(
            or_(User.username == normalized_username, User.email == normalized_username)
        )
    )


def _get_default_role(db: Session) -> Role:
    role = db.scalar(select(Role).where(Role.name == "Staff"))
    if role is None:
        role = Role(name="Staff", description="Default staff role")
        db.add(role)
        db.flush()
    return role


def _create_email_verification_token(db: Session, user: User) -> str:
    token = token_urlsafe(32)
    user.verification_token = token
    user.verification_token_expires_at = now_utc() + timedelta(
        minutes=settings.email_token_expire_minutes
    )
    db.flush()
    return token


def _create_password_reset_token(db: Session, user: User) -> str:
    token = token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_token_expires_at = now_utc() + timedelta(
        minutes=settings.password_reset_token_expire_minutes
    )
    db.flush()
    return token


def verify_login(db: Session, username: str, password: str) -> Optional[dict]:
    """Verify credentials against the database using bcrypt hashes."""
    user = get_user_model_by_username(db, username)

    if not user or not user.is_active:
        return None

    if not user.is_verified:
        raise PermissionError("Please verify your email before logging in.")

    if not verify_password(password, user.hashed_password):
        return None

    user.last_login_at = now_utc()
    create_audit_log(
        db,
        actor=user,
        action=AuditAction.LOGIN,
        entity_type="users",
        entity_id=str(user.id),
        detail="User logged in successfully.",
    )
    db.commit()
    db.refresh(user)
    return safe_user(user)


def register_user(db: Session, username: str, password: str, confirm_password: str) -> dict:
    """Register a new user with a bcrypt-hashed password and DB-backed token."""
    normalized_username = _normalize_username(username)

    if get_user_model_by_username(db, normalized_username):
        raise ValueError("User already exists")

    if password != confirm_password:
        raise ValueError("Passwords do not match")

    password_errors = validate_password_strength(password)
    if password_errors:
        raise ValueError(" ".join(password_errors))

    user = User(
        username=normalized_username,
        email=normalized_username,
        hashed_password=hash_password(password),
        is_verified=False,
        is_active=True,
        roles=[_get_default_role(db)],
    )
    db.add(user)

    try:
        db.flush()
        verification_token = _create_email_verification_token(db, user)
        create_audit_log(
            db,
            actor=user,
            action=AuditAction.CREATE,
            entity_type="users",
            entity_id=str(user.id),
            detail="User registered and verification token generated.",
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("User already exists") from exc

    return {
        "username": normalized_username,
        "verification_token": verification_token,
        "verification_link": _build_frontend_link("verify-email.html", verification_token),
    }


def verify_email(db: Session, token: str) -> dict:
    user = db.scalar(select(User).where(User.verification_token == token))

    if not user:
        raise ValueError("Invalid verification token")

    if _is_expired(user.verification_token_expires_at):
        raise ValueError("Verification link has expired")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    create_audit_log(
        db,
        actor=user,
        action=AuditAction.VERIFY_EMAIL,
        entity_type="users",
        entity_id=str(user.id),
        detail="User verified email address.",
    )
    db.commit()
    db.refresh(user)
    return safe_user(user)


def resend_verification_email(db: Session, username: str) -> dict:
    normalized_username = _normalize_username(username)
    user = get_user_model_by_username(db, normalized_username)

    if not user:
        raise ValueError("User not found")
    if user.is_verified:
        raise ValueError("User is already verified")

    token = _create_email_verification_token(db, user)
    db.commit()
    return {
        "username": normalized_username,
        "verification_token": token,
        "verification_link": _build_frontend_link("verify-email.html", token),
    }


def request_password_reset(db: Session, username: str) -> dict:
    normalized_username = _normalize_username(username)
    user = get_user_model_by_username(db, normalized_username)

    # Avoid account enumeration: public message stays generic in the route.
    if not user or not user.is_active:
        return {"username": normalized_username, "reset_token": None, "reset_link": None}

    token = _create_password_reset_token(db, user)
    db.commit()
    return {
        "username": normalized_username,
        "reset_token": token,
        "reset_link": _build_frontend_link("reset-password.html", token),
    }


def reset_password(db: Session, token: str, new_password: str, confirm_password: str) -> dict:
    if new_password != confirm_password:
        raise ValueError("Passwords do not match")

    password_errors = validate_password_strength(new_password)
    if password_errors:
        raise ValueError(" ".join(password_errors))

    user = db.scalar(select(User).where(User.password_reset_token == token))

    if not user:
        raise ValueError("Invalid password reset token")

    if _is_expired(user.password_reset_token_expires_at):
        raise ValueError("Password reset link has expired")

    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_token_expires_at = None
    create_audit_log(
        db,
        actor=user,
        action=AuditAction.PASSWORD_RESET,
        entity_type="users",
        entity_id=str(user.id),
        detail="User reset password successfully.",
    )
    db.commit()
    db.refresh(user)
    return safe_user(user)


def create_access_token(username: str) -> str:
    return create_jwt_token(
        _normalize_username(username),
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(username: str) -> str:
    return create_jwt_token(
        _normalize_username(username),
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_access_token(token: str) -> Optional[dict]:
    return decode_token(token, "access")


def decode_refresh_token(token: str) -> Optional[dict]:
    return decode_token(token, "refresh")


def create_token_pair(username: str) -> dict:
    return {
        "access_token": create_access_token(username),
        "refresh_token": create_refresh_token(username),
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, refresh_token: str) -> Optional[dict]:
    payload = decode_refresh_token(refresh_token)
    if not payload:
        return None

    user = get_user_by_username(db, payload["sub"])
    if not user or not user.get("is_verified") or not user.get("is_active"):
        return None

    return create_token_pair(user["username"])


def get_user_by_username(db: Session, username: str) -> Optional[dict]:
    user = get_user_model_by_username(db, username)
    if not user:
        return None
    return safe_user(user)
