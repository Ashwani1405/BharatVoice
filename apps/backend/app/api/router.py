from fastapi import APIRouter
from app.api import health
from app.api.voice import routes as voice_routes
from app.api.kyc import routes as kyc_routes
from app.api.fraud import routes as fraud_routes
from app.api.payments import routes as payment_routes
from app.api.sandbox import routes as sandbox_routes

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(voice_routes.router, prefix="/voice", tags=["voice"])
api_router.include_router(kyc_routes.router, prefix="/kyc", tags=["kyc"])
api_router.include_router(fraud_routes.router, prefix="/fraud", tags=["fraud"])
api_router.include_router(payment_routes.router, prefix="/payments", tags=["payments"])
api_router.include_router(sandbox_routes.router, prefix="/sandbox/v1", tags=["sandbox"])
