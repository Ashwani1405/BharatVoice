"""
Sprint 1 — Auth Middleware
Validates JWT tokens for protected routes.
"""
# TODO: Sprint 1 — implement auth extraction
from fastapi import Request, HTTPException
from typing import Optional

async def verify_token(request: Request) -> Optional[str]:
    """
    Extracts the Bearer token from the Authorization header and verifies it.
    Returns the user ID if valid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    # To be implemented
    return "user_id_placeholder"
