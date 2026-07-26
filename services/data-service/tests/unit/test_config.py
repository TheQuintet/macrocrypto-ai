"""
Unit tests for configuration.
"""

import os
import pytest
from app.config import settings


class TestConfig:
    """Test suite for configuration."""

    def test_service_settings(self):
        assert settings.SERVICE_NAME == "data-service"
        assert settings.SERVICE_PORT == 8001
        assert settings.LOG_LEVEL == "INFO"

    def test_database_settings(self):
        assert "postgresql" in settings.DATABASE_URL
        assert settings.DATABASE_POOL_SIZE == 5
        assert settings.DATABASE_MAX_OVERFLOW == 10

    def test_redis_settings(self):
        assert settings.REDIS_ENABLED is True
        assert settings.REDIS_HOST == "redis"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_DB == 0
        assert settings.REDIS_CACHE_TTL == 300

    def test_redis_connection_url(self):
        expected = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        assert settings.REDIS_CONNECTION_URL == expected

    def test_rabbitmq_settings(self):
        assert settings.RABBITMQ_HOST == "rabbitmq"
        assert settings.RABBITMQ_PORT == 5672
        assert settings.RABBITMQ_USER == "guest"
        assert settings.RABBITMQ_PASSWORD == "guest"

    def test_binance_settings(self):
        assert settings.BINANCE_REST_URL == "https://api.binance.com/api/v3"
        assert settings.BINANCE_TESTNET_URL == "https://testnet.binance.vision/api/v3"
        assert settings.BINANCE_USE_TESTNET is False
        assert settings.BINANCE_WS_URL == "wss://stream.binance.com:9443/ws"
        assert settings.BINANCE_DEFAULT_SYMBOL == "BTCUSDT"

    def test_fred_settings(self):
        """Test FRED configuration settings."""
        assert settings.FRED_API_URL == "https://api.stlouisfed.org/fred"
        # ✅ Allow placeholder value or None
        assert settings.FRED_API_KEY in (None, "your_api_key_here")

    def test_collection_intervals(self):
        assert settings.PRICE_COLLECTION_INTERVAL == 60
        assert settings.ECONOMIC_COLLECTION_INTERVAL == 3600
        assert settings.WEBSOCKET_RECONNECT_DELAY == 5

    def test_rate_limiting_settings(self):
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS == 100

    def test_in_docker_detection(self):
        """Test Docker environment detection."""
        # ✅ If running in Docker, this will be True
        # Check if we're in a container
        import os
        in_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
        assert settings.IS_IN_DOCKER == in_docker