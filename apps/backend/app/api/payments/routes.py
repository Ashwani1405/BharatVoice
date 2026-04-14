"""
Sprint 5 — Payment Routes
"""
import uuid
import json
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from app.services.payments.razorpay_client import create_razorpay_order, verify_webhook_signature
from app.services.payments.ledger import record_transaction
from app.middleware.auth import verify_token
from app.database import fetch_one, fetch_all

logger = logging.getLogger(__name__)
router = APIRouter()

class ConfirmPaymentRequest(BaseModel):
    payment_id: str
    amount: int
    description: str = "Razorpay top-up"

@router.post("/create-order")
async def create_order(amount: int, user_id: str = Depends(verify_token)):
    """
    Create a Razorpay order.
    """
    receipt_id = f"rcpt_{uuid.uuid4().hex[:8]}"

    try:
        order = await create_razorpay_order(amount, receipt_id, user_id)
        return {"order_id": order.get("id"), "amount": amount, "currency": "INR"}
    except Exception as e:
        logger.error(f"Failed to create Razorpay order: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate Razorpay order")

@router.post("/confirm-payment")
async def confirm_payment(request: ConfirmPaymentRequest, user_id: str = Depends(verify_token)):
    """
    Confirm a Razorpay payment and record it in the ledger.
    """
    existing = await fetch_one(
        query="SELECT id FROM ledger WHERE razorpay_payment_id = :payment_id",
        values={"payment_id": request.payment_id},
    )
    if existing:
        return {"status": "already_recorded"}

    try:
        await record_transaction(
            user_id=user_id,
            amount=request.amount,
            type="credit",
            description=request.description,
            razorpay_payment_id=request.payment_id,
        )
    except Exception as e:
        logger.error(f"Failed to record confirmed payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to record payment")

    balance_row = await fetch_one(
        query="SELECT COALESCE(SUM(CASE WHEN type = 'credit' THEN amount ELSE -amount END), 0) AS balance FROM ledger WHERE user_id = :user_id",
        values={"user_id": user_id},
    )
    balance = balance_row["balance"] if balance_row else 0
    return {"status": "ok", "balance": balance}

@router.get("/wallet")
async def get_wallet(user_id: str = Depends(verify_token)):
    """
    Get the user's wallet balance.
    """
    balance_row = await fetch_one(
        query="SELECT COALESCE(SUM(CASE WHEN type = 'credit' THEN amount ELSE -amount END), 0) AS balance FROM ledger WHERE user_id = :user_id",
        values={"user_id": user_id},
    )
    balance = balance_row["balance"] if balance_row else 0
    return {"balance": balance, "currency": "INR"}

@router.get("/transactions")
async def get_transactions(user_id: str = Depends(verify_token)):
    """
    Get the user's ledger transaction history.
    """
    rows = await fetch_all(
        query="""
            SELECT id, amount, type, description, razorpay_payment_id, created_at
            FROM ledger
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """,
        values={"user_id": user_id},
    )
    return {"transactions": [dict(row) for row in rows]}

@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Handle incoming Razorpay webhooks.
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    signature = request.headers.get("x-razorpay-signature")

    if not signature or not verify_webhook_signature(body_str, signature):
        logger.warning("Unverified Razorpay Webhook Call!")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body_str)
        if payload.get("event") == "payment.captured":
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            user_id = payment_entity.get("notes", {}).get("user_id")
            amount = payment_entity.get("amount")
            payment_id = payment_entity.get("id")

            if user_id:
                await record_transaction(
                    user_id=user_id,
                    amount=amount,
                    type="credit",
                    description="Razorpay webhook deposit",
                    razorpay_payment_id=payment_id,
                )
            else:
                logger.error(f"Captured payment {payment_id} has no mapped user_id!")
    except Exception as e:
        logger.error(f"Razorpay Webhook parsing error: {e}")
        return {"status": "error", "detail": "parse_failure"}

    return {"status": "ok"}
