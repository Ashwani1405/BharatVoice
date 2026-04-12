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
