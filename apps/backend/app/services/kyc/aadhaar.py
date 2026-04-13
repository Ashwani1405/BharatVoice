"""
Sprint 3 — Aadhaar Service
Integrates with the Sandbox Aadhaar Verification API to validate user identities.
"""
import os
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

AADHAAR_CLIENT_ID = os.getenv("AADHAAR_CLIENT_ID", "")
AADHAAR_CLIENT_SECRET = os.getenv("AADHAAR_CLIENT_SECRET", "")
AADHAAR_API_URL = os.getenv("AADHAAR_API_URL", "https://sandbox.aadhaarapi.com/v1")


async def trigger_otp(aadhaar_number: str) -> str:
    """
    Call the Aadhaar sandbox API to send an OTP to the user's registered phone.
    
    Args:
        aadhaar_number: The 12-digit Aadhaar number
        
    Returns:
        Reference ID for the OTP transaction
        
    Raises:
        ValueError: If credentials are not configured
        httpx.HTTPError: If API call fails
    """
    if not AADHAAR_CLIENT_ID or not AADHAAR_CLIENT_SECRET:
        raise ValueError(
            "Aadhaar API credentials not configured. "
            "Set AADHAAR_CLIENT_ID and AADHAAR_CLIENT_SECRET in .env"
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AADHAAR_API_URL}/kyc/otp",
            json={"aadhaar_number": aadhaar_number},
            headers={
                "client_id": AADHAAR_CLIENT_ID,
                "client_secret": AADHAAR_CLIENT_SECRET
            },
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        
        ref_id = data.get("reference_id")
        if not ref_id:
            raise ValueError(f"Aadhaar API did not return a reference_id: {data}")
            
        logger.info(f"OTP triggered for Aadhaar ending ...{aadhaar_number[-4:]}")
        return ref_id


async def verify_otp(reference_id: str, otp: str) -> Dict[str, Any]:
    """
    Verify the Aadhaar OTP and fetch the e-KYC profile data.
    
    Args:
        reference_id: The transaction reference ID from trigger_otp
        otp: The 6-digit OTP entered by the user
        
    Returns:
        JSON dictionary containing the user's verified Aadhaar profile
        
    Raises:
        ValueError: If credentials are not configured
        httpx.HTTPError: If API call fails
    """
    if not AADHAAR_CLIENT_ID or not AADHAAR_CLIENT_SECRET:
        raise ValueError(
            "Aadhaar API credentials not configured. "
            "Set AADHAAR_CLIENT_ID and AADHAAR_CLIENT_SECRET in .env"
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AADHAAR_API_URL}/kyc/verify",
            json={
                "reference_id": reference_id,
                "otp": otp
            },
            headers={
                "client_id": AADHAAR_CLIENT_ID,
                "client_secret": AADHAAR_CLIENT_SECRET
            },
            timeout=10.0
        )
        response.raise_for_status()
        profile = response.json()
        
        logger.info(f"Aadhaar OTP verified for reference: {reference_id}")
        return profile
