#
# Assigned to: Conrado
# Task: Backend Task 1 - Implement User Registration Endpoint (Routes & Controller)
#
# Description:
# This file will be modified to add a controller function for user registration.
# This function will call the corresponding service function to handle registration logic.
#
# Deliverables:
# 1. Add a new function `register_new_user(username: str, password: str)` to this file.
# 2. This function should:
#    - Call `auth_service.register_user(username, password)`.
#    - Handle potential errors from the service layer (e.g., user already exists) by raising
#      appropriate `HTTPException`s or returning specific status codes/messages.
#    - Return the newly registered user object from the service layer on success.
#
# Considerations:
# - Coordinate with Kenneth (Backend Task 2) who will implement the service logic for registration.
# - The function should be `async` if the service call is `await`ed.
#
#
# Assigned to: Aleczandra
# Task: Backend Task 3 - Enhance Token Structure & Generation
#
# Description:
# This task involves modifying the authentication flow to use the newly defined structured token.
#
# Deliverables:
# 1. Ensure the `authenticate_user` function correctly calls `auth_service.create_access_token`
#    upon successful authentication. This has already been added as a placeholder.
# 2. The `authenticate_user` function should return the generated token string on success,
#    or `False` on authentication failure.
#
# Considerations:
# - Coordinate with Aleczandra (who is working on `auth_service.py`) as they will be implementing the token generation logic.
# - Ensure that the `authenticate_user` function's return type is updated to reflect this change.
#
from ..services import auth_service

def authenticate_user(username: str, password: str):
    """
    Authenticates a user by calling the authentication service.
    """
    user = auth_service.verify_login(username, password)
    if not user:
        return False # Authentication failed

    # --- This is part of Aleczandra's Backend Task 3 ---
    # Task modification: Generate a structured token on successful login
    token = auth_service.create_access_token(username)
    return token # Authentication successful, return the token