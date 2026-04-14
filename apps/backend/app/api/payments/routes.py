"""
Sprint 5 — Payment Routes
"""
# TODO: Sprint 5 — implement this module
import uuid
import json
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from app.services.payments.razorpay_client import create_razorpay_order, verify_webhook_signature
from app.services.payments.ledger import record_transaction
from app.middleware.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create-order")
async def create_order(amount: int, user_id: str = Depends(verify_token)):
    """
    Create a Razorpay order.
    
    Args:
        amount: Payment amount in paise
        user_id: Caller's user ID extracted from Bearer token
        
    Returns:
        JSON with the order ID and details
    """
    # Quick receipt ID utilizing prefix and UUID
    receipt_id = f"rcpt_{uuid.uuid4().hex[:8]}"
    
    try:
        order = await create_razorpay_order(amount, receipt_id, user_id)
        return {"order_id": order.get("id"), "amount": amount, "currency": "INR"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to initiate Razorpay order")

@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Handle incoming Razorpay webhooks.
    
    Args:
        request: The FastAPI request object containing Razorpay payload
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    signature = request.headers.get("x-razorpay-signature")
    
    if not signature or not verify_webhook_signature(body_str, signature):
        logger.warning("Unverified Razorpay Webhook Call!")
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    try:
        payload = json.loads(body_str)
        
        # We only care about payments that have been successfully captured
        if payload.get("event") == "payment.captured":
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            user_id = payment_entity.get("notes", {}).get("user_id")
            amount = payment_entity.get("amount")
            payment_id = payment_entity.get("id")
            
            if user_id:
                # Deposit credit mapping for the recognized user
                await record_transaction(
                    user_id=user_id,
                    amount=amount,
                    type="credit",
                    description="Razorpay webhook deposit",
                    razorpay_payment_id=payment_id
                )
            else:
                logger.error(f"Captured payment {payment_id} has no mapped user_id!")
                
    except Exception as e:
        logger.error(f"Razorpay Webhook parsing error: {e}")
        # Webhooks shouldn't 500 otherwise Razorpay automatically retries indefinitely.
        return {"status": "error", "detail": "parse_failure"}
    
    return {"status": "ok"}
