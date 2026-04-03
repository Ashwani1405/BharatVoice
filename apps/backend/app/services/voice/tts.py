"""
Sprint 2 — Text-to-Speech Service
Converts bot responses into natural-sounding speech using ElevenLabs.
"""
# TODO: Sprint 2 — implement this module

from typing import AsyncGenerator

async def generate_speech(text: str, voice_id: str = "default") -> AsyncGenerator[bytes, None]:
    """
    Stream audio generated from ElevenLabs for the given text.
    
    Args:
        text: The response text
        voice_id: The ElevenLabs voice ID to use
        
    Returns:
        Async generator yielding chunks of audio bytes
    """
    raise NotImplementedError("Sprint 2: implement ElevenLabs TTS streaming")
