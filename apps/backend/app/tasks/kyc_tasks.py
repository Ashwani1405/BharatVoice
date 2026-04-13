import json
import asyncio
import logging
from app.tasks.celery_app import celery_app
from app.services.kyc.ocr import extract_document_data
from app.services.kyc.kyc_match import calculate_face_match_score
from app.services.kyc.aadhaar import trigger_otp

logger = logging.getLogger(__name__)


@celery_app.task(name="initiate_kyc_verification")
def initiate_kyc_verification(user_id: str):
    """
    Background worker triggered when a voice call successfully 
    collects all required KYC fields.
    
    Pulls the user's Aadhaar number from Redis session data
    and kicks off OTP verification.
    """
    import redis
    import os
    
    logger.info(f"Starting background KYC verification for user: {user_id}")
    
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = redis.from_url(redis_url)
    
    # Find the call_id associated with this user from Redis
    call_id_raw = r.get(f"vapi_user:{user_id}")
    if not call_id_raw:
        logger.error(f"No active call session found for user {user_id}")
        return {"status": "error", "reason": "no_active_session"}
    
    call_id = call_id_raw.decode("utf-8")
    
    # Fetch collected fields from the voice session
    session_data = r.hgetall(f"voice_session:{call_id}")
    if not session_data:
        logger.error(f"Session data empty for call {call_id}")
        return {"status": "error", "reason": "empty_session"}
    
    fields_raw = session_data.get(b"fields_collected", b"{}")
    fields = json.loads(fields_raw.decode("utf-8"))
    
    aadhaar_number = fields.get("aadhaar_number")
    if not aadhaar_number:
        logger.error(f"No Aadhaar number collected for user {user_id}")
        return {"status": "error", "reason": "no_aadhaar"}
    
    try:
        ref_id = asyncio.run(trigger_otp(aadhaar_number))
        logger.info(f"OTP triggered for user {user_id}, ref: {ref_id}")
        
        # Store the reference_id in Redis so the frontend can use it
        r.setex(f"aadhaar_ref:{user_id}", 600, ref_id)  # 10 min TTL
        
        return {"status": "otp_triggered", "user_id": user_id, "reference_id": ref_id}
    except Exception as e:
        logger.error(f"KYC verification failed for {user_id}: {str(e)}")
        return {"status": "error", "reason": str(e)}


@celery_app.task(name="process_identity_documents")
def process_identity_documents(user_id: str, document_bytes: bytes, doc_type: str, selfie_bytes: bytes):
    """
    Background worker for processing OCR extraction and 
    face recognition on uploaded identity documents.
    """
    logger.info(f"Processing documents for user: {user_id}")
    
    try:
        # 1. OCR Extraction
        ocr_result = asyncio.run(extract_document_data(document_bytes, doc_type))
        logger.info(f"OCR result: id_number={ocr_result.get('id_number')}")
        
        # 2. Face Similarity via AWS Rekognition
        similarity = asyncio.run(calculate_face_match_score(selfie_bytes, document_bytes))
        logger.info(f"Face similarity: {similarity:.1f}%")
        
        return {
            "status": "processed", 
            "user_id": user_id,
            "ocr": ocr_result,
            "face_similarity": round(similarity, 2),
            "face_match": similarity >= 80.0
        }
    except Exception as e:
        logger.error(f"Document processing failed for {user_id}: {str(e)}")
        return {"status": "error", "reason": str(e)}
