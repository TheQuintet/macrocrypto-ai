"""Environment configuration for data-service"""

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