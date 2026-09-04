from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # System Info
    PROJECT_NAME: str = "PRAVAH"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Platform URLs
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Secrets & Security
    SECRET_KEY: str = "pravah_master_secret_key_change_in_production_min32chars!"
    ENCRYPTION_KEY: str = "ZXZhbHVhdGlvbl9lbmNyeXB0aW9uX2tleV9mb3JfcHJhdmFoX3NlY3VyZQ=="
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30 # 30 days
    OTP_EXPIRE_MINUTES: int = 10
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./pravah.db"
    DATABASE_SYNC_URL: str = "sqlite:///./pravah.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    STORAGE_TYPE: str = "local" # local or s3
    STORAGE_LOCAL_PATH: str = "./uploads"
    S3_BUCKET: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    
    # Email / SMTP
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@pravah.app"
    SMTP_FROM_NAME: str = "PRAVAH Platform"
    SMTP_TLS: bool = True
    
    # First Run Setup Flag
    IS_INITIALIZED: bool = False
    
    # Default Provider API Keys & Model Defaults
    OPENROUTER_API_KEY: Optional[str] = None
    DEFAULT_AI_MODEL: str = "anthropic/claude-3.5-sonnet"
    IMAGE_AI_MODEL: str = "black-forest-labs/flux-1-schnell"

    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    
    CASHFREE_APP_ID: Optional[str] = None
    CASHFREE_SECRET_KEY: Optional[str] = None
    CASHFREE_ENV: str = "TEST" # TEST or PROD
    
    # Social OAuth Client IDs and Secrets
    FACEBOOK_CLIENT_ID: Optional[str] = None
    FACEBOOK_CLIENT_SECRET: Optional[str] = None
    
    X_CLIENT_ID: Optional[str] = None
    X_CLIENT_SECRET: Optional[str] = None
    
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    
    # SSO Providers
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

settings = Settings()
