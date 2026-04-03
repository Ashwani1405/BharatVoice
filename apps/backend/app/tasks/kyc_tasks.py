"""
Sprint 3 — KYC Background Tasks
Celery tasks for async document OCR, face matching, and Aadhaar background sync.
"""
# TODO: Sprint 3 — implement this module

from app.worker import celery_app

@celery_app.task
def process_kyc_documents(user_id: str, document_s3_keys: list):
    """
    Background task to process uploaded KYC documents:
    1. Download from S3
    2. Run OCR
    3. Run Face match
    4. Update DB status
    """
    raise NotImplementedError("Sprint 3: implement background KYC processing")
