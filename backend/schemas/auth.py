from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class EmailRequest(BaseModel):
    username: EmailStr


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class PasswordResetRequest(BaseModel):
    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
