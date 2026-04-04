# Pull Request 1: Foundation (Session & Language Routing)

**Assigned to:** Ashwani  
**Branch Name:** `feat/sprint2-foundation`

---

## PR Title
`feat(voice): sprint 2 foundation - session manager and language router`

## PR Description

### ## Summary
This PR sets up the foundational backend infrastructure required for the Sprint 2 Voice Agent. It introduces a Redis-backed session manager to maintain state during KYC calls and a language router to support dynamic switching between Hindi and English prompts.

### ## Changes
- Created `session_manager.py` to handle `voice_session:{call_id}` state in Redis (TTL 1800s).
- Created `language_router.py` to detect languages and route prompts for Deepgram/ElevenLabs.
- Created empty `prompts/__init__.py`.
- Updated `config.py` to add new Sprint 2 voice environment variables (Groq, VAPI, ElevenLabs).
- Updated `.env.example` with detailed instructions for the new API keys.
- Added new targets to the `Makefile` (`restart-backend`, `groq-test`, `ngrok`).

### ## How to test
1. Run `make groq-test` to ensure Groq authentication is functioning.
2. Ensure you have copied `.env.example` to `.env` and populated fake/test keys.
3. Bring the stack up using `docker compose up -d` to verify no startup crashes.

### ## Dependencies
None. This is the foundation PR and must be merged before others.

### ## Definition of Done
- No blocking code in async functions.
- Fully type-hinted methods.
- Session manager saves data successfully using `redis_client`.

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

### 1. `apps/backend/app/services/voice/session_manager.py` (NEW)
```python
import json
import logging
from datetime import datetime
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

async def create_session(call_id: str, user_id: str, language: str) -> dict:
    session_key = f"voice_session:{call_id}"
    now = datetime.utcnow().isoformat()
    
    session_data = {
        "call_id": call_id,
        "user_id": user_id,
        "language": language,
        "status": "active",
        "fields_collected": json.dumps({
            "name": None,
            "dob": None,
            "phone": None,
            "aadhaar_number": None,
            "pan_number": None,
            "address": None
        }),
        "turns": json.dumps([]),
        "created_at": now,
        "updated_at": now
    }
    
    redis_client.hset(session_key, mapping=session_data)
    redis_client.expire(session_key, 1800)  # 30 mins TTL
    logger.info(f"Session created for call {call_id} (User: {user_id})")
    return session_data

async def get_session(call_id: str) -> dict | None:
    session_key = f"voice_session:{call_id}"
    data = redis_client.hgetall(session_key)
    
    if not data:
        return None
        
    return {
        k.decode('utf-8') if isinstance(k, bytes) else k: 
        v.decode('utf-8') if isinstance(v, bytes) else v 
        for k, v in data.items()
    }

async def update_field(call_id: str, field_name: str, value: str) -> dict:
    valid_fields = {"name", "dob", "phone", "aadhaar_number", "pan_number", "address"}
    if field_name not in valid_fields:
        raise ValueError(f"Invalid field name: {field_name}")

    session_key = f"voice_session:{call_id}"
    session = await get_session(call_id)
    if not session:
        raise ValueError(f"Session not found for call: {call_id}")

    fields_collected = json.loads(session["fields_collected"])
    fields_collected[field_name] = value

    redis_client.hset(session_key, "fields_collected", json.dumps(fields_collected))
    redis_client.hset(session_key, "updated_at", datetime.utcnow().isoformat())
    
    return await get_session(call_id)

async def append_turn(call_id: str, role: str, content: str) -> None:
    session_key = f"voice_session:{call_id}"
    session = await get_session(call_id)
    if not session:
        return

    turns = json.loads(session["turns"])
    turns.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Keep only last 50 turns
    if len(turns) > 50:
        turns = turns[-50:]
        
    redis_client.hset(session_key, "turns", json.dumps(turns))
    redis_client.hset(session_key, "updated_at", datetime.utcnow().isoformat())

async def mark_complete(call_id: str) -> dict:
    session_key = f"voice_session:{call_id}"
    redis_client.hset(session_key, "status", "completed")
    redis_client.hset(session_key, "updated_at", datetime.utcnow().isoformat())
    return await get_session(call_id)

async def mark_failed(call_id: str, reason: str) -> None:
    session_key = f"voice_session:{call_id}"
    redis_client.hset(session_key, "status", "failed")
    redis_client.hset(session_key, "failure_reason", reason)
    redis_client.hset(session_key, "updated_at", datetime.utcnow().isoformat())

async def get_missing_fields(call_id: str) -> list[str]:
    session = await get_session(call_id)
    if not session:
        return []
        
    fields = json.loads(session["fields_collected"])
    ordered_checks = ["name", "dob", "phone", "aadhaar_number", "pan_number", "address"]
    
    return [field for field in ordered_checks if fields.get(field) is None]

async def is_session_complete(call_id: str) -> bool:
    session = await get_session(call_id)
    if not session:
        return False
        
    fields = json.loads(session["fields_collected"])
    required_fields = ["name", "dob", "phone", "aadhaar_number", "address"]
    
    return all(fields.get(field) is not None for field in required_fields)

async def delete_session(call_id: str) -> None:
    redis_client.delete(f"voice_session:{call_id}")

async def get_all_active_sessions() -> list[dict]:
    sessions = []
    # Using scan_iter to prevent blocking the Redis thread
    for key in redis_client.scan_iter(match="voice_session:*"):
        data = redis_client.hgetall(key)
        if data:
            decoded = {
                k.decode('utf-8') if isinstance(k, bytes) else k: 
                v.decode('utf-8') if isinstance(v, bytes) else v 
                for k, v in data.items()
            }
            if decoded.get("status") == "active":
                sessions.append(decoded)
    return sessions
```

### 2. `apps/backend/app/services/voice/language_router.py` (NEW)
```python
from pathlib import Path
from app.config import settings

SUPPORTED_LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "deepgram_code": "hi",
        "elevenlabs_voice_id": settings.ELEVENLABS_VOICE_ID_HINDI,
        "greeting": "Namaste! Main BharatVoice se bol raha hoon.",
        "farewell": "Dhanyavaad! Aapka din shubh ho."
    },
    "en": {
        "name": "English (Indian)",
        "deepgram_code": "en-IN",
        "elevenlabs_voice_id": settings.ELEVENLABS_VOICE_ID_ENGLISH,
        "greeting": "Hello! Welcome to BharatVoice.",
        "farewell": "Thank you! Have a great day."
    }
}

def detect_language(text: str) -> str:
    """
    Count characters in Devanagari Unicode block U+0900–U+097F.
    If devanagari_count / total_chars > 0.2: return 'hi'
    Else: return 'en'
    Edge case: empty string returns 'hi'.
    """
    if not text.strip():
        return "hi"
        
    devanagari_count = sum(1 for char in text if '\u0900' <= char <= '\u097F')
    if (devanagari_count / len(text)) > 0.2:
        return "hi"
    return "en"

def get_voice_id(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")
    return SUPPORTED_LANGUAGES[language]["elevenlabs_voice_id"]

def get_deepgram_language(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")
    return SUPPORTED_LANGUAGES[language]["deepgram_code"]

def get_greeting(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")
    return SUPPORTED_LANGUAGES[language]["greeting"]

def get_farewell(language: str) -> str:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")
    return SUPPORTED_LANGUAGES[language]["farewell"]

def load_prompt_template(language: str) -> str:
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / f"kyc_{language}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt file for language '{language}' at {prompt_path}")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def get_supported_languages() -> list[str]:
    return ["hi", "en"]
```

### 3. `apps/backend/app/prompts/__init__.py` (NEW)
```python
"""KYC conversation prompt templates for VAPI agent."""
```

### 4. `apps/backend/app/config.py` (MODIFY)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str

    # Voice & transcription
    VAPI_API_KEY: str
    VAPI_PHONE_NUMBER_ID: str
    DEEPGRAM_API_KEY: str
    ELEVENLABS_API_KEY: str
    
    # LLM Settings
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = ""
    
    # Voice IDs
    ELEVENLABS_VOICE_ID_HINDI: str
    ELEVENLABS_VOICE_ID_ENGLISH: str
    
    # Webhooks
    VAPI_WEB_TOKEN: str
    VAPI_WEBHOOK_SECRET: str
    NGROK_PUBLIC_URL: str = "http://localhost:8000"

    # KYC & Identity
    AADHAAR_CLIENT_ID: str
    AADHAAR_CLIENT_SECRET: str
    
    # Cloud Storage
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str

    # Payments
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str

    # Vector DB & Streaming
    QDRANT_URL: str
    QDRANT_API_KEY: str
    PATHWAY_API_KEY: str

    # Tasks
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Frontend
    FRONTEND_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

### 5. `.env.example` (MODIFY)
**Append** the following to your existing `.env.example`:

```bash
# ── Groq LLM (free — console.groq.com) ─────────────────────────────────────
# Set this key ONCE in VAPI Dashboard → Settings → Providers → Groq
# Also used for direct Groq calls in Sprint 3 (OCR validation) and Sprint 4
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

# OpenAI — not used in Sprint 2, kept as optional fallback
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

# ── ElevenLabs Voice IDs ────────────────────────────────────────────────────
# Find voice IDs at: elevenlabs.io/voice-library
# Recommended Hindi voices: search "Hindi" or "Aria" in the library
# Recommended Indian English: search "Indian" or use "Callum"
ELEVENLABS_VOICE_ID_HINDI=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_VOICE_ID_ENGLISH=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── VAPI Web Token ──────────────────────────────────────────────────────────
# DIFFERENT from VAPI_API_KEY — this is safe to expose in browser
# Get from: vapi.ai/dashboard → Account → Web Token (not API Keys)
VAPI_WEB_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Webhook Security ────────────────────────────────────────────────────────
# Make up any random 32-character string — you choose this value
# VAPI will use it to sign all webhook payloads to your server
VAPI_WEBHOOK_SECRET=your_random_32_char_secret_here_xxxx

# ── Local Development Tunnel ────────────────────────────────────────────────
# Run: make ngrok → copy the https:// URL → paste here → make restart-backend
# Required so VAPI can reach your local server via webhooks
NGROK_PUBLIC_URL=https://xxxxxxxx.ngrok.io
```

### 6. `Makefile` (MODIFY)
**Append** the following targets to your existing `Makefile`:

```makefile
restart-backend:
	docker compose restart backend

groq-test:
	@echo "Testing Groq API connection..."
	@curl -s -X POST https://api.groq.com/openai/v1/chat/completions \
	  -H "Authorization: Bearer $${GROQ_API_KEY}" \
	  -H "Content-Type: application/json" \
	  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"Say namaste in one word."}],"max_tokens":10}' \
	  | python3 -m json.tool

ngrok:
	ngrok http 8000
```
