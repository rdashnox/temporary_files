from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,128}$")


def _not_blank(value: str, field_name: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} is required.")
    return str(value)


def _validate_password_strength(value: str) -> str:
    if not PASSWORD_PATTERN.match(value or ""):
        raise ValueError("Password must be 8-128 characters and include uppercase, lowercase, number, and special character.")
    return value


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password", "confirm_password")
    @classmethod
    def passwords_not_blank(cls, value: str, info):
        value = _not_blank(value, info.field_name.replace("_", " ").title())
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class EmailRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: EmailStr


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    refresh_token: str = Field(..., min_length=20)

    @field_validator("refresh_token")
    @classmethod
    def refresh_token_not_blank(cls, value: str):
        return _not_blank(value, "Refresh token")


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("token")
    @classmethod
    def token_not_blank(cls, value: str):
        return _not_blank(value, "Password reset token")

    @field_validator("new_password", "confirm_password")
    @classmethod
    def reset_password_not_blank(cls, value: str, info):
        value = _not_blank(value, info.field_name.replace("_", " ").title())
        return _validate_password_strength(value)

    @model_validator(mode="after")
    def reset_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
