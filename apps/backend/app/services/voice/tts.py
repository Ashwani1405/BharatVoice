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
