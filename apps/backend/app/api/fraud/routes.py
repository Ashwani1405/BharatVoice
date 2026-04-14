"""
Sprint 4 — Fraud API Routes
Endpoints to evaluate KYC profiles and push events to the fraud streams.
"""
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any

from app.services.fraud.ml_scorer import generate_fraud_score
from app.services.fraud.qdrant_client import upsert_profile
import redis
from app.config import settings

router = APIRouter()

class FraudEvalRequest(BaseModel):
    user_id: str
    profile: Dict[str, Any]
    context: Dict[str, Any] = {}

def push_event_to_redis(user_id: str, ip_address: str, event_type: str):
    """Pushes a raw event to Redis for Pathway to monitor velocity."""
    try:
        import json
        import time
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        payload = json.dumps({
            "user_id": user_id,
            "ip_address": ip_address,
            "event_type": event_type,
            "timestamp": time.time()
        })
        r.rpush("fraud_events", payload)
    except:
        pass


@router.post("/evaluate")
async def evaluate_fraud(body: FraudEvalRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Evaluates a user profile for fraud.
    Should be called immediately after KYC data collection completes.
    """
    # 1. Grab IP for context
    client_ip = request.client.host if request.client else "unknown"
    body.context["ip_address"] = body.context.get("ip_address", client_ip)
    
    # 2. Push event for Pathway real-time analysis in the background
    background_tasks.add_task(
        push_event_to_redis, 
        body.user_id, 
        body.context["ip_address"], 
        "kyc_evaluate"
    )
    
    # 3. Generate Fraud Score (Rules + Qdrant similarity)
    fraud_result = await generate_fraud_score(body.user_id, body.context, body.profile)
    
    # 4. If action is allow, save this profile to Qdrant so future clones get caught!
    if fraud_result["action"] == "allow":
        background_tasks.add_task(upsert_profile, body.user_id, body.profile)
        
    return {
        "status": "success",
        "fraud_assessment": fraud_result
    }
