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
    # FEATURE SOURCE
    # ============================================================
    # Where training and prediction features come from.
    #
    # Supported values:
    #   "parquet"      — data-service parquet files (47 columns).
    #                    Used by the manual CLI file-path pipeline.
    #   "features_db"  — the future DB table (47 columns, live-updated).
    #                    This is the target production source.
    #
    # Both sources provide the same canonical 47-column contract.
    # Only the physical storage differs.
    #
    # The legacy 10-feature path (btc_prices + macro_indicators) is
    # NOT a supported option. The old repository method
    # fetch_training_frame(hours) remains for reference but is
    # unreachable via this setting.
    feature_source: str = Field(default="features_db")

    # Name of the DB table that holds the canonical 47-column set.
    # Used when feature_source="features_db". Owned by the data-service;
    # the AI Service reads from it, never writes.
    features_db_table: str = Field(
        default="features_db",
        description="Name of the feature-store table used by features_db source",
    )

    # Directory where the data-service writes its processed parquet
    # files. Used when feature_source="parquet". The AI Service must
    # be able to read this directory (usually mounted as a read-only
    # volume in Docker/K8s).
    shared_data_dir: str = Field(
        default="/app/shared/features",
        description="Directory containing data-service parquet files",
    )

    # Optional override for the partition used as prediction history
    # (FeatureContext.PREDICTION). Empty means the default mapping
    # (live_frontier). Set to "test" for local dev when live_frontier
    # holds fewer rows than the generator's minimum history.
    prediction_feature_partition: str = Field(
        default="",
        description="Partition override for prediction history (e.g. 'test')",
    )

    # ============================================================
    # CLI ISOLATION
    # ============================================================
    # When True, all repository writes and file-system writes go to
    # isolated targets so a CLI run never touches production data:
    #   - DB writes go to <table>_cli variants
    #   - Model files go to {cli_data_dir}/models/
    #   - Backtest temp dirs go to {cli_data_dir}/models/backtest/
    #   - Export files go to {cli_data_dir}/exports/
    #
    # Controlled by the CLI_MODE environment variable. Default: False.
    # The manual CLI (app.cli.pipeline) sets CLI_MODE=true before
    # invoking any job or repository.
    cli_mode: bool = Field(default=False)

    # Root directory for CLI-mode artifacts (models, exports, etc.).
    # Relative to the service working directory.
    cli_data_dir: str = Field(default="cli_data")

    # ============================================================
    # CHAMPION SELECTION
    # ============================================================
    # The champion is the model currently authorized to serve
    # predictions for a given horizon. A daily promotion job
    # (daily_promote_champion_job) ranks candidate models by a
    # configured metric over rolling windows and, when a candidate
    # beats the incumbent by a meaningful margin and has been
    # stable for N consecutive days, promotes it.
    #
    # The prediction jobs then load the champion (per horizon, and
    # optionally per market regime) instead of using a hardcoded
    # model.
    #
    # See docs/champion_selection_investigation.md for the full
    # design and rationale.

    # ------------------------------------------------------------
    # Ranking metric
    # ------------------------------------------------------------
    # Which metric the promotion job ranks candidates by. Lower is
    # better for "mae", "rmse", "mape". Higher is better for
    # "directional_accuracy".
    #
    # The metric is read from the prediction_performance table
    # (per-point backtest metrics), NOT from model_performance
    # (which is an aggregate written after backtest). We use
    # prediction_performance because it carries the sample_size
    # needed for the minimum-sample gate.
    #
    # Recommended values:
    #   "mae"  — default, matches the pre-existing in-sample ranking
    #            and is scale-invariant with the price
    #   "rmse" — penalizes large errors more
    #   "mape" — scale-independent
    #   "directional_accuracy" — flipped comparison (higher is better)
    champion_selection_metric: str = Field(default="mae")

    # ------------------------------------------------------------
    # Look-back windows
    # ------------------------------------------------------------
    # The candidate must win on BOTH windows to be eligible. This
    # prevents a model from being promoted on a short window of
    # lucky results that wouldn't hold over a longer period.
    #
    # primary: 30 days. The current regime.
    # secondary: 90 days. Broader stability.
    #
    # Both are measured from `datetime.now(timezone.utc)` at
    # promotion time, applied to `prediction_performance.forecast_date`.
    champion_primary_lookback_days: int = Field(default=30)
    champion_secondary_lookback_days: int = Field(default=90)

    # ------------------------------------------------------------
    # Safety gates
    # ------------------------------------------------------------
    # A candidate must pass ALL of these gates to be promoted:
    #
    # 1) Minimum sample size
    #    The candidate must have at least this many matched points
    #    in the primary window. A model that only ran 3 backtests
    #    this month shouldn't displace a well-tested champion.
    #
    #    Rule of thumb: 100 points ≈ 4 full days of hourly
    #    backtest output for a 24h horizon, or ~0.5 days for 7d.
    #    The default is a conservative floor for either horizon.
    #
    # 2) Meaningful lead
    #    The candidate's metric must be better than the incumbent's
    #    by at least this fraction. E.g., 0.05 = 5%.
    #
    #    Why: a lead of 0.1% is noise. Promoting on noise causes
    #    the champion to flip back and forth, which is bad for
    #    interpretability and produces operational churn.
    #
    #    Rule of thumb: 0.05 (5%) filters out most noise. Tighten
    #    to 0.10 for very conservative regimes; loosen to 0.02
    #    only if the model set changes frequently.
    #
    #    Comparison direction depends on the metric:
    #      - For "mae" / "rmse" / "mape": candidate < incumbent * (1 - lead)
    #      - For "directional_accuracy": candidate > incumbent * (1 + lead)
    #
    # 3) Stability
    #    The candidate must have been the top-ranked model for at
    #    least this many CONSECUTIVE DAYS. The stability check
    #    reads champion_candidates, which is written once per day
    #    by the promotion job.
    #
    #    Why: a single day's ranking is noisy. Requiring a run of
    #    consecutive days filters out one-off wins.
    #
    #    Rule of thumb: 3 days. Higher for very stable regimes (5),
    #    lower only if you're prepared for more churn.
    champion_min_sample_size: int = Field(default=100)
    champion_min_lead_pct: float = Field(default=0.05)
    champion_stability_days: int = Field(default=3)

    # ------------------------------------------------------------
    # Regime-aware champion selection — PROMOTION SIDE
    # ------------------------------------------------------------
    # When True, the promotion job ranks candidates PER MARKET
    # REGIME (bull / bear / volatile / neutral) in addition to
    # globally. That produces up to five champion rows per horizon:
    # one for the global champion (market_condition IS NULL) and
    # one for each regime that has enough data to clear the gates.
    #
    # When False (default), only global champions are written. The
    # market_condition column in model_champions stays NULL.
    #
    # ------------------------------------------------------------------
    # This flag does NOT enable regime-aware serving.
    # ------------------------------------------------------------------
    # Enabling this flag alone makes the promotion job write
    # per-regime champion rows — but the prediction jobs still load
    # the global champion, because serving is gated separately by
    # `champion_serve_regime_aware`. The two flags are independent
    # so you can:
    #
    #   1. Enable promotion alone to observe which regimes would
    #      promote which models, without affecting production
    #      forecasts.
    #   2. Enable serving later, once you're confident in the
    #      per-regime champions.
    #   3. Disable serving without losing the accumulated
    #      per-regime history (the rows stay; they're just not
    #      consulted).
    #
    # ------------------------------------------------------------------
    # Why default to False
    # ------------------------------------------------------------------
    # Regime-aware selection is a strict improvement in theory, but
    # it requires enough data per regime to be meaningful. With the
    # current data volume, most regimes will have fewer than
    # champion_min_sample_size matched points within a 30-day
    # window, so the promotion job would fall back to the global
    # champion anyway.
    #
    # Turning it on before there's enough per-regime data creates
    # the illusion of regime-awareness without the substance: the
    # promotion job will run every regime candidate through the
    # same gates, most will be skipped, and the output will look
    # identical to running with regime=False.
    #
    # ------------------------------------------------------------------
    # When to enable it
    # ------------------------------------------------------------------
    # Enable this once:
    #   - The backtest has produced at least ~90 days of prediction
    #     history (so each regime has multiple 30-day windows).
    #   - The three regimes ('bull', 'bear', 'volatile') each show
    #     enough samples in the primary window across the model
    #     set to be able to distinguish winners.
    #   - You've verified the classifier in app.prediction.market
    #     is producing the expected regime labels on recent data.
    #
    # A reasonable rollout:
    #   1. Leave False while populating prediction_performance.
    #   2. Run a dry pass of the promotion job with regime=True to
    #      inspect the candidate rankings and see how many regimes
    #      clear the sample-size gate. If most don't, keep False.
    #   3. When enough regimes have data, flip to True. The
    #      promotion job will start writing per-regime champions.
    #
    # Turning this off later is safe: existing per-regime champions
    # remain in the table but are ignored, and the promotion job
    # reverts to writing only the global champion.
    champion_enable_regime_selection: bool = Field(default=False)

    # ------------------------------------------------------------
    # Regime-aware champion selection — SERVING SIDE
    # ------------------------------------------------------------
    # When True, the prediction jobs classify the CURRENT BTC
    # price regime before loading a champion, and load the
    # champion for that regime. The classification uses the same
    # function the backtest uses (`classify_market_condition_safe`
    # in app.prediction.market), applied to a trailing window of
    # real BTC prices.
    #
    # The trailing window length matches the horizon:
    #   - hourly_prediction_job (24h horizon) — last 24 hours
    #   - daily_7d_prediction_job (7d horizon) — last 168 hours
    #
    # This mirrors the backtest, where each iteration classifies
    # its full forecast window (24h or 168h). Serving and backtest
    # therefore assign labels with the same semantics.
    #
    # ------------------------------------------------------------------
    # Fallback chain
    # ------------------------------------------------------------------
    # With this flag on, the champion loading chain becomes:
    #
    #   regime_champion        (horizon, classified_regime)
    #     → global_champion    (horizon, None)
    #       → previous_champion
    #         → prophet_fresh
    #
    # The regime_champion step is skipped when:
    #   - this flag is False, OR
    #   - the classifier returned None (couldn't decide)
    #
    # In those cases the chain falls back to today's three-level
    # behavior: global → previous → prophet_fresh.
    #
    # ------------------------------------------------------------------
    # Why default to False
    # ------------------------------------------------------------------
    # This flag is meaningful only when `champion_enable_regime_selection`
    # is also True — there must be per-regime champion rows to
    # consult. Enable it after:
    #
    #   1. Promotion has been running with regime selection on for
    #      long enough to have written per-regime champions.
    #   2. You've inspected `model_champions` and are satisfied
    #      that the per-regime picks are sensible.
    #   3. You've checked the classifier logs to confirm the
    #      current-regime classifications are reasonable.
    #
    # With this flag on and no regime champions yet in the table,
    # the chain simply falls through to the global champion on
    # every run — no harm done, but no benefit either. The
    # WARNING log line (see the classifier helper) tells you when
    # the classifier couldn't decide.
    champion_serve_regime_aware: bool = Field(default=False)

    # ------------------------------------------------------------
    # Promotion schedule
    # ------------------------------------------------------------
    # When the daily promotion job runs. Must be AFTER both:
    #   - The backtest job (6:45 AM UTC) — populates prediction_performance
    #   - The aggregation job (7:15 AM UTC) — populates model_performance
    #
    # The default (7:30 AM UTC) sits right after aggregation, giving
    # the promotion job a fresh view of both source tables.
    #
    # Changing this to a time before 7:15 will cause the promotion
    # job to read stale metrics on days when the aggregation job is
    # delayed.
    champion_promotion_hour: int = Field(default=7)
    champion_promotion_minute: int = Field(default=30)

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
    # DEPRECATED (2026-XX): The following settings are not read by
    # any code path. Kept for reference during the current migration
    # and will be removed once the future feature pipeline is in
    # place. See known_issues.md #13.
    model_training_days: int = Field(default=90)          # DEPRECATED
    model_forecast_horizon_hours: int = Field(default=24) # DEPRECATED
    model_forecast_horizon_days: int = Field(default=7)   # DEPRECATED
    model_changepoint_prior: float = Field(default=0.05)  # DEPRECATED
    model_seasonality_prior: float = Field(default=10.0)  # DEPRECATED
    model_holidays_prior: float = Field(default=10.0)     # DEPRECATED

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

    # DEPRECATED: not read by any code path. Kept for reference.
    # See known_issues.md #13.
    walk_forward_days: int = Field(default=30)  # DEPRECATED

    # ------------------------------------------------------------
    # Scheduler toggles
    # ------------------------------------------------------------
    # Master switch for the entire scheduler. When False, no jobs
    # run, even if the category toggles below are True.
    scheduler_enabled: bool = Field(default=True)

    # ML pipeline jobs — the 7 jobs that depend on trained models
    # and a working feature source:
    #   - daily_retrain
    #   - hourly_prediction
    #   - daily_7d_prediction
    #   - daily_backtest
    #   - daily_accuracy
    #   - daily_multi_model_predictions
    #   - daily_model_performance_aggregation
    #
    # The daily_promote_champion_job is also gated by this flag,
    # because it depends on the ML pipeline having produced fresh
    # metrics.
    #
    # Default: False. Enable once the live path is ready to run
    # against the "features_db" source.
    scheduler_ml_jobs_enabled: bool = Field(default=False)

    # Analytics + housekeeping jobs — the 3 independent jobs that
    # do not depend on trained models:
    #   - daily_correlation
    #   - daily_event_impact_update
    #   - daily_export_cleanup
    #
    # Default: True. These run regardless of ML pipeline state.
    scheduler_analytics_jobs_enabled: bool = Field(default=True)

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

    # Event impact update job schedule (A5.5): daily at 4:00 AM UTC.
    # Runs after the 3:00 export cleanup and well before the 6:00
    # retrain. Reads every row in historical_event_impacts, recomputes
    # the BTC reaction with A5.2's ReactionCalculator, and updates
    # rows whose reaction changed. Idempotent: a second run the same
    # day is a no-op.
    event_impact_hour: int = Field(default=4)
    event_impact_minute: int = Field(default=0)

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
    # ``export_storage_dir_path``). In CLI mode, the path is
    # redirected under ``cli_data_dir``.
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

    # ------------------------------------------------------------
    # CLI-aware path properties
    # ------------------------------------------------------------
    @property
    def effective_model_save_dir(self) -> str:
        """Return the active model save directory.

        When CLI mode is enabled, returns a path under
        ``cli_data_dir`` so the CLI never writes into the production
        ``models/`` directory. Otherwise returns ``model_save_dir``.
        """
        if self.cli_mode:
            return f"{self.cli_data_dir}/models"
        return self.model_save_dir

    @property
    def effective_backtest_model_dir(self) -> str:
        """Return the active backtest temp dir.

        When CLI mode is enabled, returns a path under
        ``cli_data_dir``. Otherwise returns ``backtest_model_dir``.
        """
        if self.cli_mode:
            return f"{self.cli_data_dir}/models/backtest"
        return self.backtest_model_dir

    @property
    def prophet_24h_model_path(self) -> str:
        """Return the full path to the trained 24h Prophet model file.

        Uses the CLI-aware model save dir so CLI runs don't clash
        with production model files.
        """
        return (
            f"{self.effective_model_save_dir}/"
            f"{self.prophet_24h_model_filename}"
        )

    @property
    def prophet_7d_model_path(self) -> str:
        """Return the full path to the trained 7d Prophet model file.

        Uses the CLI-aware model save dir so CLI runs don't clash
        with production model files.
        """
        return (
            f"{self.effective_model_save_dir}/"
            f"{self.prophet_7d_model_filename}"
        )

    @property
    def export_storage_dir_path(self) -> Path:
        """Return the export storage directory as an absolute Path.

        When CLI mode is enabled, the directory is redirected under
        ``cli_data_dir/exports``. Otherwise, relative paths in
        ``export_storage_dir`` are resolved against the current
        working directory (which for the AI Service is the service
        root), and absolute paths are returned unchanged.

        Returns:
            The resolved :class:`pathlib.Path` for the storage
            directory. The path is not created here — creation is
            ``LocalDiskStorage``'s responsibility.
        """
        if self.cli_mode:
            base = Path(f"{self.cli_data_dir}/exports")
        else:
            base = Path(self.export_storage_dir)

        if not base.is_absolute():
            base = Path.cwd() / base
        return base

    # ------------------------------------------------------------
    # Champion-related helpers
    # ------------------------------------------------------------
    @property
    def champion_metric_eligible_values(self) -> tuple:
        """Return the set of allowed values for champion_selection_metric.

        Returned as a tuple so it can be used directly in `in` checks
        and validations. The promotion job validates
        `champion_selection_metric` against this tuple at startup, so
        a typo in the env var produces a clear error rather than
        silently ranking on an unknown metric.

        Returns:
            Tuple of allowed metric names. Same set as the CHECK
            constraint on threshold_breaches.metric and
            model_champions.metric_name.
        """
        return ("mae", "rmse", "mape", "directional_accuracy")

    @property
    def champion_metric_is_higher_better(self) -> bool:
        """Return True if higher metric values are better.

        Used by the promotion job to decide the comparison direction:
            - For mae, rmse, mape: lower is better → False
            - For directional_accuracy: higher is better → True
        """
        return self.champion_selection_metric == "directional_accuracy"


# Global settings instance
settings = Settings()