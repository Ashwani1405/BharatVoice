"""
Sprint 3 — OCR Service
Extracts text and structured data from uploaded KYC documents (PAN, Aadhaar cards).
"""
# TODO: Sprint 3 — implement this module

from typing import Dict, Any

async def extract_document_data(image_bytes: bytes, document_type: str) -> Dict[str, Any]:
    """
    Run OCR on a document image and extract fields like Name, DOB, and ID Number.
    
    Args:
        image_bytes: The raw image bytes
        document_type: 'PAN' or 'AADHAAR'
        
    Returns:
        Dictionary of extracted fields
    """
    raise NotImplementedError("Sprint 3: implement document OCR")
