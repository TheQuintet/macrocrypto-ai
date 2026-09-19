"""Configuration management for AI Service."""

from enum import Enum
from pathlib import Path
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
    prophet_7d_model_filename: str = Field(default="prophet_7d.json")

    # ============================================================
    # PERFORMANCE THRESHOLDS
    # ============================================================
    # MAE/RMSE thresholds are decimal fractions of mean price
    # (0.10 = 10%). MAPE and directional are already percentages.
    threshold_mae: float = Field(default=0.10)
    threshold_rmse: float = Field(default=0.15)
    threshold_mape: float = Field(default=10.0)
    threshold_directional: float = Field(default=55.0)

    # ============================================================
    # THRESHOLD WARNING STREAKS (T5.6)
    # ============================================================
    # A warning is emitted when a metric has breached its threshold
    # for this many consecutive days.
    threshold_warning_streak_days: int = Field(default=3)

    # ============================================================
    # MARKET CONDITION THRESHOLDS (T5.3)
    # ============================================================
    # Bull market: cumulative return > +20% over the forecast window
    market_bull_threshold_pct: float = Field(default=20.0)
    # Bear market: cumulative return < -20% over the forecast window
    market_bear_threshold_pct: float = Field(default=20.0)
    # Volatile market: std of percentage returns > 5% (decimal form)
    market_volatility_threshold: float = Field(default=0.05)

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

    # 7d prediction job schedule (daily at 6:30 AM UTC, after retrain)
    prediction_7d_hour: int = Field(default=6)
    prediction_7d_minute: int = Field(default=30)

    # Backtest job schedule (daily at 6:45 AM UTC, after 7d prediction)
    backtest_hour: int = Field(default=6)
    backtest_minute: int = Field(default=45)

    # Accuracy check job schedule (daily at 7:00 AM UTC, after backtest)
    accuracy_hour: int = Field(default=7)
    accuracy_minute: int = Field(default=0)

    # Multi-model prediction job schedule (M6b): daily at 6:15 AM UTC,
    # after the 6:00 retrain (so all variants are fresh on disk) and
    # before the 6:30 7d Prophet prediction. The job writes batches
    # for the 5 non-prophet_fresh variants; the 24h Prophet batch is
    # handled by hourly_prediction_job and the 7d Prophet batch by
    # daily_7d_prediction_job, so this job does not duplicate them.
    multi_model_prediction_hour: int = Field(default=6)
    multi_model_prediction_minute: int = Field(default=15)

    # Model-performance aggregation job schedule (M7b): daily at
    # 7:15 AM UTC, after the 6:45 backtest has written fresh rows to
    # prediction_performance and after the 7:00 accuracy check has
    # read the same source. This job copies the latest aggregate
    # metrics into model_performance for the M8 multi-model
    # performance API to read from.
    model_performance_aggregation_hour: int = Field(default=7)
    model_performance_aggregation_minute: int = Field(default=15)

    # Correlation calculation job schedule (A1.5): daily at 2:00 AM
    # UTC. Runs well before the 6:00 retrain so the correlations are
    # computed on the previous day's freshest macro data. The job
    # writes one row per (indicator, window) into
    # btc_macro_correlation via the CorrelationCalculator.
    correlation_hour: int = Field(default=2)
    correlation_minute: int = Field(default=0)

    # ============================================================
    # BACKTEST PARAMETERS
    # ============================================================
    # Number of walk-forward iterations (days) for the backtest
    backtest_iterations: int = Field(default=30)

    # Number of hours of history to fetch for backtesting
    # (must be >= backtest_iterations * 24 + max lag)
    backtest_history_hours: int = Field(default=2880)  # 120 days

    # If True, evaluate the full forecast trajectory (24 or 168 points
    # per iteration). If False, evaluate only the endpoint.
    backtest_full_trajectory: bool = Field(default=True)

    # Temporary directory for chained warm-start models between iterations
    backtest_model_dir: str = Field(default="models/backtest")

    # ============================================================
    # EXPORT STORAGE (A2.6)
    # ============================================================
    # Backend selector. Only "local" is implemented in A2.6.
    # "s3" is reserved so a future branch can add an S3-compatible
    # implementation without changing this field's name.
    export_storage_backend: str = Field(default="local")

    # Directory where locally-stored export files live. Relative
    # paths are resolved against the current working directory (see
    # ``export_storage_dir_path``).
    export_storage_dir: str = Field(default="exports")

    # How long a download link remains valid, in seconds. The A2.6
    # ticket calls for "7 days" as the example; 604800 = 7 × 24 × 3600.
    export_link_ttl_seconds: int = Field(default=604800)

    # How long a stored file remains on disk before the cleanup job
    # deletes it, in seconds. Defaults to the same 7-day window as
    # the link TTL so a stale link and a stale file expire together.
    export_file_ttl_seconds: int = Field(default=604800)

    # ============================================================
    # ACCURACY JOB PARAMETERS (T5.4)
    # ============================================================
    # Look-back window for accuracy checks (in days)
    accuracy_lookback_days: int = Field(default=7)

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

    @property
    def prophet_7d_model_path(self) -> str:
        """Return the full path to the trained 7d Prophet model file."""
        return f"{self.model_save_dir}/{self.prophet_7d_model_filename}"

    @property
    def export_storage_dir_path(self) -> Path:
        """Return the export storage directory as an absolute Path.

        Relative paths in ``export_storage_dir`` are resolved
        against the current working directory, which for the
        AI Service is the service root. Absolute paths are
        returned unchanged.

        Returns:
            The resolved :class:`pathlib.Path` for the storage
            directory. The path is not created here — creation is
            ``LocalDiskStorage``'s responsibility.
        """
        path = Path(self.export_storage_dir)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path


# Global settings instance
settings = Settings()