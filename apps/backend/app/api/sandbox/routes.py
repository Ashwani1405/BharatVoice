"""
KYC Sandbox API
Mock implementation of external Aadhaar sandbox services.
"""
import csv
import os
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for the dataset
# A dict mapping aadhaar_number -> profile
_MOCK_DATASET: Dict[str, Dict[str, Any]] = {}

# In-memory store for generated OTP references
# A dict mapping reference_id -> aadhaar_number
_OTP_SESSIONS: Dict[str, str] = {}

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
    "data", 
    "mock_aadhaar_dataset.csv"
)

def get_mock_dataset() -> Dict[str, Dict[str, Any]]:
    """Lazy load the mock dataset into memory."""
    global _MOCK_DATASET
    if not _MOCK_DATASET:
        if not os.path.exists(DATASET_PATH):
            logger.warning(f"Mock dataset not found at {DATASET_PATH}. Please generate it.")
            return {}
        
        try:
            logger.info("Loading mock Aadhaar dataset into memory...")
            with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    _MOCK_DATASET[row['aadhaar_number']] = row
            logger.info(f"Loaded {len(_MOCK_DATASET)} records into mock sandbox.")
        except Exception as e:
            logger.error(f"Failed to load mock dataset: {e}")
            
    return _MOCK_DATASET


class SandboxOtpTriggerRequest(BaseModel):
    aadhaar_number: str

class SandboxOtpVerifyRequest(BaseModel):
    reference_id: str
    otp: str


@router.post("/kyc/otp")
async def trigger_mock_otp(body: SandboxOtpTriggerRequest):
    """
    Mock endpoint to trigger OTP.
    Generates a mock reference_id if the Aadhaar number exists in our mock dataset.
    """
    dataset = get_mock_dataset()
    aadhaar = body.aadhaar_number.replace(" ", "").replace("-", "")
    
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        raise HTTPException(status_code=400, detail="Invalid Aadhaar number format")
        
    if aadhaar not in dataset:
        raise HTTPException(status_code=404, detail="Aadhaar number not found in mock Sandbox")
        
    # Generate a mock reference ID
    ref_id = f"mock_{uuid.uuid4().hex}"
    
    # Store session
    _OTP_SESSIONS[ref_id] = aadhaar
    
    logger.info(f"Sandbox: Triggered OTP for {aadhaar}, Ref ID: {ref_id}")
    return {"status": "success", "reference_id": ref_id, "message": "OTP sent in Sandbox mode (Use 123456 to verify)"}


@router.post("/kyc/verify")
async def verify_mock_otp(body: SandboxOtpVerifyRequest):
    """
    Mock endpoint to verify OTP.
    Accepts OTP '123456' for any valid reference_id and returns the profile.
    """
    if body.reference_id not in _OTP_SESSIONS:
        raise HTTPException(status_code=400, detail="Invalid or expired reference_id")
        
    if body.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP. Please use 123456.")
        
    aadhaar = _OTP_SESSIONS.pop(body.reference_id)
    dataset = get_mock_dataset()
    
    profile = dataset.get(aadhaar)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found in database anymore")
        
    logger.info(f"Sandbox: Verified OTP for {aadhaar}")
    
    # Return structure matching Aadhaar standard
    return {
        "status": "success",
        "verified": True,
        "profile": profile
    }
