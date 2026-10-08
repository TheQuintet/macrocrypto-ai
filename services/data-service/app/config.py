"""Environment configuration for data-service"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings"""
    # Load .env.local when available, otherwise .env 
    model_config = SettingsConfigDict( 
        env_file=".env.local" if os.path.exists(".env.local") else ".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True, )
    
    # ============================================
    # SERVICE CONFIGURATION
    # ============================================
    SERVICE_NAME: str = "data-service"
    SERVICE_PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    
    # ============================================
    # DATABASE
    # ============================================
    # Default Docker database URL.
    # Local development overrides this through .env.local.
    DATABASE_URL: str = "postgresql://macro:crypto@postgres:5432/macrocrypto"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # ============================================
    # REDIS
    # ============================================
    # Support BOTH individual settings AND full URL
    REDIS_ENABLED: bool = True
    # REDIS_HOST: str = "redis"  # Docker service name
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None  # Override if provided
    REDIS_CACHE_TTL: int = 300
    
    @property
    def REDIS_CONNECTION_URL(self) -> str:
        """Build Redis connection URL (supports both formats)"""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ============================================
    # RABBITMQ
    # ============================================
    RABBITMQ_HOST: str = "rabbitmq"  # Docker service name
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_URL: Optional[str] = None
    BTC_PRICE_RABBITMQ_THRESHOLD_USD: float = Field(default=1.0, gt=0)
    
    @property
    def RABBITMQ_CONNECTION_URL(self) -> str:
        """Build RabbitMQ connection URL"""
        if self.RABBITMQ_URL:
            return self.RABBITMQ_URL
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VHOST}"
    
    # ============================================
    # BINANCE API (Primary Crypto Data Source)
    # ============================================
    # REST API
    BINANCE_REST_URL: str = "https://api.binance.com/api/v3"
    BINANCE_TESTNET_URL: str = "https://testnet.binance.vision/api/v3"
    BINANCE_USE_TESTNET: bool = False
    
    # WebSocket
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
    BINANCE_WS_TESTNET_URL: str = "wss://testnet.binance.vision/ws"
    
    # Rate limiting
    BINANCE_RATE_LIMIT_PER_MINUTE: int = 1200
    
    # Default symbol
    BINANCE_DEFAULT_SYMBOL: str = "BTCUSDT"

    #Binance REST API endpoint for historical daily candles
    BINANCE_HISTORY_API: str = "https://api.binance.com/api/v3/klines"
    
    @property
    def BINANCE_REST_ENDPOINT(self) -> str:
        """Get the appropriate Binance REST endpoint"""
        return self.BINANCE_TESTNET_URL if self.BINANCE_USE_TESTNET else self.BINANCE_REST_URL
    
    @property
    def BINANCE_WS_ENDPOINT(self) -> str:
        """Get the appropriate Binance WebSocket endpoint"""
        return self.BINANCE_WS_TESTNET_URL if self.BINANCE_USE_TESTNET else self.BINANCE_WS_URL
    
    
    # COINGECKO API (Market Cap Data Source)
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"
    MARKET_CAP_CACHE_TTL: int = 900  # 15 minutes


    # BTC Dominance Cache TTL (seconds)
    BTC_DOMINANCE_CACHE_TTL: int = 900


    # ============================================
    # FRED API (Economic Indicators)
    # ============================================
    FRED_API_URL: str = "https://api.stlouisfed.org/fred"
    FRED_API_KEY: Optional[str] = None  # Replace with your actual FRED API key or set to None if not available

    # ============================================
    # FRED SERIES CONFIGURATION
    # ============================================

    # Consumer Price Index (CPI) - Inflation
    # Series: CPIAUCSL
    FRED_CPI_SERIES: str = "CPIAUCSL"


    # Federal Funds Effective Rate
    # Series: FEDFUNDS
    FRED_FED_FUNDS_SERIES: str = "FEDFUNDS"


    # M2 Money Supply
    # Series: M2SL
    FRED_M2_SERIES: str = "M2SL"


    # US Dollar Index for ML, Daily
    # Series: DTWEXBGS
    FRED_DXY_SERIES: str = "DTWEXBGS"

    # Volatility Index (VIX)
    # Series: VIXCLS
    FRED_VIX_SERIES: str = "VIXCLS"

    # 10-Year Treasury Yield
    # Series: DGS10
    FRED_TREASURY_10Y_SERIES: str = "DGS10"


    # Gross Domestic Product
    # Series: GDP
    FRED_GDP_SERIES: str = "GDP"


    # Unemployment Rate
    # Series: UNRATE
    FRED_UNEMPLOYMENT_SERIES: str = "UNRATE"

    # High Yield Corporate Bond Spread
    # Series: BAMLH0A0HYM2
    FRED_HIGH_YIELD_SPREAD_SERIES: str = "BAMLH0A0HYM2"

    # NASDAQ Composite Index
    # Series: NASDAQCOM
    FRED_NASDAQ_COMPOSITE_SERIES: str = "NASDAQCOM"


    # FRED API rate limiting delay
    # Prevent excessive requests
    FRED_REQUEST_DELAY: float = 0.5

    # ============================================
    # FRED ECONOMIC CALENDAR
    # ============================================
    # FRED calendar releases mapping for monthly economic events. The keys are event types, and the values are FRED release IDs.
    FRED_CALENDAR_RELEASES: dict = {
        "fed": 101,
        "cpi": 10,
        "employment": 50,
        "gdp": 53,
        "vix": 200,
        "m2_money_supply": 21,
        "dxy": 245, 
        "nasdaq": 328,
        "high_yield_spread": 209,
        "ten_year_treasury": 18,
    }

    FRED_CALENDAR_LOOKBACK_DAYS: int = 365 


    # Cache TTL for indicators in seconds
    MACRO_INDICATORS_CACHE_TTL: int = 3600

    # ============================================
    # MACROECONOMIC REGIME CLASSIFICATION
    # ============================================
    MACRO_REGIME_CACHE_TTL: int = 3600

    # CPI thresholds used by the regime classification engine.
    # Values can be overridden through environment variables.

    INFLATION_THRESHOLD: float = 3.0
    LOW_INFLATION_THRESHOLD: float = 2.0
    GDP_GROWTH_THRESHOLD: float = 2.0

    # Approximate period used for interest-rate trend detection.
    DAYS_IN_YEAR: int = 365
    DAYS_IN_3_MONTHS: int = 90


    # ============================================
    # CURRENT REGIME CONFIDENCE
    # ============================================

    REGIME_CONFIDENCE_CPI_WEIGHT: float = 40.0
    REGIME_CONFIDENCE_RATE_WEIGHT: float = 30.0
    REGIME_CONFIDENCE_GDP_WEIGHT: float = 30.0

    REGIME_HIGH_CONFIDENCE_THRESHOLD: float = 80.0

    REGIME_VISUAL_INDICATORS: dict = {
        "high_inflation": "bear",
        "low_inflation": "bull",
        "rising_rates": "bear",
        "falling_rates": "bull",
        "recession": "recession",
        "growth": "bull",
    }

    CURRENT_REGIME_UPDATE_HOUR_UTC: int = 1
    CURRENT_REGIME_UPDATE_MINUTE_UTC: int = 0


    # Development/testing only.
    # Set > 0 to run current-regime processing every N minutes.
    CURRENT_REGIME_UPDATE_INTERVAL_MINUTES: int = 0

    # Development/testing only.
    REGIME_PERFORMANCE_QA_MODE: bool = True
    REGIME_EVENT_QA_MODE: bool = True

    # ============================================
    # REGIME EVENT ANALYSIS (UNIT 2, Option A)
    # ============================================
    #
    # Daily job that computes BTC's reaction to recent
    # economic events and writes one row per
    # (regime_id, event_type, event_date) triple to
    # regime_event_analysis.
    #
    # Source events come from economic_events (populated by
    # EconomicCalendarService from FRED). The service filters
    # them to:
    #   - impact_level in {high, medium}
    #   - event_date within the last 90 days
    #   - event_date at least 24h in the past (so the +24h
    #     window has a price to look up)
    #
    # For each event it computes BTC's return over the
    # symmetric window [event - 24h, event + 24h] using a
    # PIT-correct price lookup (last btc_prices tick with
    # time <= endpoint).
    #
    # 01:15 UTC is staggered after the 01:00 UTC current-regime
    # job (which refreshes current_regime and reconciles the
    # open macro_regimes row) so the event analysis always
    # attaches to a fresh regime_id.
    #
    # Idempotent: existing (regime_id, event_type, event_date)
    # triples are skipped via a pre-check in the service.
    #
    # See app/services/regime_event_service.py and
    # app/services/scheduler.py::periodic_regime_event_analysis.

    REGIME_EVENT_UPDATE_HOUR_UTC: int = 1
    REGIME_EVENT_UPDATE_MINUTE_UTC: int = 15

    # ============================================
    # COLLECTION INTERVALS (seconds)
    # ============================================
    PRICE_COLLECTION_INTERVAL: int = 60
    ECONOMIC_COLLECTION_INTERVAL: int = 3600
    WEBSOCKET_RECONNECT_DELAY: int = 5

    # ============================================
    # SCHEDULED JOBS
    # ============================================

    # Macroeconomic update schedule (production)
    MACRO_UPDATE_HOUR_UTC: int = 1
    MACRO_UPDATE_MINUTE_UTC: int = 0

    # Development/testing only.
    # Set to a value > 0 to run every N minutes instead of once per day.
    MACRO_UPDATE_INTERVAL_MINUTES: int = 0

    # ============================================
    # HOURLY GAP SCAN (Phase B, Chat 4, C4-3)
    # ============================================
    #
    # Background task that scans btc_prices_hourly and
    # macro_indicators_hourly for gaps, classifies each missing
    # hour as MATERIALIZATION_GAP or RAW_DATA_GAP, and logs a
    # warning if any gaps exist. Read-only: never auto-repairs.
    #
    # Runs once at startup, then every INTERVAL_HOURS.
    # See docs/data-service-hourly-runbook.md for the operator
    # playbook (how to repair gaps found by this scan).

    # Master switch. Set to False to disable the background
    # scan entirely. The CLI path
    # (verify_hourly_tables.py) is unaffected by this flag.
    HOURLY_GAP_SCAN_ENABLED: bool = True

    # How often the scan runs, in hours.
    # Default 6h: frequent enough to notice a broken writer the
    # same day, infrequent enough not to spam logs on a healthy
    # system.
    HOURLY_GAP_SCAN_INTERVAL_HOURS: float = 6.0

    # Look-back window for each scan, in hours.
    # Default 168h = 7 days. Long enough to catch weekend gaps
    # (when a backfill might have been missed) without scanning
    # all history on every run.
    HOURLY_GAP_SCAN_LOOKBACK_HOURS: int = 168

    # ============================================
    # HIGH YIELD CREDIT STRESS PROXY (Phase B, Chat 5, B5)
    # ============================================
    #
    # Daily job that computes (HYG / SHY).pct_change() and writes
    # one row per trading day into the raw macro_indicators table
    # with:
    #     indicator_name = 'high_yield_credit_stress_proxy'
    #     source         = 'derived'
    #
    # This value is consumed by features_db as the
    # high_yield_credit_stress_proxy column (see
    # docs/data-service-schemas.md §5, row 14). The features
    # writer treats it as a market feature and ffills it
    # without a limit.
    #
    # The timestamp written is midnight UTC of the observation
    # day, NOT datetime.now(). This is required for two reasons:
    #
    #   1. Idempotency. Same calendar day -> same timestamp, so
    #      the ON CONFLICT (time, indicator_name) constraint in
    #      MacroIndicatorRepository.create_many deduplicates
    #      correctly. datetime.now() would produce a different
    #      row on every run.
    #
    #   2. PIT correctness. The features writer picks the latest
    #      observation with time <= the feature hour. Midnight
    #      UTC means "the value for day D" is available for
    #      every hour of day D, which is what a daily series
    #      means.
    #
    # Note: this differs from gold_spot, which uses
    # datetime.now() because it is a point-in-time snapshot,
    # not a daily series. See the service docstring for detail.

    # Production schedule for the daily HY proxy collection.
    # 03:00 UTC is staggered after the 01:00 UTC macro/FRED
    # task and before the 03:30 UTC vintages task (B6).
    HY_PROXY_UPDATE_HOUR_UTC: int = 3
    HY_PROXY_UPDATE_MINUTE_UTC: int = 0

    # Yahoo Finance history window per run, in days.
    #
    # 730 (2 years) covers the largest plausible multi-day
    # outage, and the writer is idempotent, so a wide window is
    # free on a healthy system: the ON CONFLICT clause skips
    # every day already stored.
    #
    # If Yahoo ever changes its history retention policy such
    # that 2y daily candles are no longer returned, lower this
    # value. A shorter window is still correct — it just means
    # a longer outage needs an explicit backfill instead of
    # being absorbed by the next scheduled run.
    HY_PROXY_LOOKBACK_DAYS: int = 730

    # ============================================
    # MACRO INDICATOR VINTAGES (Phase B, Chat 5, B6)
    # ============================================
    #
    # Daily job that fetches the full revision history (vintages)
    # of 5 revision-prone FRED series and writes them to
    # macro_indicator_vintages:
    #
    #     cpi                 <- CPIAUCSL
    #     unemployment        <- UNRATE
    #     federal_funds_rate  <- FEDFUNDS
    #     m2_money_supply     <- M2SL
    #     gdp                 <- GDP
    #
    # Why vintages matter: FRED revisions mean the value known
    # for an observation changes over time. Training a model on
    # the *final* value of, say, January 2024 CPI leaks future
    # information. Vintages preserve every release so the
    # features writer (B4) can merge point-in-time.
    #
    # Consumed by features_db for 5 of its 53 columns:
    #     cpi, federal_funds_rate, gdp, m2_money_supply,
    #     unemployment.
    # See docs/data-service-schemas.md §5, rows 15-19, and §6.1
    # for the rename map.
    #
    # Retention is unlimited (a few thousand rows per series per
    # year after the no-op filter).
    #
    # No-op filter: consecutive releases for the same
    # (series_id, observation_date) where the value did not
    # change are collapsed to the first. Halves the row count;
    # does not change PIT merge results. Applied in the service,
    # not the table; see migration 008 and
    # app/services/macro_vintage_service.py for detail.

    # Production schedule for the daily vintage collection.
    # 03:30 UTC is staggered after the 03:00 UTC HY proxy job
    # (B5) and after the 01:00 UTC macro/FRED task.
    VINTAGE_UPDATE_HOUR_UTC: int = 3
    VINTAGE_UPDATE_MINUTE_UTC: int = 30

    # Lookback window per run, in years.
    #
    # 20 years covers any realistic ML training window. The
    # first run fetches the full window per series (a one-time
    # cost; FRED's response time dominates); subsequent runs
    # are effectively free because every already-stored triple
    # is skipped by the ON CONFLICT clause.
    #
    # The CLI can override this per run with --years N.
    # Lowering this is safe; raising it re-fetches history that
    # will be deduplicated.
    VINTAGE_LOOKBACK_YEARS: int = 20

    # ============================================
    # FEATURES_DB (Phase B, Chat 5, B4)
    # ============================================
    #
    # The ML feature table. Populated hourly by FeaturesDBWriter,
    # which calls FeatureBuilderService.build_features() and
    # persists the 53-column contract v2 vector to features_db.
    #
    # Consumed by the AI Service via the DB path
    # (fetch_training_frame_from_features_db) once its config
    # defaults point at the hourly tables.
    #
    # See:
    #   - migrations/009_create_features_db.sql  (DDL)
    #   - app/services/feature_builder_service.py  (SSOT)
    #   - app/services/features_db_writer.py  (DB writer)
    #   - app/services/features_parquet_writer.py  (Option B parquet)
    #   - docs/data-service-schemas.md §3, §5

    # Minute offset for the hourly features_db write.
    #
    # The write runs at :05 every hour, staggered after the
    # hourly materializers (BTC at :01, macro at :02) so a slow
    # upstream writer does not delay features_db.
    #
    # There is no FEATURES_DB_UPDATE_HOUR_UTC because the job
    # is hourly, not daily. The minute offset is applied to
    # every hour via wait_until_next_hour().
    FEATURES_DB_UPDATE_MINUTE_UTC: int = 5

    # Output directory for the Option B parquet set.
    #
    # Contains five self-contained artifacts:
    #   train_scaled.parquet
    #   val_scaled.parquet
    #   test_scaled.parquet
    #   live_frontier_scaled.parquet
    #   feature_scaler.pkl
    #
    # This is a SEPARATE directory from app/data/processed/
    # (which is frozen, D13, D21). Never write to processed/.
    #
    # Relative to the data-service working directory. Override
    # in .env.local for non-default deployments.
    FEATURES_DB_PARQUET_DIR: str = "app/data/processed_v2_builder"

    # ============================================
    # RATE LIMITING
    # ============================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100

    # Rate-limit window in seconds.
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Delay between requests during rate-limit integration tests.
    RATE_LIMIT_TEST_DELAY_SECONDS: float = 0.05

    # Number of requests kept below the configured rate limit
    # during integration tests.
    RATE_LIMIT_TEST_SAFETY_MARGIN: int = 5

    # Number of additional requests used to trigger
    # the rate limit during integration tests.
    RATE_LIMIT_TEST_TRIGGER_REQUESTS: int = 10

    # Additional buffer after the rate-limit window expires.
    RATE_LIMIT_TEST_RESET_BUFFER_SECONDS: int = 5

# ============================================
    # API RESPONSE TIME
    # ============================================

    # Maximum acceptable response time for the BTC price endpoint.
    # BTC uses Redis caching and has a stricter performance target.
    BTC_PRICE_RESPONSE_TIME_LIMIT_MS: int = 200

    # Maximum acceptable response time for standard API endpoints.
    API_RESPONSE_TIME_LIMIT_MS: int = 500

    # Number of repeated requests used by response-time tests.
    RESPONSE_TIME_TEST_REQUEST_COUNT: int = 5

    # BTC chart history (GET /api/v1/btc/price/history)
    PRICE_HISTORY_MAX_POINTS: int = 500
    PRICE_HISTORY_CACHE_TTL: int = 60


    # ============================================
    # DEVELOPMENT
    # ============================================
    RELOAD: bool = False
    DEBUG: bool = False
    
    @property
    def IS_IN_DOCKER(self) -> bool:
        """Detect if running inside a Docker container"""
        return os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
    

@lru_cache()
def get_settings() -> Settings:
    """Cache settings for better performance"""
    return Settings()


settings = get_settings()