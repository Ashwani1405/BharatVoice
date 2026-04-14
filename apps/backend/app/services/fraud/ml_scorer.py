"""
Sprint 4 — ML Scorer
Aggregates Qdrant embeddings and Rule Engine metrics into a unified Fraud Confidence Score.
"""
from typing import Dict, List
import logging

from app.services.fraud.qdrant_client import search_similar_profiles
from app.services.fraud.rule_engine import evaluate_rules

logger = logging.getLogger(__name__)

async def generate_fraud_score(user_id: str, context: Dict, profile: Dict) -> Dict:
    """
    Main entrypoint for Fraud Analysis API.
    
    Returns:
        {
           "risk_score": 0-100,
           "flags": ["RULE_VELOCITY_ABUSE", "SYBIL_MATCH"],
           "action": "allow" | "review" | "block",
           "similarity_score": 0.85
        }
    """
    # 1. Rule Engine
    rule_flags = await evaluate_rules(user_id, context, profile)
    
    # 2. Vector DB (Sybil Attack Detection)
    # Exclude results that are literally the same user_id using the API filter
    similar_profiles, max_sim_score = await search_similar_profiles(profile, user_id=user_id, limit=2)
    
    sybil_flag = False
    # Threshold at 0.95: BGE-small scores near-duplicate strings (same person with 1-2 typos)
    # between 0.95-0.97, isolating actual different household members (who score ~0.94).
    if max_sim_score > 0.95:
        sybil_flag = True
        rule_flags.append("SYBIL_IDENTITY_CLONE")
        
    # Calculate Risk
    base_risk = 0
    if "RULE_VELOCITY_ABUSE" in rule_flags:
        base_risk += 100
    if "RULE_DUMMY_ADDRESS" in rule_flags or "RULE_INVALID_DOB_RANGE" in rule_flags:
        # Increase from 30 to 45 so a single rule triggers the "review" threshold (>= 40)
        base_risk += 45
    if sybil_flag:
        base_risk += 80
        
    final_score = min(base_risk, 100)
    
    # Decision Engine
    if final_score >= 80:
        action = "block"
    elif final_score >= 40:
        action = "review"
    else:
        action = "allow"
        
    logger.info(f"Fraud Scan for {user_id}: Score={final_score}, Action={action}")
    
    return {
        "risk_score": final_score,
        "flags": rule_flags,
        "action": action,
        "similarity_score": max_sim_score
    }
