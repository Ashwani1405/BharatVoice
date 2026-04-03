"""
Sprint 2 — Speech-to-Text Service
Converts raw audio bytes received from VAPI webhooks into text using Deepgram Nova-2.
Handles Hindi, English, and code-switched Hindi-English speech.
"""
# TODO: Sprint 2 — implement this module

import httpx
from typing import Optional

async def transcribe_audio(audio_bytes: bytes, language: str = "hi") -> str:
    """
    Send audio bytes to Deepgram Nova-2 and return the transcript.
    
    Args:
        audio_bytes: Raw audio data from VAPI (16kHz, mono, PCM16)
        language: BCP-47 language code. "hi" for Hindi, "en-IN" for Indian English
    
    Returns:
        Transcribed text string
    
    Raises:
        DeepgramError: if transcription fails or confidence < 0.6
    
    API: POST https://api.deepgram.com/v1/listen
    Docs: https://developers.deepgram.com/reference/listen-file
    """
    raise NotImplementedError("Sprint 2: implement Deepgram Nova-2 STT")

async def detect_language(text: str) -> str:
    """
    Detect the primary language of the text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Language code string
    """
    raise NotImplementedError("Sprint 2: implement language detection")
