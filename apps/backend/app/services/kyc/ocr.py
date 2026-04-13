"""
Sprint 3 — OCR Service
Extracts text and structured data from uploaded KYC documents (PAN, Aadhaar cards).
"""
import io
import re
import asyncio
import logging
from typing import Dict, Any

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

logger = logging.getLogger(__name__)

async def extract_document_data(image_bytes: bytes, document_type: str) -> Dict[str, Any]:
    """
    Run OCR on a document image and extract fields like Name, DOB, and ID Number.
    
    Args:
        image_bytes: The raw image bytes
        document_type: 'PAN' or 'AADHAAR'
        
    Returns:
        Dictionary of extracted fields
    """
    if pytesseract is None or Image is None:
        logger.error("pytesseract or Pillow is not installed. Please install them.")
        raise RuntimeError("OCR dependencies missing.")

    # Load image using Pillow
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Invalid image format: {str(e)}")

    # Extract raw text via Tesseract (offloaded to threadpool to avoid blocking event loop)
    raw_text = await asyncio.to_thread(pytesseract.image_to_string, img)
    
    logger.info(f"Successfully ran OCR on {document_type} document.")

    # Initialize response dict
    extracted_data = {
        "id_number": None,
        "dob": None,
        "raw_text_preview": raw_text[:100].replace("\n", " ").strip()
    }

    # Use basic regex constraints based on document type
    if document_type.upper() == "PAN":
        # PAN format: 5 letters, 4 numbers, 1 letter (e.g. ABCDE1234F)
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', raw_text)
        if pan_match:
            extracted_data["id_number"] = pan_match.group(0)
    elif document_type.upper() == "AADHAAR":
        # Aadhaar format: 12 digits (sometimes spaced 4 by 4)
        clean_text = raw_text.replace(" ", "").replace("-", "")
        aadhaar_match = re.search(r'\d{12}', clean_text)
        if aadhaar_match:
            extracted_data["id_number"] = aadhaar_match.group(0)

    # DOB match across either document
    # formats: DD/MM/YYYY or DD-MM-YYYY
    dob_match = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b', raw_text)
    if dob_match:
        extracted_data["dob"] = dob_match.group(1)

    return extracted_data
