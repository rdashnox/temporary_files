from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import User


class EntityNotFound(HTTPException):
    """Standard 404 exception for domain services."""

    def __init__(self, entity: str, entity_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity} with id {entity_id} was not found.",
        )


def enum_from_input(enum_cls, value: str | None, default=None):
    """Map API strings such as PAID or paid to the matching Enum member."""
    if value is None:
        return default
    cleaned = value.strip()
    if not cleaned:
        return default
    upper_value = cleaned.upper()
    lower_value = cleaned.lower()
    if upper_value in enum_cls.__members__:
        return enum_cls[upper_value]
    for member in enum_cls:
        if member.value.lower() == lower_value:
            return member
    allowed = ", ".join(member.name for member in enum_cls)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid status/action '{value}'. Allowed values: {allowed}.",
    )


def enum_to_api(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "name"):
        return value.name
    return str(value).upper()


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def money(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def actor_from_current_user(db: Session, current_user: dict | None) -> User | None:
    if not current_user or not current_user.get("id"):
        return None
    return db.get(User, current_user["id"])


def paginate(statement, limit: int, offset: int):
    return statement.offset(offset).limit(limit)
