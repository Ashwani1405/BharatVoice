import hmac
import hashlib
import json
import logging
from datetime import datetime
from app.config import settings
from app.services.voice import session_manager, vapi_client
from app.services.voice.agent_config import build_agent
from app.services.voice.language_router import detect_language
# Using the placeholder database execute here (update tables imports as schema evolves)
from app.database import execute 
from app.tasks.kyc_tasks import initiate_kyc_verification

logger = logging.getLogger(__name__)

async def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify the VAPI Webhook cryptographic signature to prevent tampering.
    """
    if not signature:
        return False
        
    secret = settings.VAPI_WEBHOOK_SECRET.encode("utf-8")
    computed_signature = hmac.new(
        secret, msg=body, digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)

async def handle_assistant_request(call_id: str, payload: dict) -> dict:
    """
    Fired at call start — VAPI asks which assistant configuration to use.
    """
    from app.redis_client import redis_client
    
    user_id_raw = redis_client.get(f"vapi_call:{call_id}")
    user_id = user_id_raw.decode("utf-8") if user_id_raw else "anonymous_user"
    
    session = await session_manager.get_session(call_id)
    language = session["language"] if session else "hi"
    
    if not session and user_id == "anonymous_user":
        await session_manager.create_session(call_id, user_id, language)
        
    assistant = build_agent(language)
    logger.info(f"Built agent configuration for call {call_id} (lang: {language})")
    
    return {"assistant": assistant}

async def handle_function_call(call_id: str, payload: dict) -> dict:
    """
    Fired when the LLM triggers a tool call like save_kyc_field.
    """
    from app.redis_client import redis_client
    
    msg_obj = payload.get("message", {})
    function_call = msg_obj.get("functionCall", {})
    function_name = function_call.get("name")
    parameters = function_call.get("parameters", {})
    
    if function_name == "save_kyc_field":
        field_name = parameters.get("field_name")
        value = parameters.get("value")
        
        # 1. Update session redis
        await session_manager.update_field(call_id, field_name, value)
        
        # 2. Update postgres user (if applicable)
        user_id_raw = redis_client.get(f"vapi_call:{call_id}")
        if user_id_raw and field_name in ("name", "phone"):
            uid = user_id_raw.decode("utf-8")
            # execute(f"UPDATE users SET {field_name} = :val WHERE id = :id", {"val": value, "id": uid})
            pass # Keep it safe until table structure finalized
            
        # 3. Check completeness
        is_complete = await session_manager.is_session_complete(call_id)
        if is_complete:
            if user_id_raw:
                uid = user_id_raw.decode("utf-8")
                logger.info(f"All KYC fields collected for user {uid}")
                initiate_kyc_verification.delay(uid) # Trigger celery
                
        # 4. Construct tool response
        missing = await session_manager.get_missing_fields(call_id)
        if missing:
            return {"result": f"Saved {field_name}. Remaining: {missing}"}
        else:
            return {"result": f"Saved {field_name}. All fields collected!"}
            
    elif function_name == "confirm_and_complete":
        await session_manager.mark_complete(call_id)
        logger.info(f"KYC call {call_id} successfully confirmed and completed by user.")
        return {"result": "KYC submitted. You will receive an SMS confirmation shortly."}
        
    logger.warning(f"Unknown LLM function call triggered: {function_name}")
    return {"result": "unknown function"}

async def handle_end_of_call(call_id: str, payload: dict) -> None:
    """
    Fired when the web call connection terminates.
    """
    from app.redis_client import redis_client
    
    session = await session_manager.get_session(call_id)
    if not session:
        logger.warning(f"Call {call_id} ended but no session was found in Redis.")
        return
        
    started_at = datetime.fromisoformat(session["created_at"])
    now = datetime.utcnow()
    duration_seconds = (now - started_at).seconds
    
    fields_collected = json.loads(session.get("fields_collected", "{}"))
    non_null_fields = sum(1 for k, v in fields_collected.items() if v is not None)
    
    audit_data = {
        "user_id": session["user_id"],
        "action": "voice_call_ended",
        "metadata": json.dumps({
            "call_id": call_id,
            "duration_seconds": duration_seconds,
            "fields_collected_count": non_null_fields,
            "status": session["status"],
            "language": session["language"]
        })
    }
    
    # execute("INSERT INTO audit_logs (user_id, action, metadata) VALUES (:user_id, :action, :metadata)", audit_data)
    
    if session["status"] != "completed":
        await session_manager.mark_failed(call_id, "call_ended_before_completion")
        
    await session_manager.delete_session(call_id)
    redis_client.delete(f"vapi_call:{call_id}")
    redis_client.delete(f"vapi_user:{session['user_id']}")

async def handle_transcript(call_id: str, payload: dict) -> None:
    """
    Fired after each interaction buffer passes.
    """
    from app.redis_client import redis_client
    
    msg_obj = payload.get("message", {})
    transcript = msg_obj.get("transcript", "")
    role = msg_obj.get("role", "user")
    
    if not transcript:
        return
        
    detected_lang = detect_language(transcript)
    session = await session_manager.get_session(call_id)
    
    if session and session["language"] != detected_lang and len(transcript) > 20:
        redis_client.hset(f"voice_session:{call_id}", "language", detected_lang)
        logger.info(f"Language auto-switch detected for {call_id} -> {detected_lang}")
        
    await session_manager.append_turn(call_id, role, transcript)
