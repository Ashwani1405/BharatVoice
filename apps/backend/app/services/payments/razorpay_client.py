"""
Sprint 5 — Razorpay Client
Handles all communication with the Razorpay API for creating orders, checking status, and verifying signatures.
"""
# TODO: Sprint 5 — implement this module

from typing import Dict, Any

async def create_razorpay_order(amount: int, receipt_id: str) -> Dict[str, Any]:
    """
    Create a new Razorpay order.
    
    Args:
        amount: Amount in paise
        receipt_id: Local receipt/transaction ID
        
    Returns:
        JSON response from Razorpay containing the new order_id
    """
    raise NotImplementedError("Sprint 5: implement Razorpay order creation")

def verify_webhook_signature(body: str, signature: str) -> bool:
    """
    Verify the cryptographic signature of an incoming Razorpay webhook.
    
    Args:
        body: The raw request body
        signature: The x-razorpay-signature header
        
    Returns:
        True if valid, False otherwise
    """
    raise NotImplementedError("Sprint 5: implement Razorpay signature verification")
