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
