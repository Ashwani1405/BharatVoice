"""
Sprint 5 — Razorpay Client
Handles all communication with the Razorpay API for creating orders, checking status, and verifying signatures.
"""
# TODO: Sprint 5 — implement this module

from typing import Dict, Any
import razorpay
import asyncio
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Razorpay Client synchronously
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

async def create_razorpay_order(amount: int, receipt_id: str, user_id: str) -> Dict[str, Any]:
    """
    Create a new Razorpay order.
    
    Args:
        amount: Amount in paise
        receipt_id: Local receipt/transaction ID
        user_id: The ID of the user initiating the order
        
    Returns:
        JSON response from Razorpay containing the new order_id
    """
    data = {
        "amount": amount,
        "currency": "INR",
        "receipt": receipt_id,
        "payment_capture": 1, # Auto-capture payments
        "notes": {
            "user_id": user_id
        }
    }
    
    # Razorpay library uses requests (synchronous). Let's wrap in an executor to avoid blocking the event loop.
    try:
        response = await asyncio.to_thread(client.order.create, data=data)
        logger.info(f"Created Razorpay order {response.get('id')} for receipt {receipt_id}")
        return response
    except Exception as e:
        logger.error(f"Failed to create Razorpay order: {e}")
        raise e

def verify_webhook_signature(body: str, signature: str) -> bool:
    """
    Verify the cryptographic signature of an incoming Razorpay webhook.
    
    Args:
        body: The raw request body
        signature: The x-razorpay-signature header
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Expected signature utility compares it with backend webhook secret
        return client.utility.verify_webhook_signature(
            body, 
            signature, 
            settings.RAZORPAY_WEBHOOK_SECRET
        )
    except razorpay.errors.SignatureVerificationError:
        logger.warning("Razorpay Webhook Signature mismatch.")
        return False
