from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _required_text(value: str | None, field_name: str) -> str:
    cleaned = _clean_optional(value)
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


class NotificationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: int | None = None
    title: str = Field(..., min_length=3, max_length=160)
    message: str = Field(..., min_length=3, max_length=1000)
    channel: str = Field(default="in_app", max_length=40)
    entity_type: str | None = Field(default=None, max_length=80)
    entity_id: str | None = Field(default=None, max_length=80)

    @field_validator("title", "message")
    @classmethod
    def required_text(cls, value: str, info):
        return _required_text(value, info.field_name.replace("_", " ").title())

    @field_validator("channel")
    @classmethod
    def valid_channel(cls, value: str):
        cleaned = _required_text(value, "Channel")
        if cleaned not in {"in_app", "email", "sms", "webhook"}:
            raise ValueError("Invalid channel. Allowed values: in_app, email, sms, webhook.")
        return cleaned

    @field_validator("entity_type", "entity_id")
    @classmethod
    def clean_optional_text(cls, value: str | None):
        return _clean_optional(value)


class NotificationUpdate(BaseModel):
    is_read: bool = True


class IntegrationEventRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: str = Field(..., min_length=8, max_length=120)
    event_type: str = Field(..., min_length=3, max_length=120)
    aggregate_type: str | None = Field(default=None, max_length=80)
    aggregate_id: str | None = Field(default=None, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id", "event_type")
    @classmethod
    def required_event_text(cls, value: str, info):
        return _required_text(value, info.field_name.replace("_", " ").title())

    @field_validator("aggregate_type", "aggregate_id")
    @classmethod
    def clean_event_optional(cls, value: str | None):
        return _clean_optional(value)
