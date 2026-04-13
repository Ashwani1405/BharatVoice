"""
Sprint 3 — KYC Match Service
Verifies that OCR data matches the Aadhaar profile and performs face matching
using AWS Rekognition CompareFaces API.
"""
import os
import boto3
import asyncio
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")


def _rekognition_compare_faces(source_bytes: bytes, target_bytes: bytes) -> float:
    """
    Synchronous boto3 call to AWS Rekognition CompareFaces API.
    Must be run inside asyncio.to_thread() to avoid blocking the event loop.
    """
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError(
            "AWS credentials not configured. "
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env"
        )

    client = boto3.client(
        'rekognition',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    response = client.compare_faces(
        SourceImage={'Bytes': source_bytes},
        TargetImage={'Bytes': target_bytes},
        SimilarityThreshold=0.0
    )
    
    if len(response['FaceMatches']) == 0:
        return 0.0
        
    return float(response['FaceMatches'][0]['Similarity'])


async def calculate_face_match_score(source_image: bytes, target_image: bytes) -> float:
    """
    Compare two faces and compute a similarity score using AWS Rekognition.
    
    Args:
        source_image: The user's live selfie (raw bytes)
        target_image: The photo extracted from their ID document (raw bytes)
        
    Returns:
        Confidence score between 0.0 and 100.0
        
    Raises:
        ValueError: If AWS credentials are not configured or no faces detected
        ClientError: If the AWS API call fails
    """
    try:
        similarity = await asyncio.to_thread(
            _rekognition_compare_faces, 
            source_image, 
            target_image
        )
        logger.info(f"AWS Rekognition face similarity: {similarity:.1f}%")
        return similarity
    except ClientError as e:
        logger.error(f"AWS Rekognition error: {str(e)}")
        raise ValueError(f"Face matching failed: {str(e)}")
