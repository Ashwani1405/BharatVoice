"""
Sprint 3 — KYC Match Service
Verifies that OCR data matches the Aadhaar profile and performs face matching.
"""
# TODO: Sprint 3 — implement this module

async def calculate_face_match_score(source_image: bytes, target_image: bytes) -> float:
    """
    Compare two faces and compute a similarity score.
    
    Args:
        source_image: The user's live selfie
        target_image: The photo extracted from their ID
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    raise NotImplementedError("Sprint 3: implement face matching")
