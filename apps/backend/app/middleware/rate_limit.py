from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.redis_client import redis_client

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Very basic rate limiting by IP (placeholder for Sprint 1)
        client_ip = request.client.host if request.client else "unknown"
        if client_ip != "unknown":
            key = f"rate_limit:{client_ip}"
            requests = redis_client.incr(key)
            if requests == 1:
                redis_client.expire(key, 60) # 1 minute window
            
            if requests > 100: # 100 requests per minute
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."}
                )
                
        response = await call_next(request)
        return response
