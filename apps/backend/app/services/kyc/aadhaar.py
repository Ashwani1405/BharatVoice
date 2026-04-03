"""
Sprint 3 — Aadhaar Service
Integrates with the Sandbox Aadhaar Verification API to validate user identities.
"""
# TODO: Sprint 3 — implement this module

from typing import Dict, Any

async def trigger_otp(aadhaar_number: str) -> str:
    """
    Call the Aadhaar sandbox API to send an OTP to the user's registered phone.
    
    Args:
        aadhaar_number: The 12-digit Aadhaar number
        
    Returns:
        Reference ID for the OTP transaction
    """
    raise NotImplementedError("Sprint 3: implement Aadhaar OTP trigger")

async def verify_otp(reference_id: str, otp: str) -> Dict[str, Any]:
    """
    Verify the Aadhaar OTP and fetch the e-KYC profile data.
    
    Args:
        reference_id: The transaction reference ID
        otp: The 6-digit OTP
        
    Returns:
        JSON dictionary containing the user's Aadhaar data
    """
    raise NotImplementedError("Sprint 3: implement Aadhaar OTP verification")
