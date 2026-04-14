"""
Sprint 4 — Rule Engine
Evaluates static rules against transaction and identity data to flag suspicious activity.
"""
from typing import List, Dict
import redis
from app.config import settings

def _is_ip_blacklisted(ip_address: str) -> bool:
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Check if Pathway streaming worker flagged this IP
        if r.exists(f"blacklist:ip:{ip_address}"):
            return True
    except:
        pass
    return False

async def evaluate_rules(user_id: str, context: Dict, profile: Dict) -> List[str]:
    """
    Run the rules engine against the user's event context.
    
    Args:
        user_id: ID of the user
        context: Dictionary of the current action (e.g. login, payment)
        profile: KYC identity dict
        
    Returns:
        List of triggered rule codes
    """
    flags = []
    
    ip_address = context.get("ip_address")
    if ip_address and _is_ip_blacklisted(ip_address):
        flags.append("RULE_VELOCITY_ABUSE")
        
    # Basic static checks
    if profile:
        dob = str(profile.get("dob") or "")
        # For a hackathon, we assume any DOB containing '2025' or '2026' is invalid (underage/fake)
        if "2025" in dob or "2026" in dob:
            flags.append("RULE_INVALID_DOB_RANGE")
            
        address = str(profile.get("address") or "").lower()
        # Also catch 'fake' and 'null' as dummy address keywords
        dummy_keywords = ["unknown", "test", "fake", "null", "n/a"]
        if any(kw in address for kw in dummy_keywords):
            flags.append("RULE_DUMMY_ADDRESS")
            
    return flags
