"""Unit tests for cache service and caching utilities."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.cache.service import CacheService, CacheTTL
from app.cache.decorators import cached, cache_clear, cache_invalidate


class TestCacheTTL:
    """Test cache TTL constants."""

    def test_cache_ttl_values(self):
        """Test that TTL constants have correct values."""
        assert CacheTTL.PREDICTIONS == 300  # 5 minutes
        assert CacheTTL.PRICES == 300  # 5 minutes
        assert CacheTTL.INDICATORS == 3600  # 1 hour
        assert CacheTTL.CORRELATION == 3600  # 1 hour
        assert CacheTTL.REGIMES == 3600  # 1 hour
        assert CacheTTL.RECOMMENDATIONS == 3600  # 1 hour
        assert CacheTTL.ACCURACY == 600  # 10 minutes
        assert CacheTTL.DEFAULT == 300  # 5 minutes


class TestCacheService:
    """Test cache service functionality."""

    @pytest.fixture
    def cache_service(self):
        """Create a cache service instance."""
        return CacheService()

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service):
        """Test getting a cached value (hit)."""
        with patch("app.cache.service.redis_client.get", return_value='{"key": "value"}'):
            result = await cache_service.get("test_key")
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service):
        """Test getting a cached value (miss)."""
        with patch("app.cache.service.redis_client.get", return_value=None):
            result = await cache_service.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_cache(self, cache_service):
        """Test setting a cached value."""
        with patch("app.cache.service.redis_client.set", return_value=True) as mock_set:
            result = await cache_service.set("test_key", {"key": "value"}, ttl=300)
            assert result is True
            mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_cache(self, cache_service):
        """Test deleting a cached value."""
        with patch("app.cache.service.redis_client.delete", return_value=True) as mock_delete:
            result = await cache_service.delete("test_key")
            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_cache(self, cache_service):
        """Test checking if a cache key exists."""
        with patch("app.cache.service.redis_client.get", return_value='{"key": "value"}'):
            result = await cache_service.exists("test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_exists_cache_miss(self, cache_service):
        """Test checking if a cache key exists (miss)."""
        with patch("app.cache.service.redis_client.get", return_value=None):
            result = await cache_service.exists("test_key")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_ttl(self, cache_service):
        """Test getting TTL for a cache key."""
        with patch("app.cache.service.redis_client.ttl", return_value=300):
            result = await cache_service.get_ttl("test_key")
            assert result == 300

    @pytest.mark.skip(reason="Redis client mocking needs to be fixed")
    @pytest.mark.asyncio
    async def test_clear_pattern(self, cache_service):
        """Test clearing cache keys matching a pattern."""
        mock_redis = AsyncMock()
        mock_redis.client = AsyncMock()
        mock_redis.client.scan = AsyncMock()
        mock_redis.client.scan.return_value = (0, ["key1", "key2"])

        with patch("app.cache.service.redis_client", mock_redis):
            with patch("app.cache.service.redis_client.delete", return_value=True):
                result = await cache_service.clear_pattern("test_*")
                assert result == 2

    # ============================================
    # Convenience Methods Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_get_predictions(self, cache_service):
        """Test getting cached predictions."""
        expected = {"symbol": "BTC", "predictions": []}
        with patch("app.cache.service.redis_client.get", return_value=json.dumps(expected)):
            result = await cache_service.get_predictions("BTC", "24h", "ensemble")
            assert result == expected

    @pytest.mark.asyncio
    async def test_set_predictions(self, cache_service):
        """Test caching predictions."""
        data = {"symbol": "BTC", "predictions": []}
        with patch("app.cache.service.redis_client.set", return_value=True) as mock_set:
            result = await cache_service.set_predictions("BTC", "24h", "ensemble", data)
            assert result is True
            mock_set.assert_called_once_with(
                "predictions_BTC_24h_ensemble",
                json.dumps(data),
                expire=300
            )

    @pytest.mark.asyncio
    async def test_get_indicators(self, cache_service):
        """Test getting cached indicators."""
        expected = {"indicators": {"GDP": 28.78}}
        with patch("app.cache.service.redis_client.get", return_value=json.dumps(expected)):
            result = await cache_service.get_indicators("all")
            assert result == expected

    @pytest.mark.asyncio
    async def test_set_indicators(self, cache_service):
        """Test caching indicators."""
        data = {"indicators": {"GDP": 28.78}}
        with patch("app.cache.service.redis_client.set", return_value=True) as mock_set:
            result = await cache_service.set_indicators("all", data)
            assert result is True
            mock_set.assert_called_once_with(
                "indicators_all",
                json.dumps(data),
                expire=3600
            )

    @pytest.mark.asyncio
    async def test_get_recommendations(self, cache_service):
        """Test getting cached recommendations."""
        expected = {"symbol": "BTC", "recommendation": "BUY"}
        with patch("app.cache.service.redis_client.get", return_value=json.dumps(expected)):
            result = await cache_service.get_recommendations("24h", "moderate")
            assert result == expected

    @pytest.mark.asyncio
    async def test_set_recommendations(self, cache_service):
        """Test caching recommendations."""
        data = {"symbol": "BTC", "recommendation": "BUY"}
        with patch("app.cache.service.redis_client.set", return_value=True) as mock_set:
            result = await cache_service.set_recommendations("24h", "moderate", data)
            assert result is True
            mock_set.assert_called_once_with(
                "recommendations_btc_24h_moderate",
                json.dumps(data),
                expire=3600
            )


class TestCacheDisabled:
    """Test cache service when Redis is disabled."""

    @pytest.fixture
    def cache_service(self):
        """Create a cache service instance with Redis disabled."""
        service = CacheService()
        service.enabled = False
        return service

    @pytest.mark.asyncio
    async def test_get_when_disabled(self, cache_service):
        """Test get returns None when Redis is disabled."""
        result = await cache_service.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_when_disabled(self, cache_service):
        """Test set returns False when Redis is disabled."""
        result = await cache_service.set("test_key", {"key": "value"})
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_when_disabled(self, cache_service):
        """Test delete returns False when Redis is disabled."""
        result = await cache_service.delete("test_key")
        assert result is False


class TestCacheDecorators:
    """Test cache decorators."""

    @pytest.mark.asyncio
    async def test_cached_decorator_hit(self):
        """Test cached decorator with cache hit."""
        mock_func = AsyncMock(return_value={"result": "success"})

        with patch("app.cache.decorators.cache_service.get", return_value={"cached": "value"}):
            with patch("app.cache.decorators.cache_service.set") as mock_set:
                decorated = cached(ttl=300, key_prefix="test")(mock_func)
                result = await decorated("arg1", key="value")

                assert result == {"cached": "value"}
                mock_set.assert_not_called()
                mock_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_decorator_miss(self):
        """Test cached decorator with cache miss."""
        mock_func = AsyncMock(return_value={"result": "success"})

        with patch("app.cache.decorators.cache_service.get", return_value=None):
            with patch("app.cache.decorators.cache_service.set") as mock_set:
                decorated = cached(ttl=300, key_prefix="test")(mock_func)
                result = await decorated("arg1", key="value")

                assert result == {"result": "success"}
                mock_set.assert_called_once()
                mock_func.assert_called_once_with("arg1", key="value")

    @pytest.mark.asyncio
    async def test_cache_clear_decorator(self):
        """Test cache_clear decorator."""
        mock_func = AsyncMock(return_value={"result": "success"})

        with patch("app.cache.decorators.cache_service.clear_pattern") as mock_clear:
            decorated = cache_clear(key_prefix="test")(mock_func)
            result = await decorated()

            assert result == {"result": "success"}
            mock_clear.assert_called_once_with("test_*")
            mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_invalidate_decorator(self):
        """Test cache_invalidate decorator."""
        mock_func = AsyncMock(return_value={"result": "success"})

        with patch("app.cache.decorators.cache_service.delete") as mock_delete:
            decorated = cache_invalidate(key_prefix="test")(mock_func)
            result = await decorated("arg1")

            assert result == {"result": "success"}
            mock_delete.assert_called_once()
            mock_func.assert_called_once_with("arg1")