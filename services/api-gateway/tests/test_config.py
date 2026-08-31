"""Tests for configuration management."""

import os
import pytest
from unittest.mock import patch

from app.core.config import Settings, get_settings, settings


class TestSettings:
    """Test settings loading and validation."""

    def test_default_settings(self):
        """Test default values are loaded correctly."""
        assert settings.SERVICE_NAME == "api-gateway"
        assert settings.SERVICE_PORT == 8000
        assert settings.REDIS_HOST == "redis"
        assert settings.RABBITMQ_HOST == "rabbitmq"
        assert settings.JWT_ALGORITHM == "HS256"

    def test_settings_from_env(self):
        """Test settings can be overridden by environment variables."""
        with patch.dict(os.environ, {
            "SERVICE_NAME": "test-gateway",
            "SERVICE_PORT": "9000",
            "LOG_LEVEL": "DEBUG",
        }):
            test_settings = Settings()
            assert test_settings.SERVICE_NAME == "test-gateway"
            assert test_settings.SERVICE_PORT == 9000
            assert test_settings.LOG_LEVEL == "DEBUG"

    def test_rabbitmq_url_property(self):
        """Test RabbitMQ URL is built correctly."""
        expected = "amqp://guest:guest@rabbitmq:5672/"
        assert settings.RABBITMQ_URL == expected

    def test_cors_origins_parsing(self):
        """Test CORS origins are parsed correctly from string."""
        with patch.dict(os.environ, {
            "CORS_ALLOW_ORIGINS": '["http://test.com","https://test2.com"]'
        }):
            test_settings = Settings()
            assert "http://test.com" in test_settings.CORS_ALLOW_ORIGINS
            assert "https://test2.com" in test_settings.CORS_ALLOW_ORIGINS

    def test_invalid_log_level(self):
        """Test invalid log level raises validation error."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValueError):
                Settings()

    def test_get_settings_singleton(self):
        """Test get_settings returns the same instance."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        assert s1.SERVICE_NAME == s2.SERVICE_NAME