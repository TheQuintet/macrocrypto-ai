"""Configuration management for API Gateway service.

Uses Pydantic Settings to load environment variables with validation.
All settings are loaded from .env file or system environment variables.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ============================================
    # SERVICE CONFIGURATION
    # ============================================
    SERVICE_NAME: str = "api-gateway"
    SERVICE_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = Field(..., description="Required: Secret key for JWT signing")
    DEBUG: bool = False
    RELOAD: bool = True

    # ============================================
    # REDIS (Session, Rate Limiting, Cache)
    # ============================================
    REDIS_ENABLED: bool = True
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_CACHE_TTL: int = 300  # 5 minutes default
    REDIS_SESSION_TTL: int = 3600  # 1 hour

    # ============================================
    # RABBITMQ (Event Consumer/Producer)
    # ============================================
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"

    @property
    def RABBITMQ_URL(self) -> str:
        """Build RabbitMQ connection URL."""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VHOST}"

    # ============================================
    # INTERNAL SERVICES
    # ============================================
    DATA_SERVICE_URL: str = "http://data-service:8001"
    AI_SERVICE_URL: str = "http://ai-service:8002"
    ALERT_SERVICE_URL: str = "http://alert-service:8003"

    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # Tiered rate limits (requests per minute)
    RATE_LIMIT_GUEST: int = 10
    RATE_LIMIT_USER: int = 100
    RATE_LIMIT_ADMIN: int = 1000

    # ============================================
    # JWT / AUTHENTICATION
    # ============================================
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15  # Access token expiry
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7  # Refresh token expiry

    # ============================================
    # CORS
    # ============================================
    CORS_ALLOW_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="List of allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["*"],
        description="Allowed HTTP methods"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"],
        description="Allowed HTTP headers"
    )

    # ============================================
    # VALIDATORS
    # ============================================

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: any) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(value, str):
            # Remove brackets if present and split by comma
            value = value.strip("[]")
            return [origin.strip().strip('"').strip("'") for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate log level is one of standard levels."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_value = value.upper()
        if upper_value not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return upper_value

    # ============================================
    # Pydantic Settings Config
    # ============================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars not defined here
    )


# ============================================
# SINGLETON INSTANCE
# ============================================

settings = Settings()


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_settings() -> Settings:
    """Return the singleton settings instance."""
    return settings