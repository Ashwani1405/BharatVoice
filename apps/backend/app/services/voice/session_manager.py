"""
Session Manager for Voice
Manages the state of KYC calls in Redis.
"""
import json
import logging
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

SESSION_EXPIRE = 3600  # 1 hour

REQUIRED_FIELDS = ["name", "dob", "address", "aadhaar_number"]

async def create_session(call_id: str, user_id: str, language: str):
    """Initializes a new session in Redis."""
    session_data = {
        "user_id": user_id,
        "language": language,
        "status": "in_progress",
        "turns": "[]",
        "fields_collected": "{}"
    }
    
    # Store hash in redis
    try:
        redis_client.hset(f"call:{call_id}", mapping=session_data)
        redis_client.expire(f"call:{call_id}", SESSION_EXPIRE)
        logger.info(f"Created voice session for call {call_id}")
    except Exception as e:
        logger.error(f"Redis error creating session: {e}")


async def get_session(call_id: str) -> dict:
    """Retrieves session state from Redis."""
    try:
        data = redis_client.hgetall(f"call:{call_id}")
        return data if data else {}
    except Exception as e:
        logger.error(f"Redis error getting session: {e}")
        return {}


async def get_missing_fields(call_id: str) -> list:
    """Determines what KYC fields remain to be collected."""
    session = await get_session(call_id)
    if not session:
        return REQUIRED_FIELDS
        
    collected_str = session.get("fields_collected", "{}")
    try:
        collected = json.loads(collected_str)
    except json.JSONDecodeError:
        collected = {}
        
    missing = [f for f in REQUIRED_FIELDS if f not in collected or not collected[f]]
    return missing


async def is_session_complete(call_id: str) -> bool:
    """Checks if all required fields are collected."""
    missing = await get_missing_fields(call_id)
    return len(missing) == 0


async def mark_failed(call_id: str, reason: str):
    """Marks a session as failed/ended prematurely."""
    try:
        redis_client.hset(f"call:{call_id}", "status", "failed")
        redis_client.hset(f"call:{call_id}", "failure_reason", reason)
        logger.info(f"Marked call {call_id} as failed: {reason}")
    except Exception as e:
        logger.error(f"Redis error marking fail: {e}")

async def save_kyc_field(call_id: str, field_name: str, value: str):
    """Updates a collected field in the session."""
    session = await get_session(call_id)
    if not session:
        return
        
    collected_str = session.get("fields_collected", "{}")
    try:
        collected = json.loads(collected_str)
    except json.JSONDecodeError:
        collected = {}
        
    collected[field_name] = value
    
    try:
        redis_client.hset(f"call:{call_id}", "fields_collected", json.dumps(collected))
        logger.info(f"Call {call_id} updated field {field_name}")
    except Exception as e:
        logger.error(f"Redis error saving field: {e}")
