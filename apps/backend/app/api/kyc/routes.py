"""
Sprint 3 — KYC REST Routes
Endpoints for document upload (OCR), Aadhaar OTP trigger/verify, 
and face match scoring.
"""
import json
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.kyc.ocr import extract_document_data
from app.services.kyc.aadhaar import trigger_otp, verify_otp
from app.services.kyc.kyc_match import calculate_face_match_score

logger = logging.getLogger(__name__)

router = APIRouter()


class AadhaarOTPRequest(BaseModel):
    aadhaar_number: str


class AadhaarVerifyRequest(BaseModel):
    reference_id: str
    otp: str


@router.post("/upload-document")
async def upload_document(
    document: UploadFile = File(...),
    doc_type: str = "AADHAAR"
):
    """
    Upload an Aadhaar or PAN document image for OCR processing.
    
    Args:
        document: The image file uploaded by the user
        doc_type: 'PAN' or 'AADHAAR' (default: AADHAAR)
        
    Returns:
        JSON response with OCR extracted data (id_number, dob, raw_text_preview)
    """
    if doc_type.upper() not in ("PAN", "AADHAAR"):
        raise HTTPException(status_code=400, detail="doc_type must be 'PAN' or 'AADHAAR'")

    image_bytes = await document.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 10 MB.")

    try:
        result = await extract_document_data(image_bytes, doc_type.upper())
        logger.info(f"OCR extraction complete for {doc_type}: id_found={result.get('id_number') is not None}")
        return {"status": "success", "extracted": result}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-aadhaar/trigger")
async def aadhaar_trigger_otp(body: AadhaarOTPRequest):
    """
    Trigger Aadhaar OTP for identity verification.
    """
    aadhaar = body.aadhaar_number.replace(" ", "").replace("-", "")
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        raise HTTPException(status_code=400, detail="Aadhaar must be exactly 12 digits")

    try:
        ref_id = await trigger_otp(aadhaar)
        return {"status": "otp_sent", "reference_id": ref_id}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Aadhaar OTP trigger failed: {str(e)}")
        raise HTTPException(status_code=502, detail="External Aadhaar API error")


@router.post("/verify-aadhaar/confirm")
async def aadhaar_verify_otp(body: AadhaarVerifyRequest):
    """
    Confirm the 6-digit OTP and retrieve verified e-KYC profile.
    """
    if len(body.otp) != 6 or not body.otp.isdigit():
        raise HTTPException(status_code=400, detail="OTP must be exactly 6 digits")

    try:
        profile = await verify_otp(body.reference_id, body.otp)
        return {"status": "verified", "profile": profile}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Aadhaar OTP verification failed: {str(e)}")
        raise HTTPException(status_code=502, detail="External Aadhaar verification error")


@router.post("/face-match")
async def face_match(
    selfie: UploadFile = File(...),
    id_photo: UploadFile = File(...)
):
    """
    Compare a live selfie against an ID document photo using AWS Rekognition.
    
    Returns:
        similarity: Float between 0.0 - 100.0
        match: Boolean (true if similarity >= 80%)
    """
    selfie_bytes = await selfie.read()
    id_bytes = await id_photo.read()

    if len(selfie_bytes) == 0 or len(id_bytes) == 0:
        raise HTTPException(status_code=400, detail="Both image files are required and cannot be empty")

    try:
        score = await calculate_face_match_score(selfie_bytes, id_bytes)
        return {
            "status": "success",
            "similarity": round(score, 2),
            "match": score >= 80.0
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Face match failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Face matching service error")
