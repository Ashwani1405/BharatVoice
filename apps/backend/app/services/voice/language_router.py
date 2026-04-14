import os

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts")

def load_prompt_template(language: str) -> str:
    filename = f"kyc_{'hindi' if language == 'hi' else 'english'}.txt"
    filepath = os.path.join(PROMPTS_DIR, filename)
    
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "You are a KYC assistant. Please ask for Name, DOB, and Address."

def get_voice_id(language: str) -> str:
    # ElevenLabs voice IDs mapping
    if language == "hi":
        return "pNInz6obbfIdG2f9O2zV" # Example Hindi capable voice
    return "21m00Tcm4TlvDq8ikWAM" # Example English voice

def get_deepgram_language(language: str) -> str:
    if language == "hi":
        return "hi"
    return "en"

def get_greeting(language: str) -> str:
    if language == "hi":
        return "नमस्ते। मैं भारत वॉइस का केवायसी एजेंट हूँ। क्या हम आपकी पहचान की पुष्टि शुरू कर सकते हैं?"
    return "Hello. I am the BharatVoice KYC agent. Can we begin verifying your identity?"

def get_farewell(language: str) -> str:
    if language == "hi":
        return "धन्यवाद। आपकी जानकारी सुरक्षित कर ली गई है। आपका दिन शुभ हो।"
    return "Thank you. Your information has been secured. Have a good day."
    
def detect_language(text: str) -> str:
    # Basic dummy detect language logic since this is just a stub for voice
    return "hi" if any("\u0900" <= c <= "\u097F" for c in text) else "en"
