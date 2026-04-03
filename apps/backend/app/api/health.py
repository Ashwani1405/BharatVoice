from fastapi import APIRouter
from app.database import database
from app.redis_client import redis_client
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    health_status = {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database": "disconnected",
        "redis": "disconnected",
        "version": "1.0.0"
    }

    try:
        if database.is_connected:
            # Quick query to verify it's really alive
            await database.execute("SELECT 1")
            health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"

    try:
        ping = redis_client.ping()
        if ping:
            health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"

    return health_status
