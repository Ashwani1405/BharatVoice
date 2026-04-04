# Pull Request 2: VAPI Agent Engine

**Assigned to:** Vikram Aditya Verma  
**Branch Name:** `feat/sprint2-vapi-agent`

---

## PR Title
`feat(voice): sprint 2 - vapi client and groq fallback agent config`

## PR Description

### ## Summary
This PR replaces the VAPI client stub with a fully-featured async HTTPx wrapper for Vapi.ai API calls. It also creates the central agent config factory (`agent_config.py`) that returns the Groq Llama-3.3-70b-versatile voice assistant payload, complete with function calling schemas for extracting KYC fields out of conversations.

### ## Changes
- Created `vapi_client.py` connecting to `https://api.vapi.ai` via async `httpx`.
- Created `agent_config.py` including strict `LLAMA_TOOL_CALL_REMINDER` constraints to force the LLM to adhere to the 2-sentence conversational voice limits.
- Configured functional tools: `save_kyc_field` and `confirm_and_complete` within the payload.
- Added `groq` to `requirements.txt` for direct API fallback validation.

### ## How to test
1. Run `pnpm install` in root if necessary.
2. Check that the VAPI token is set in `.env`.
3. Try starting a mock test script hitting `vapi_client.get_calls()` manually (or wait for the Webhooks PR).

### ## Dependencies
**Depends on:** `feat/sprint2-foundation` (PR-1). Must be merged into main first!

### ## Definition of Done
- All Python functions have type hints.
- Groq is exclusively targeted.
- Redis mapping for calls is active.

---

## Reviewers Checklist
- [ ] No npm or yarn commands anywhere
- [ ] No hardcoded API keys or secrets
- [ ] All Python functions have type hints
- [ ] All async functions use await (no blocking calls)
- [ ] Error states handled — no unhandled promise rejections
- [ ] Imports use absolute paths (`app.*`) not relative
- [ ] docker compose up still works after this PR

---

## Files to Create/Modify

### 1. `apps/backend/app/services/voice/vapi_client.py` (REPLACE)
```python
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
```

### 2. `apps/backend/app/services/voice/agent_config.py` (NEW)
```python
from app.config import settings
from app.services.voice.language_router import (
    load_prompt_template, get_voice_id, 
    get_deepgram_language, get_greeting, get_farewell
)

LLAMA_TOOL_CALL_REMINDER = """

CRITICAL RULES FOR VOICE — FOLLOW EXACTLY:
1. Maximum 2 sentences per response. Stop after 2 sentences.
2. After user confirms any field value, IMMEDIATELY call save_kyc_field. Do not ask another question first.
3. Never ask more than one question per response.
4. If user says they don't know or are confused, simplify and try once more, then move on.
5. Never use bullet points, lists, or markdown — this is a voice call.
6. Speak naturally. Short sentences. Simple words.
"""

def build_agent(language: str = "hi") -> dict:
    """
    Build complete VAPI assistant config for Groq/Llama.
    NOTE: Groq API key is NOT passed here. Configure it once in:
    VAPI Dashboard → Settings → Providers → Groq
    """
    system_prompt = load_prompt_template(language) + LLAMA_TOOL_CALL_REMINDER
    
    return {
        "name": "BharatVoice KYC Agent",
        "model": {
            "provider": "groq",
            "model": settings.GROQ_MODEL,
            "temperature": 0.2,
            "maxTokens": 300,
            "systemPrompt": system_prompt,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "save_kyc_field",
                        "description": (
                            "Save a KYC field after user has confirmed the value. "
                            "Call this IMMEDIATELY after user confirms. "
                            "Do not wait or ask another question first."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "field_name": {
                                    "type": "string",
                                    "enum": ["name", "dob", "phone", 
                                             "aadhaar_number", "pan_number", "address"],
                                    "description": "The KYC field being saved"
                                },
                                "value": {
                                    "type": "string",
                                    "description": "Confirmed value exactly as spoken"
                                }
                            },
                            "required": ["field_name", "value"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "confirm_and_complete",
                        "description": (
                            "Call ONLY when ALL required fields are collected AND "
                            "user has explicitly confirmed the final summary with "
                            "yes/haan/sahi hai."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
            ]
        },
        "voice": {
            "provider": "elevenlabs",
            "voiceId": get_voice_id(language),
            "model": "eleven_multilingual_v2",
            "stability": 0.5,
            "similarityBoost": 0.75
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": get_deepgram_language(language),
            "smartFormat": True,
            "endpointing": 300
        },
        "firstMessage": get_greeting(language),
        "endCallMessage": get_farewell(language),
        "recordingEnabled": False,
        "maxDurationSeconds": 600,
        "backgroundSound": "off",
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.5,
        "serverUrl": f"{settings.NGROK_PUBLIC_URL}/api/voice/webhook",
        "serverUrlSecret": settings.VAPI_WEBHOOK_SECRET
    }
```

### 3. `apps/backend/requirements.txt` (MODIFY)
**Append** the following package:
```text
groq==0.9.0
```
