import json
import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.services.voice import session_manager, vapi_client
from app.api.voice.webhook_handler import (
    verify_webhook_signature,
    handle_assistant_request,
    handle_function_call,
    handle_end_of_call,
    handle_transcript
)
from app.database import fetch_one

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["voice"])

class StartCallRequest(BaseModel):
    user_id: str
    language: str = "hi"

    model_config = {
        "json_schema_extra": {
            "example": {"user_id": "uuid-here", "language": "hi"}
        }
    }


@router.post("/webhook")
async def vapi_webhook(request: Request):
    """
    Main VAPI webhook receiver. Validates and dispatches lifecycle events.
    """
    try:
        body_bytes = await request.body()
        signature = request.headers.get("X-Vapi-Signature")
        
        if signature:
            is_valid = await verify_webhook_signature(body_bytes, signature)
            if not is_valid:
                return JSONResponse(status_code=401, content={"detail": "Invalid webhook signature"})
        else:
            if settings.ENVIRONMENT != "development":
                return JSONResponse(status_code=401, content={"detail": "Missing signature"})
                
        body = await request.json()
        message_obj = body.get("message", {})
        message_type = message_obj.get("type")
        call_obj = message_obj.get("call", {})
        call_id = call_obj.get("id", "unknown_call")
        
        # Route dispatch
        if message_type == "assistant-request":
            response_json = await handle_assistant_request(call_id, body)
            return JSONResponse(content=response_json)
            
        elif message_type == "function-call":
            response_json = await handle_function_call(call_id, body)
            return JSONResponse(content=response_json)
            
        elif message_type == "end-of-call-report":
            await handle_end_of_call(call_id, body)
            return {"status": "ok"}
            
        elif message_type == "transcript":
            await handle_transcript(call_id, body)
            return {"status": "ok"}
            
        else:
            logger.info(f"Unhandled VAPI webhook message type: {message_type}")
            return {"status": "ok"}
            
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        # NEVER return 500 — Vapi will just needlessly DDOS retry us
        return JSONResponse(status_code=200, content={"status": "error", "detail": str(e)})


@router.post("/call/start")
async def start_call(payload: StartCallRequest):
    """
    Initiates a new Web RTC call structure and returns tokenized URLs.
    """
    # 1. Fetch user (using simple fetch_one wrapper)
    # user_row = await fetch_one("SELECT * FROM users WHERE id = :uid", {"uid": payload.user_id})
    # if not user_row:
    #     raise HTTPException(status_code=404, detail="User not found")
        
    # 2. existing call check
    existing = await vapi_client.get_active_call_for_user(payload.user_id)
    if existing:
        raise HTTPException(
            status_code=409, 
            detail={"message": "Active call already in progress", "call_id": existing}
        )
        
    # 3. Create Web call
    call_res = await vapi_client.create_web_call(payload.user_id, payload.language)
    call_id = call_res["id"]
    web_call_url = call_res.get("webCallUrl", "")
    
    # 4. Redis session state
    await session_manager.create_session(call_id, payload.user_id, payload.language)
    
    # 5. Audit logs
    # execute(...) # to be finalized
    
    return {
        "call_id": call_id,
        "web_call_url": web_call_url,
        "session_id": call_id, 
        "language": payload.language
    }

@router.get("/call/{call_id}/status")
async def check_call_status(call_id: str):
    """
    Combine internal session state with remote VAPI status.
    """
    session = await session_manager.get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    try:
        vapi_status = await vapi_client.get_call_status(call_id)
        remote_state = vapi_status.get("status", "unknown")
    except Exception:
        remote_state = "error fetching"
        
    missing = await session_manager.get_missing_fields(call_id)
    is_complete = await session_manager.is_session_complete(call_id)
    turns_count = len(json.loads(session.get("turns", "[]")))
    
    return {
        "call_id": call_id,
        "status": remote_state,
        "fields_collected": json.loads(session.get("fields_collected", "{}")),
        "missing_fields": missing,
        "is_complete": is_complete,
        "turns_count": turns_count,
        "language": session.get("language")
    }

@router.delete("/call/{call_id}")
async def force_end_call(call_id: str):
    """
    Client initiates a hangup gracefully, clearing state safely.
    """
    ended = await vapi_client.end_call(call_id)
    await session_manager.mark_failed(call_id, "user_requested_end")
    
    return {
        "success": ended, 
        "message": "Call ended" if ended else "Call already ended"
    }

@router.get("/calls")
async def list_global_calls(limit: int = 20):
    """
    Admin diagnostic tool to enumerate active calls and sessions.
    """
    calls = await vapi_client.list_calls(limit)
    enriched_calls = []
    
    for c in calls:
        cid = c.get("id")
        sess = await session_manager.get_session(cid) if cid else None
        c["session_data"] = sess
        enriched_calls.append(c)
        
    return enriched_calls
