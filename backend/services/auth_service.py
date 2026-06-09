import json
import base64
from datetime import datetime, timedelta

# Initial in-memory store of users for demonstration purposes.
# In a real application, this would be a database.
_IN_MEMORY_USERS = {
    "user@example.com": {"username": "user@example.com", "password": "password123"}
}

def verify_login(username: str, password: str):
    """
    Verifies user credentials against the in-memory user store.
    """
    user = _IN_MEMORY_USERS.get(username)
    if user and user["password"] == password:
        return user
    return None

def register_user(username: str, password: str):
    """
    Registers a new user in the in-memory store.
    """
    # Implement logic to check if user already exists
    # Implement logic to add new user to _IN_MEMORY_USERS
    # In a real app, hash the password before storing
    pass # Placeholder, implement registration logic here

def create_access_token(username: str):
    """
    Generates a structured, but non-cryptographically signed, JWT-like string.
    """
    # Implement logic to construct a dictionary with claims (e.g., "sub", "exp")
    # JSON-encode the dictionary
    # Base64-encode the JSON string
    # Return the base64-encoded string
    # (This is for demonstration; NOT cryptographically secure JWT for production)
    return "fake-jwt-token" # Placeholder, implement token generation logic here
