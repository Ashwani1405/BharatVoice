"""
Sprint 5 — Payment Routes
"""
# TODO: Sprint 5 — implement this module
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/create-order")
async def create_order(amount: int):
    """
    Create a Razorpay order.
    
    Args:
        amount: Payment amount in paise
        
    Returns:
        JSON with the order ID and details
    """
    raise NotImplementedError("Sprint 5: implement order creation")

@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Handle incoming Razorpay webhooks.
    
    Args:
        request: The FastAPI request object containing Razorpay payload
    """
    raise NotImplementedError("Sprint 5: implement Razorpay webhook")
