#
# Assigned to: Franze
# Task: Backend Task 4 - Implement Protected Endpoint (Routes & Controller)
#
# Description:
# This task involves implementing a new FastAPI endpoint that demonstrates how to protect resources
# using an authentication token.
#
# Deliverables:
# 1. Create a new GET endpoint (e.g., `/protected`) under this router. This has already been done as a placeholder.
# 2. This endpoint should:
#    - Utilize FastAPI's dependency injection (`token: str = Depends(oauth2_scheme)`) to require an `Authorization`
#      header with a Bearer token.
#    - For this prototype, simply check if *any* token is present (you do not need to validate its content yet).
#      The `Depends(oauth2_scheme)` will handle the initial check for token presence and format.
#    - If a token is successfully extracted, return a dummy JSON response (e.g., `{"message": "This is protected data!", "your_token_was": token}`).
#    - FastAPI's `OAuth2PasswordBearer` will automatically raise `HTTPException(401)` if no token (or an invalid format) is provided.
#
# Considerations:
# - Ensure the `oauth2_scheme` is correctly defined with the `tokenUrl` pointing to your login endpoint. This is already done.
# - Coordinate with Almer (Backend Task 5) who is integrating this router into `main.py`.
#
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

@router.get("/protected")
async def read_protected_data(token: str = Depends(oauth2_scheme)):
    """
    Retrieves protected data, requiring a valid authentication token.
    For this prototype, any token present will grant access.
    """
    # The Depends(oauth2_scheme) already handles the basic check for token presence.
    # If a token is provided (even if just a string), this function will execute.
    return {"message": "This is protected data!", "your_token_was": token}