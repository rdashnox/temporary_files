from ..services import auth_service


def authenticate_user(username: str, password: str):
    """Authenticate a user and return signed access/refresh JWT tokens."""
    user = auth_service.verify_login(username, password)
    if not user:
        return False

    return auth_service.create_token_pair(user["username"])


def register_new_user(username: str, password: str, confirm_password: str):
    """Register a new user by calling the authentication service."""
    return auth_service.register_user(username, password, confirm_password)


def verify_user_email(token: str):
    """Verify a new user's email address."""
    return auth_service.verify_email(token)


def resend_user_verification(username: str):
    """Regenerate a verification token for an unverified user."""
    return auth_service.resend_verification_email(username)


def request_password_reset(username: str):
    """Request a password reset link/token."""
    return auth_service.request_password_reset(username)


def reset_password(token: str, new_password: str, confirm_password: str):
    """Reset the user's password with a valid reset token."""
    return auth_service.reset_password(token, new_password, confirm_password)


def refresh_tokens(refresh_token: str):
    """Return a fresh token pair from a valid refresh token."""
    return auth_service.refresh_access_token(refresh_token)


def get_current_user_from_token(token: str):
    """Validate a JWT access token and return the authenticated user."""
    payload = auth_service.decode_access_token(token)
    if not payload:
        return None

    user = auth_service.get_user_by_username(payload["sub"])
    if not user or not user.get("is_verified"):
        return None

    return user
