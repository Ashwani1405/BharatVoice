"""
Sprint 2 — Voice Routers
"""
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook")
async def voice_webhook(request: Request):
    """
    Handle incoming webhooks from VAPI.
    
    Args:
        request: The FastAPI request object containing the VAPI payload
        
    Returns:
        JSON response with the next action for the voice agent
    """
    raise NotImplementedError("Sprint 2: implement voice webhook")
