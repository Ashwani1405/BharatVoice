"""
Sprint 4 — Rule Engine
Evaluates static rules against transaction and identity data to flag suspicious activity.
"""
# TODO: Sprint 4 — implement this module

from typing import List, Dict

async def evaluate_rules(user_id: str, context: Dict) -> List[str]:
    """
    Run the rules engine against the user's event context.
    
    Args:
        user_id: ID of the user
        context: Dictionary of the current action (e.g. login, payment)
        
    Returns:
        List of triggered rule codes
    """
    raise NotImplementedError("Sprint 4: implement rule evaluation")
