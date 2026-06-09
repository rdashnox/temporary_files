#
# Assigned to: Kenneth
# Task: Backend Task 2 - Implement User Registration Logic (Service & In-Memory Storage)
#
# Description:
# This task requires implementing the core logic for user registration within the authentication service.
# New users will be stored in an in-memory dictionary for this prototype.
#
# Deliverables:
# 1. Implement the `register_user(username: str, password: str)` function in this file.
# 2. This function should:
#    - Check if the `username` (email) already exists in the `_IN_MEMORY_USERS` dictionary.
#      If it exists, return `None` or raise an appropriate exception (e.g., `ValueError("User already exists")`).
#    - If the username is unique, add the new user (username and password) to the `_IN_MEMORY_USERS` dictionary.
#      (In a real application, passwords would be hashed before storing, but for this prototype, plain text is acceptable).
#    - Return the newly registered user's dictionary (e.g., a dictionary with username) upon successful registration.
#
# Considerations:
# - The `_IN_MEMORY_USERS` dictionary is already initialized with a dummy user.
# - Coordinate closely with Conrado (Backend Task 1) to ensure the function signature and return types match expectations.
#

#
# Assigned to: Aleczandra
# Task: Backend Task 3 - Enhance Token Structure & Generation
#
# Description:
# This task involves modifying the token creation to return a more structured, but still non-cryptographically signed,
# JWT-like string instead of a simple "fake-jwt-token".
#
# Deliverables:
# 1. Implement the `create_access_token(username: str)` function in this file. This function already exists as a placeholder.
# 2. This function should:
#    - Construct a Python dictionary with claims, including at least "sub" (subject, which is the username)
#      and "exp" (expiration timestamp).
#    - For "exp", calculate a future timestamp (e.g., 30 minutes from now) using `datetime` and `timedelta`.
#    - JSON-encode this dictionary to a string.
#    - Base64-encode the JSON string to simulate a JWT payload.
#    - Return this base64-encoded string as the "token".
#
# Considerations:
# - This token is for demonstrating structure and is NOT cryptographically secure. Do not use for real security.
# - You will need to import `json`, `base64`, `datetime`, and `timedelta`. These are already imported.
# - Coordinate with Conrado (Backend Task 1) as they will call this function.
#
import json
import base64
from datetime import datetime, timedelta

# Initial in-memory store of users
_IN_MEMORY_USERS = {
    "user@example.com": {"username": "user@example.com", "password": "password123"}
}

def verify_login(username: str, password: str):
    """
    Verifies user credentials against the in-memory user store.
    In a real application, this would involve querying a database and hashing passwords.
    """
    user = _IN_MEMORY_USERS.get(username)
    if user and user["password"] == password:
        return user
    return None