# app/config.py
"""Environment configuration for alert-service"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # ============================================
    # SERVICE CONFIGURATION
    # ============================================
    SERVICE_NAME: str = "alert-service"
    SERVICE_PORT: int = 8003
    LOG_LEVEL: str = "INFO"
    
    # ============================================
    # DATABASE
    # ============================================
    DATABASE_URL: str = "postgresql://macro:crypto@postgres:5432/macrocrypto"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # ============================================
    # REDIS
    # ============================================
    REDIS_ENABLED: bool = True
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    REDIS_CACHE_TTL: int = 300
    
    @property
    def REDIS_CONNECTION_URL(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ============================================
    # RABBITMQ
    # ============================================
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_URL: Optional[str] = None
    
    @property
    def RABBITMQ_CONNECTION_URL(self) -> str:
        if self.RABBITMQ_URL:
            return self.RABBITMQ_URL
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VHOST}"
    
    # ============================================
    # ALERT SERVICE SPECIFIC
    # ============================================
    ALERT_CHECK_INTERVAL: int = 60
    MAX_ALERTS_PER_USER: int = 50
    ALERT_RETENTION_DAYS: int = 30
    
    # This setting controls whether email notifications are enabled. If set to False, email notifications will be disabled.
    EMAIL_ENABLED: bool = True

    # ============================================
    # EMAIL NOTIFICATIONS
    # ============================================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "alerts@macrocrypto.ai"
    SMTP_FROM_NAME: str = "MacroCrypto AI Alerts"
    
    # ============================================
    # SMS NOTIFICATIONS (Optional)
    # ============================================
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # ============================================
    # SLACK NOTIFICATIONS (Optional)
    # ============================================
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    
    # ============================================
    # DEVELOPMENT
    # ============================================
    RELOAD: bool = False
    DEBUG: bool = False
    
    @property
    def IS_IN_DOCKER(self) -> bool:
        return os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
    
    class Config:
        env_file = (
            ".env.local"
            if os.path.exists(".env.local")
            else ".env"
        )
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cache settings for better performance"""
    return Settings()


settings = get_settings()