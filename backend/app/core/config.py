import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CampusFix API"
    API_VERSION: str = "v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & JWT
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_STARTTLS: bool = True
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "sqlite:///./campusfix.db"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # Machine Learning
    ML_MODEL_PATH: str = "ml/models/active-model.json"
    ML_CONFIDENCE_THRESHOLD: float = 0.45
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"
    ML_SERVICE_URL: str = "http://127.0.0.1:8001"
    DAILY_ISSUE_REWARD_LIMIT: int = 30
    PENDING_ASSIGNMENT_OVERDUE_HOURS: int = 24
    ACTIVE_ASSIGNMENT_OVERDUE_HOURS: int = 72

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def model_post_init(self, __context):
        if not 0.0 <= self.ML_CONFIDENCE_THRESHOLD <= 1.0:
            raise ValueError("ML_CONFIDENCE_THRESHOLD must be between 0 and 1")
        if not 1 <= self.MAX_UPLOAD_SIZE_MB <= 50:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be between 1 and 50")
        if not 0 <= self.DAILY_ISSUE_REWARD_LIMIT <= 100:
            raise ValueError("DAILY_ISSUE_REWARD_LIMIT must be between 0 and 100")
        if not self.SECRET_KEY:
            if self.ENVIRONMENT.lower() in {"production", "prod"}:
                raise ValueError("SECRET_KEY must be set in production")
            import secrets
            self.SECRET_KEY = secrets.token_urlsafe(48)



settings = Settings()
