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
    OPENAI_API_KEY: str

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
