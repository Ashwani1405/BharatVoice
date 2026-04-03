"""
Sprint 4 — Fraud Routes
"""
# TODO: Sprint 4 — implement this module
from fastapi import APIRouter

router = APIRouter()

@router.get("/risk-score/{user_id}")
async def get_risk_score(user_id: str):
    """
    Get the calculated risk score for a user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        JSON with risk score and supporting signals
    """
    raise NotImplementedError("Sprint 4: implement risk score retrieval")
