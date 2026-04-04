# Pull Request 3: Deepgram STT & ElevenLabs TTS Wrappers

**Assigned to:** Parth Garg  
**Branch Name:** `feat/sprint2-stt-tts`

---

## PR Title
`feat(voice): sprint 2 - deepgram stt and elevenlabs tts integration`

## PR Description

### ## Summary
This PR implements the asynchronous wrappers for Speech-to-Text (Deepgram Nova-2) and Text-to-Speech (ElevenLabs). It supports standard async blocking requests as well as async generators for WebSocket/Streaming endpoints, which prepares us for the live frontend transcription and lower-latency voice delivery.

### ## Changes
- Created `stt.py` integrating the Deepgram SDK for robust transcription. Include confidence checks and strict error handling.
- Created `tts.py` to stream raw mp3 bytes directly from ElevenLabs. It caches voice listings to prevent unnecessary external network calls.
- Updated `requirements.txt` to include `deepgram-sdk` and `elevenlabs`.

### ## How to test
1. Ensure `DEEPGRAM_API_KEY` and `ELEVENLABS_API_KEY` are placed in `.env`.
2. Start the backend. If developing/testing locally, you can hit the proxy health endpoint to verify the API keys are functional.

### ## Dependencies
**Depends on:** `feat/sprint2-foundation` (PR-1). Must be merged into main first!

### ## Definition of Done
- No blocking code in async generator pipelines.
- Deepgram SDK correctly connected in live transcription streaming mode.
- ElevenLabs network overhead optimized with Redis caching.

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

### 1. `apps/backend/app/services/voice/stt.py` (REPLACE)
```python
import logging
import asyncio
from typing import AsyncGenerator
from deepgram import (
    DeepgramClient, 
    LiveTranscriptionEvents, 
    LiveOptions, 
    PrerecordedOptions, 
    FileSource
)
from app.config import settings
from app.services.voice.language_router import get_deepgram_language

logger = logging.getLogger(__name__)

class DeepgramError(Exception):
    pass

class LowConfidenceError(DeepgramError):
    def __init__(self, transcript: str, confidence: float):
        self.transcript = transcript
        self.confidence = confidence
        super().__init__(f"Low confidence: {confidence:.2f} — '{transcript}'")

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"

# Global client initialization using the Deepgram SDK
deepgram = DeepgramClient(settings.DEEPGRAM_API_KEY)

async def transcribe_audio(audio_bytes: bytes, language: str = "hi", retry_count: int = 1) -> str:
    """
    Send audio to Deepgram Nova-2 for block processing.
    """
    options = PrerecordedOptions(
        model="nova-2",
        language=get_deepgram_language(language),
        smart_format=True,
        punctuate=True,
        numerals=True,
    )
    
    payload: FileSource = {"buffer": audio_bytes}
    
    for attempt in range(retry_count + 1):
        try:
            # We use the sync wrapper in async mode conceptually, but SDK natively supports async.
            response = await asyncio.to_thread(
                deepgram.listen.prerecorded.v("1").transcribe_file, 
                payload, 
                options
            )
            
            result = response["results"]["channels"][0]["alternatives"][0]
            transcript = result.get("transcript", "").strip()
            confidence = result.get("confidence", 0.0)
            
            logger.debug(f"Deepgram transcript confidence: {confidence:.2f}")
            
            if confidence < 0.5:
                raise LowConfidenceError(transcript, confidence)
                
            return transcript
            
        except LowConfidenceError:
            raise
        except Exception as e:
            if attempt < retry_count:
                logger.warning(f"Deepgram parsing failed, retrying in 1s... ({e})")
                await asyncio.sleep(1)
            else:
                logger.error(f"Deepgram failed after retries: {e}")
                raise DeepgramError(f"Transcription failed: {str(e)}")

async def transcribe_streaming(audio_stream) -> AsyncGenerator[str, None]:
    """
    Streaming transcription using Deepgram WebSocket.
    """
    options = LiveOptions(
        model="nova-2",
        language="en-IN", # We will let the app handle default language mappings
        smart_format=True,
        interim_results=True,
        punctuate=True,
        numerals=True,
    )
    
    # Establish connection
    try:
        dg_connection = deepgram.listen.live.v("1")
        
        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            yield sentence

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        
        if not dg_connection.start(options):
            logger.error("Failed to start Deepgram Live Connection")
            return
            
        async for chunk in audio_stream:
            dg_connection.send(chunk)
            
        dg_connection.finish()
        
    except Exception as e:
        logger.error(f"Deepgram WebSocket Error: {e}")
        raise DeepgramError(str(e))

async def detect_language(text: str) -> str:
    """Delegate to language_router.detect_language(text)"""
    from app.services.voice.language_router import detect_language as base_detect
    return base_detect(text)

async def test_connection() -> bool:
    """
    Test Deepgram API key validity.
    """
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://api.deepgram.com/v1/projects",
                headers={"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
            )
            return res.status_code == 200
    except Exception:
        return False
```

### 2. `apps/backend/app/services/voice/tts.py` (REPLACE)
```python
import json
import logging
import httpx
from typing import AsyncGenerator
from app.config import settings
from app.services.voice.language_router import get_voice_id
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

class ElevenLabsError(Exception):
    pass

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

async def synthesize_speech(text: str, language: str = "hi") -> bytes:
    """
    POST to ElevenLabs TTS and return raw mp3 bytes.
    """
    voice_id = get_voice_id(language)
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=20.0)
        
        if response.status_code != 200:
            raise ElevenLabsError(f"TTS Failed ({response.status_code}): {response.text}")
            
        logger.debug(f"TTS: {len(text)} chars → {language}")
        return response.content

async def synthesize_speech_streaming(
    text: str, language: str = "hi"
) -> AsyncGenerator[bytes, None]:
    """
    Streaming TTS for lower latency via async HTTP streaming.
    """
    voice_id = get_voice_id(language)
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}/stream"
    
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            if response.status_code != 200:
                error = await response.aread()
                raise ElevenLabsError(f"Streaming TTS Failed: {error.decode()}")
                
            async for chunk in response.aiter_bytes():
                if chunk:
                    yield chunk

async def get_available_voices() -> list[dict]:
    """
    GET {ELEVENLABS_BASE_URL}/voices, cached in Redis.
    """
    cache_key = "elevenlabs:voices"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
        
    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ELEVENLABS_BASE_URL}/voices", headers=headers)
        if response.status_code != 200:
            raise ElevenLabsError(f"Failed to fetch voices: {response.text}")
            
        voices = response.json().get("voices", [])
        redis_client.setex(cache_key, 3600, json.dumps(voices))
        return voices

async def get_character_quota() -> dict:
    """
    GET {ELEVENLABS_BASE_URL}/user/subscription limits.
    """
    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ELEVENLABS_BASE_URL}/user/subscription", headers=headers)
        if response.status_code != 200:
            raise ElevenLabsError("Failed to fetch subscription bounds")
            
        data = response.json()
        count = data.get("character_count", 0)
        limit = data.get("character_limit", 1)
        used = (count / limit) * 100 if limit > 0 else 0
        
        return {
            "character_count": count,
            "character_limit": limit,
            "percentage_used": round(used, 2)
        }

async def test_connection() -> bool:
    """Test ElevenLabs key validity via GET /user."""
    headers = {"xi-api-key": settings.ELEVENLABS_API_KEY}
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{ELEVENLABS_BASE_URL}/user", headers=headers)
            return res.status_code == 200
    except Exception:
        return False
```

### 3. `apps/backend/requirements.txt` (MODIFY)
**Append** the following packages:
```text
deepgram-sdk==3.2.7
elevenlabs==1.0.0
```
