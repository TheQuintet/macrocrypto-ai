"""Configuration management for AI Service."""

from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """AI Service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================================
    # SERVICE
    # ============================================================
    service_name: str = Field(default="ai-service")
    service_version: str = Field(default="1.0.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    # ============================================================
    # DATABASE (TimescaleDB)
    # ============================================================
    database_url: str = Field(
        default="postgresql://macro:crypto@postgres:5432/macrocrypto"
    )

    # Source tables (written by Data Ingestion Service)
    db_table_btc_prices: str = Field(default="btc_prices")
    db_table_macro_indicators: str = Field(default="macro_indicators")

    # Target table (written by AI Service)
    db_table_predictions: str = Field(default="btc_predictions")

    # ============================================================
    # REDIS
    # ============================================================
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)

    # TTL for cached predictions (5 minutes per T1.5 spec)
    redis_forecast_ttl: int = Field(default=300)

    # ============================================================
    # RABBITMQ
    # ============================================================
    rabbitmq_host: str = Field(default="rabbitmq")
    rabbitmq_port: int = Field(default=5672)
    rabbitmq_username: str = Field(default="guest")
    rabbitmq_password: str = Field(default="guest")
    rabbitmq_vhost: str = Field(default="/")
    rabbitmq_exchange: str = Field(default="macrocrypto")

    # Queues
    rabbitmq_price_queue: str = Field(default="ai.price.queue")
    rabbitmq_indicator_queue: str = Field(default="ai.indicator.queue")

    # Routing keys
    rabbitmq_price_routing_key: str = Field(default="*.price.*")
    rabbitmq_indicator_routing_key: str = Field(default="*.economic.*")
    rabbitmq_prediction_routing_key: str = Field(
        default="intelligence.forecast.generated"
    )

    # ============================================================
    # MLFLOW
    # ============================================================
    mlflow_tracking_uri: str = Field(default="http://mlflow:5000")
    mlflow_experiment_name: str = Field(default="macrocrypto_ai")
    mlflow_model_name: str = Field(default="prophet_btc_forecast")

    # ============================================================
    # MODEL PARAMETERS
    # ============================================================
    model_training_days: int = Field(default=90)
    model_forecast_horizon_hours: int = Field(default=24)
    model_forecast_horizon_days: int = Field(default=7)
    model_changepoint_prior: float = Field(default=0.05)
    model_seasonality_prior: float = Field(default=10.0)
    model_holidays_prior: float = Field(default=10.0)

    # Model artifact storage
    model_save_dir: str = Field(default="models")
    prophet_24h_model_filename: str = Field(default="prophet_24h.json")

    # ============================================================
    # PERFORMANCE THRESHOLDS
    # ============================================================
    threshold_mae: float = Field(default=0.10)
    threshold_rmse: float = Field(default=0.15)
    threshold_mape: float = Field(default=10.0)
    threshold_directional: float = Field(default=55.0)

    # ============================================================
    # SCHEDULING
    # ============================================================
    retrain_hour: int = Field(default=6)
    retrain_minute: int = Field(default=0)
    retrain_timezone: str = Field(default="UTC")
    walk_forward_days: int = Field(default=30)

    # Scheduler master switch (disabled in tests, enabled in prod)
    scheduler_enabled: bool = Field(default=True)

    # Retention of in-memory job history entries
    scheduler_history_max_entries: int = Field(default=100)

    # Retries per job run on failure (0 = no retry)
    scheduler_max_retries: int = Field(default=1)

    # ============================================================
    # PROPERTIES
    # ============================================================
    @property
    def rabbitmq_url(self) -> str:
        """Build RabbitMQ connection URL."""
        return (
            f"amqp://{self.rabbitmq_username}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        )

    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def async_database_url(self) -> str:
        """Build the async (asyncpg) variant of the database URL.

        SQLAlchemy async requires the driver to be specified in the
        URL scheme. This property converts a plain postgresql://
        URL to postgresql+asyncpg://, and leaves already-driver-
        specified URLs untouched.

        Returns:
            SQLAlchemy-compatible async database URL.
        """
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def prophet_24h_model_path(self) -> str:
        """Return the full path to the trained 24h Prophet model file."""
        return f"{self.model_save_dir}/{self.prophet_24h_model_filename}"


# Global settings instance
settings = Settings()