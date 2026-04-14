"""
Sprint 5 — Ledger Service
Manages internal double-entry booking equivalent for user wallets/accounts, ensuring
atomic transactions.
"""
# TODO: Sprint 5 — implement this module

import uuid
import logging
from app.database import execute

logger = logging.getLogger(__name__)

async def record_transaction(user_id: str, amount: int, type: str, description: str, razorpay_payment_id: str = None):
    """
    Record a credit or debit in the user's ledger atomically.
    
    Args:
        user_id: User performing the transaction
        amount: Positive amount in paise
        type: 'credit' or 'debit'
        description: Text description
        razorpay_payment_id: (Optional) External gateway mapping ID
    """
    query = """
        INSERT INTO ledger (id, user_id, amount, type, description, razorpay_payment_id)
        VALUES (:id, :user_id, :amount, :type, :description, :razorpay_payment_id)
    """
    values = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": amount,
        "type": type,
        "description": description,
        "razorpay_payment_id": razorpay_payment_id
    }
    
    try:
        await execute(query=query, values=values)
        logger.info(f"Recorded {type} of {amount} paise for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to record transaction for user {user_id}: {e}")
        raise e
