"""
Sprint 1 — Auth Middleware
Validates Bearer tokens and ensures a local user exists.
"""
import uuid
from fastapi import Request, HTTPException
from app.database import execute, fetch_one

async def ensure_user_exists(user_id: str, token: str):
    query = """
        INSERT INTO users (id, phone, name, email)
        VALUES (:id, :phone, :name, :email)
        ON CONFLICT (id) DO NOTHING
    """
    await execute(
        query=query,
        values={
            "id": user_id,
            "phone": f"{token[:20]}@local",
            "name": "Local User",
            "email": f"{token[:20]}@local.test",
        },
    )

async def verify_token(request: Request) -> str:
    """
    Extracts the Bearer token from the Authorization header and returns a stable user ID.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, token))

    try:
        await ensure_user_exists(user_id, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to verify user token")

    return user_id
