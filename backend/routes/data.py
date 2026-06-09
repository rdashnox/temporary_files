from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

@router.get("/protected")
async def read_protected_data(token: str = Depends(oauth2_scheme)):
    """
    Retrieves protected data, requiring a valid authentication token.
    The presence of any token in the Authorization header grants access for this prototype.
    """
    # For a real application, token validation (e.g., JWT signature, expiration)
    # would be implemented here or in a dependency.
    return {"message": "This is protected data!", "your_token_was": token}
