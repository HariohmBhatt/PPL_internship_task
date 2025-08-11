"""Application configuration management."""

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # JWT Configuration
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, env="JWT_EXPIRE_MINUTES")  # 24 hours
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    database_url_test: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5433/quiz_test",
        env="DATABASE_URL_TEST"
    )
    
    # CORS Configuration
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        env="ALLOWED_ORIGINS"
    )
    
    # AI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    gemini_fallback_model: str = Field(default="gemini-2.0-flash-lite", env="GEMINI_FALLBACK_MODEL")
    
    # Environment
    env: str = Field(default="dev", env="ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Rate Limiting
    hint_rate_limit_per_user_question: int = Field(
        default=3, env="HINT_RATE_LIMIT_PER_USER_QUESTION"
    )
    submission_rate_limit_per_quiz: int = Field(
        default=10, env="SUBMISSION_RATE_LIMIT_PER_QUIZ"
    )
    
    # Email Configuration
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    notification_from_email: str = Field(default="noreply@aiquiz.com", env="NOTIFICATION_FROM_EMAIL")
    notification_enabled: bool = Field(default=False, env="NOTIFICATION_ENABLED")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")  # 1 hour
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    
    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins as a list."""
        if isinstance(self.allowed_origins, str):
            origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
            # Add null origin for file:// protocol support
            if self.env == "dev":
                origins.append("null")
            return origins
        return []
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v_upper
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env.lower() in ("dev", "development")
    
    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.env.lower() in ("test", "testing")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env.lower() in ("prod", "production")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
