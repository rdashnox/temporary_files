from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...schemas.auth import EmailRequest, PasswordResetRequest, RefreshTokenRequest, UserCreate
from ..databases import get_auth_db
from ..security.user_auth import get_current_user
from ..services import auth_enterprise_service as auth_service

router = APIRouter()


@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_auth_db)):
    try:
        token_pair = auth_service.authenticate_user(db, form_data.username, form_data.password)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not token_pair:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_pair


@router.post("/refresh")
def refresh_access_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_auth_db)):
    token_pair = auth_service.refresh_access_token(db, refresh_request.refresh_token)
    if not token_pair:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    return token_pair


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user_route(user_create: UserCreate, db: Session = Depends(get_auth_db)):
    try:
        user = auth_service.register_user(db, user_create.username, user_create.password, user_create.confirm_password)
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_409_CONFLICT if "already exists" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message) from exc
    return {
        "message": "User registered successfully. Please verify your email before logging in.",
        "username": user["username"],
        "verification_token": user["verification_token"],
        "verification_link": user["verification_link"],
    }


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_auth_db)):
    try:
        user = auth_service.verify_email(db, token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"message": "Email verified successfully. You may now log in.", "username": user["username"]}


@router.post("/resend-verification")
def resend_verification(request: EmailRequest, db: Session = Depends(get_auth_db)):
    try:
        result = auth_service.resend_verification_email(db, request.username)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "message": "Verification link generated. In production this would be emailed.",
        "username": result["username"],
        "verification_token": result["verification_token"],
        "verification_link": result["verification_link"],
    }


@router.post("/forgot-password")
def forgot_password(request: EmailRequest, db: Session = Depends(get_auth_db)):
    result = auth_service.request_password_reset(db, request.username)
    response = {"message": "If the account exists, a password reset link has been generated."}
    if result.get("reset_link"):
        response["reset_token"] = result["reset_token"]
        response["reset_link"] = result["reset_link"]
    return response


@router.post("/reset-password")
def reset_password(request: PasswordResetRequest, db: Session = Depends(get_auth_db)):
    try:
        user = auth_service.reset_password(db, request.token, request.new_password, request.confirm_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"message": "Password reset successfully. You may now log in.", "username": user["username"]}


@router.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return current_user
