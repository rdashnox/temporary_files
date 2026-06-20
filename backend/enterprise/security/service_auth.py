"""Service-to-service JWT authentication.

Public user traffic still uses normal user bearer tokens. Internal service calls
must use X-Service-Token, signed with SERVICE_AUTH_SECRET.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException, status
from jose import JWTError, jwt

from ..config import enterprise_settings


def create_service_token(service_name: str, audience: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "iss": service_name,
        "sub": service_name,
        "aud": audience or "finmark-internal",
        "iat": now,
        "exp": now + timedelta(minutes=enterprise_settings.service_token_expire_minutes),
        "type": "service",
    }
    return jwt.encode(
        claims,
        enterprise_settings.service_auth_secret,
        algorithm=enterprise_settings.service_auth_algorithm,
    )


def decode_service_token(token: str, audience: str | None = None) -> dict | None:
    try:
        options = {"verify_aud": audience is not None}
        return jwt.decode(
            token,
            enterprise_settings.service_auth_secret,
            algorithms=[enterprise_settings.service_auth_algorithm],
            audience=audience,
            options=options,
        )
    except JWTError:
        return None


def require_service_token(x_service_token: str | None = Header(default=None, alias="X-Service-Token")) -> dict:
    if not x_service_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Service-Token")
    payload = decode_service_token(x_service_token)
    if not payload or payload.get("type") != "service":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")
    return payload
