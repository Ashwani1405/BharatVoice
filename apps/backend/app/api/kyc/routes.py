"""
Sprint 3 — KYC Routes
"""
# TODO: Sprint 3 — implement this module
from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload-document")
async def upload_document(document: UploadFile = File(...)):
    """
    Upload an Aadhaar or PAN document for OCR processing.
    
    Args:
        document: The image file uploaded by the user
        
    Returns:
        JSON response with OCR extracted data
    """
    raise NotImplementedError("Sprint 3: implement OCR document upload")

@router.post("/verify-aadhaar")
async def verify_aadhaar(aadhaar_number: str):
    """
    Trigger Aadhaar OTP for verification.
    
    Args:
        aadhaar_number: The 12-digit Aadhaar number
    """
    raise NotImplementedError("Sprint 3: implement Aadhaar verification")
