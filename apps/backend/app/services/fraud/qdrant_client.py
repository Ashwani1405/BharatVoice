"""
Sprint 4 — Qdrant Client
Manages connections and queries to the Qdrant vector database for similarity search of fraud clusters.
"""
import logging
import uuid
from typing import List, Dict, Tuple
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Qdrant Client
qdrant = AsyncQdrantClient(url=settings.QDRANT_URL)

COLLECTION_NAME = "kyc_profiles"

# Initialize FastEmbed (downloads/loads BAAI/bge-small-en-v1.5 locally)
# Using singleton pattern to avoid reloading model constantly
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


async def init_qdrant_collection():
    """Ensure the target collection exists with correct vector size."""
    try:
        collections = await qdrant.get_collections()
        if not any(c.name == COLLECTION_NAME for c in collections.collections):
            # BGE-small outputs 384 dimensions
            await qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info("Created new Qdrant collection: kyc_profiles")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")


def _generate_embedding(text: str) -> List[float]:
    """Generates embedding using fastembed. FastEmbed returns a generator of numpy arrays."""
    # embed() returns a list of results, we take the first item, convert to list of floats
    emb_generator = embedding_model.embed([text])
    emb_array = next(emb_generator)
    return emb_array.tolist()


def format_kyc_string(profile: Dict) -> str:
    """Combines KYC properties into a single meaning-rich string.
    
    Returns an empty string if the profile has no real content,
    so callers can skip Qdrant operations for degenerate inputs.
    """
    name = profile.get("name")
    address = profile.get("address")
    dob = profile.get("dob")
    
    # All meaningful fields are absent or None — not worth embedding
    if not any([name, address, dob]):
        return ""
    
    name_str = str(name) if name else "Unknown Name"
    address_str = str(address) if address else "Unknown Address"
    dob_str = str(dob) if dob else "Unknown DOB"
    return f"{name_str} residing at {address_str} born {dob_str}"


def _is_meaningful_profile(profile: Dict) -> bool:
    """Returns True if the profile contains at least one non-empty field."""
    if not profile:
        return False
    for v in profile.values():
        if v is not None and str(v).strip():
            return True
    return False


async def search_similar_profiles(profile: Dict, user_id: str = None, limit: int = 5) -> Tuple[List[dict], float]:
    """
    Search Qdrant for similar users based on KYC data text embeddings.
    
    Returns:
        List of matched profiles
        Max Similarity score (0.0 to 1.0)
    """
    # If the profile has no meaningful content, skip the Qdrant lookup entirely.
    # All empty/None profiles would embed to the same generic string, causing
    # false SYBIL_IDENTITY_CLONE flags across unrelated sparse submissions.
    if not _is_meaningful_profile(profile):
        logger.debug(f"Skipping Qdrant search for {user_id}: profile has no meaningful content")
        return [], 0.0
    
    text = format_kyc_string(profile)
    if not text:  # extra safety
        return [], 0.0
    vector = _generate_embedding(text)
    
    # Calculate current point_id to exclude it from search results
    point_id_to_exclude = None
    if user_id:
        try:
            point_id_to_exclude = str(uuid.UUID(user_id))
        except ValueError:
            point_id_to_exclude = str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id))

    try:
        from qdrant_client.models import Filter, HasIdCondition
        
        search_filter = None
        if point_id_to_exclude:
            # Tell Qdrant to NOT return our own record
            search_filter = Filter(
                must_not=[
                    HasIdCondition(has_id=[point_id_to_exclude])
                ]
            )

        search_result = await qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
            query_filter=search_filter,
            score_threshold=0.70 # Lower threshold to see full range
        )
        
        matches = [
            {"score": hit.score, "payload": hit.payload}
            for hit in search_result
        ]
        
        max_score = matches[0]["score"] if matches else 0.0
        return matches, max_score
        
    except Exception as e:
        logger.error(f"Qdrant Search Error: {e}")
        return [], 0.0


async def upsert_profile(user_id: str, profile: Dict):
    """
    Embed and insert a completed KYC profile into Qdrant.
    
    Skips profiles with no meaningful content to avoid polluting the
    vector store with generic embeddings that cause false positives.
    """
    if not _is_meaningful_profile(profile):
        logger.debug(f"Skipping Qdrant upsert for {user_id}: profile has no meaningful content")
        return
    
    await init_qdrant_collection()
    
    text = format_kyc_string(profile)
    if not text:
        return
    vector = _generate_embedding(text)
    
    # Qdrant requires UUIDs or unsigned integers for IDs
    # If user_id is already a UUID string, use it. Otherwise, derive one.
    try:
        point_id = str(uuid.UUID(user_id))
    except ValueError:
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id))
        
    try:
        await qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"user_id": user_id, "kyc_string": text}
                )
            ]
        )
        logger.info(f"Upserted vector for {user_id} into Qdrant")
    except Exception as e:
        logger.error(f"Qdrant Upsert Error: {e}")
