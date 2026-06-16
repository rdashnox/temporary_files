from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory store for demonstration purposes only.
# A real application should replace this with a database table.
_IN_MEMORY_USERS = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> list[str]:
    """Return a list of password policy errors. Empty list means the password is valid."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not any(char.islower() for char in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one number.")
    if not any(not char.isalnum() for char in password):
        errors.append("Password must contain at least one special character.")

    return errors


def _build_frontend_link(path: str, token: str) -> str:
    base_url = settings.frontend_base_url.rstrip("/")
    return f"{base_url}/{path}?token={token}"


def _create_email_verification_token(username: str) -> str:
    token = token_urlsafe(32)
    user = _IN_MEMORY_USERS[_normalize_username(username)]
    user["verification_token"] = token
    user["verification_token_expires_at"] = _now() + timedelta(
        minutes=settings.email_token_expire_minutes
    )
    return token


def _create_password_reset_token(username: str) -> str:
    token = token_urlsafe(32)
    user = _IN_MEMORY_USERS[_normalize_username(username)]
    user["password_reset_token"] = token
    user["password_reset_token_expires_at"] = _now() + timedelta(
        minutes=settings.password_reset_token_expire_minutes
    )
    return token


def _seed_demo_user() -> None:
    """Create a verified demo user without storing a plain-text password."""
    demo_username = "user@example.com"
    if demo_username not in _IN_MEMORY_USERS:
        _IN_MEMORY_USERS[demo_username] = {
            "username": demo_username,
            "hashed_password": hash_password("Password123!"),
            "is_verified": True,
            "verification_token": None,
            "verification_token_expires_at": None,
            "password_reset_token": None,
            "password_reset_token_expires_at": None,
        }


_seed_demo_user()


def verify_login(username: str, password: str) -> Optional[dict]:
    """
    Verify user credentials against the in-memory user store.
    Passwords are checked using bcrypt hashes, not plain-text comparison.
    """
    normalized_username = _normalize_username(username)
    user = _IN_MEMORY_USERS.get(normalized_username)

    if not user:
        return None

    if not user.get("is_verified"):
        raise PermissionError("Please verify your email before logging in.")

    if not verify_password(password, user["hashed_password"]):
        return None

    return {"username": user["username"]}


def register_user(username: str, password: str, confirm_password: str) -> dict:
    """
    Register a new user with a bcrypt-hashed password and verification token.
    """
    normalized_username = _normalize_username(username)

    if normalized_username in _IN_MEMORY_USERS:
        raise ValueError("User already exists")

    if password != confirm_password:
        raise ValueError("Passwords do not match")

    password_errors = validate_password_strength(password)
    if password_errors:
        raise ValueError(" ".join(password_errors))

    _IN_MEMORY_USERS[normalized_username] = {
        "username": normalized_username,
        "hashed_password": hash_password(password),
        "is_verified": False,
        "verification_token": None,
        "verification_token_expires_at": None,
        "password_reset_token": None,
        "password_reset_token_expires_at": None,
    }

    verification_token = _create_email_verification_token(normalized_username)

    # Do not return password hashes to controllers/routes.
    return {
        "username": normalized_username,
        "verification_token": verification_token,
        "verification_link": _build_frontend_link("verify-email.html", verification_token),
    }


def verify_email(token: str) -> dict:
    """Mark a user as verified if the email verification token is valid."""
    for user in _IN_MEMORY_USERS.values():
        if user.get("verification_token") != token:
            continue

        expires_at = user.get("verification_token_expires_at")
        if not expires_at or expires_at < _now():
            raise ValueError("Verification link has expired")

        user["is_verified"] = True
        user["verification_token"] = None
        user["verification_token_expires_at"] = None
        return {"username": user["username"]}

    raise ValueError("Invalid verification token")


def resend_verification_email(username: str) -> dict:
    """Create a new verification token for an unverified account."""
    normalized_username = _normalize_username(username)
    user = _IN_MEMORY_USERS.get(normalized_username)

    if not user:
        raise ValueError("User not found")
    if user.get("is_verified"):
        raise ValueError("User is already verified")

    token = _create_email_verification_token(normalized_username)
    return {
        "username": normalized_username,
        "verification_token": token,
        "verification_link": _build_frontend_link("verify-email.html", token),
    }


def request_password_reset(username: str) -> dict:
    """
    Create a reset token for an account.
    Demo note: returns a link so the flow can be tested without an email provider.
    """
    normalized_username = _normalize_username(username)
    user = _IN_MEMORY_USERS.get(normalized_username)

    # Avoid account enumeration: public message stays generic in the route.
    if not user:
        return {"username": normalized_username, "reset_token": None, "reset_link": None}

    token = _create_password_reset_token(normalized_username)
    return {
        "username": normalized_username,
        "reset_token": token,
        "reset_link": _build_frontend_link("reset-password.html", token),
    }


def reset_password(token: str, new_password: str, confirm_password: str) -> dict:
    """Reset a user's password if the reset token is valid and the new password is strong."""
    if new_password != confirm_password:
        raise ValueError("Passwords do not match")

    password_errors = validate_password_strength(new_password)
    if password_errors:
        raise ValueError(" ".join(password_errors))

    for user in _IN_MEMORY_USERS.values():
        if user.get("password_reset_token") != token:
            continue

        expires_at = user.get("password_reset_token_expires_at")
        if not expires_at or expires_at < _now():
            raise ValueError("Password reset link has expired")

        user["hashed_password"] = hash_password(new_password)
        user["password_reset_token"] = None
        user["password_reset_token_expires_at"] = None
        return {"username": user["username"]}

    raise ValueError("Invalid password reset token")


def _create_jwt_token(username: str, token_type: str, expires_delta: timedelta) -> str:
    expires_at = _now() + expires_delta
    claims = {
        "sub": _normalize_username(username),
        "exp": expires_at,
        "type": token_type,
    }
    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(username: str) -> str:
    """Create a signed JWT access token using python-jose."""
    return _create_jwt_token(
        username,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(username: str) -> str:
    """Create a signed JWT refresh token using python-jose."""
    return _create_jwt_token(
        username,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> Optional[dict]:
    """Decode and validate a signed JWT token by token type."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        return None

    username = payload.get("sub")
    token_type = payload.get("type")

    if not username or token_type != expected_type:
        return None

    return payload


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


def refresh_access_token(refresh_token: str) -> Optional[dict]:
    payload = decode_refresh_token(refresh_token)
    if not payload:
        return None

    user = get_user_by_username(payload["sub"])
    if not user:
        return None

    return create_token_pair(user["username"])


def get_user_by_username(username: str) -> Optional[dict]:
    """Return safe user data for an existing username."""
    normalized_username = _normalize_username(username)
    user = _IN_MEMORY_USERS.get(normalized_username)

    if not user:
        return None

    return {
        "username": user["username"],
        "is_verified": user.get("is_verified", False),
    }
