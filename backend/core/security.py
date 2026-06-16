from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> list[str]:
    """Return password policy errors. Empty list means valid."""
    errors: list[str] = []

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


def create_jwt_token(username: str, token_type: str, expires_delta: timedelta) -> str:
    expires_at = now_utc() + expires_delta
    claims = {
        "sub": username.strip().lower(),
        "exp": expires_at,
        "type": token_type,
    }
    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, expected_type: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None

    username = payload.get("sub")
    token_type = payload.get("type")

    if not username or token_type != expected_type:
        return None

    return payload
