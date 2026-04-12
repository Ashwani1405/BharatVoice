import httpx
import logging
from app.config import settings
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

class VAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"VAPI Error {status_code}: {message}")

VAPI_BASE_URL = "https://api.vapi.ai"

async def _get_client() -> httpx.AsyncClient:
    """Return configured httpx client. Use as async context manager."""
    return httpx.AsyncClient(
        base_url=VAPI_BASE_URL,
        headers={"Authorization": f"Bearer {settings.VAPI_API_KEY}"},
        timeout=30.0
    )

async def create_web_call(user_id: str, language: str = "hi") -> dict:
    """
    POST /call/web to VAPI.
    """
    from app.services.voice.agent_config import build_agent
    
    payload = {
        "assistant": build_agent(language)
    }
    
    async with await _get_client() as client:
        response = await client.post("/call/web", json=payload)
        
        if response.status_code not in (200, 201):
            raise VAPIError(response.status_code, response.text)
            
        data = response.json()
        call_id = data["id"]
        
        # Store reverse lookups in Redis
        redis_client.setex(f"vapi_call:{call_id}", 3600, user_id)
        redis_client.setex(f"vapi_user:{user_id}", 3600, call_id)
        
        logger.info(f"Created web call {call_id} for user {user_id}")
        return data

async def get_call_status(call_id: str) -> dict:
    """
    GET /call/{call_id}
    """
    async with await _get_client() as client:
        response = await client.get(f"/call/{call_id}")
        if response.status_code != 200:
            raise VAPIError(response.status_code, response.text)
        return response.json()

async def end_call(call_id: str) -> bool:
    """
    DELETE /call/{call_id}
    """
    async with await _get_client() as client:
        response = await client.delete(f"/call/{call_id}")
        
        if response.status_code == 404:
            return False
            
        if response.status_code not in (200, 201, 204):
            raise VAPIError(response.status_code, response.text)
            
        # Clean up mapping
        user_id = redis_client.get(f"vapi_call:{call_id}")
        if user_id:
            user_id_str = user_id.decode("utf-8") if isinstance(user_id, bytes) else user_id
            redis_client.delete(f"vapi_user:{user_id_str}")
            
        redis_client.delete(f"vapi_call:{call_id}")
        return True

async def list_calls(limit: int = 20) -> list[dict]:
    """GET /call?limit={limit}&sortOrder=desc"""
    async with await _get_client() as client:
        response = await client.get("/call", params={"limit": limit, "sortOrder": "desc"})
        if response.status_code != 200:
            raise VAPIError(response.status_code, response.text)
        return response.json()

async def get_active_call_for_user(user_id: str) -> str | None:
    """
    Look up "vapi_user:{user_id}" in Redis.
    """
    call_id = redis_client.get(f"vapi_user:{user_id}")
    if not call_id:
        return None
    return call_id.decode("utf-8") if isinstance(call_id, bytes) else call_id

async def call_groq_direct(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 500
) -> str:
    """
    Direct Groq API call using OpenAI-compatible endpoint.
    Used for OCR text extraction validation and fraud reasoning mapping.
    """
    target_model = model or settings.GROQ_MODEL
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=20.0)
        
        if response.status_code != 200:
            raise VAPIError(response.status_code, f"Groq Direct API error: {response.text}")
            
        json_resp = response.json()
        return json_resp["choices"][0]["message"]["content"]
