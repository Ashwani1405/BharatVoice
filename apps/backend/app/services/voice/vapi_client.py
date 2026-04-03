"""
Sprint 2 — VAPI Client
Handles communication with the VAPI API for starting and managing calls.
"""
# TODO: Sprint 2 — implement this module

from typing import Dict, Any

async def start_outbound_call(phone_number: str) -> Dict[str, Any]:
    """
    Start an outbound call to a user via VAPI.
    
    Args:
        phone_number: E.164 formatted phone number
        
    Returns:
        JSON response with the call details
    """
    raise NotImplementedError("Sprint 2: implement VAPI outbound call")
