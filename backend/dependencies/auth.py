from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..controllers import auth_controller
from ..database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Validate the bearer token and return the current verified user."""
    user = auth_controller.get_current_user_from_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or unverified access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permission(current_user: dict, permission: str) -> None:
    permissions = set(current_user.get("permissions", []))
    if permission not in permissions and "users.manage" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission}",
        )
