"""
Integration tests for Redis cache behavior.

Validates:
- Redis connection and availability
- Cache set/get operations
- Cache TTL (Time To Live)
- Cache invalidation
- Graceful degradation when Redis is unavailable
"""

import pytest
import time
import json
import redis
from app.cache.client import CacheClient
from app.config import settings


@pytest.mark.integration
class TestRedisCache:
    """Test suite for Redis cache functionality."""

    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test Redis connection."""

        cache = CacheClient()

        result = await cache.connect()

        if settings.REDIS_ENABLED and not result:
            pytest.skip(
                "Redis is enabled but unavailable"
            )

        if settings.REDIS_ENABLED:
            assert result is True
            assert cache.is_connected is True

        else:
            assert result is False
            assert cache.is_connected is False

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test setting and getting a value from cache."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        # Test with simple string
        key = "test:string"
        value = "hello world"
        
        result = await cache.set(key, value, ttl=10)
        assert result is True
        
        cached = await cache.get(key)
        assert cached == value
        
        # Clean up
        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_set_and_get_dict(self):
        """Test setting and getting a dictionary from cache."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        key = "test:dict"
        value = {"price": 45000.0, "symbol": "BTCUSDT", "change": 2.27}
        
        result = await cache.set(key, value, ttl=10)
        assert result is True
        
        cached = await cache.get(key)
        assert cached == value
        assert cached["price"] == 45000.0
        assert cached["symbol"] == "BTCUSDT"
        
        # Clean up
        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_set_and_get_list(self):
        """Test setting and getting a list from cache."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        key = "test:list"
        value = [45000.0, 46000.0, 44000.0]
        
        result = await cache.set(key, value, ttl=10)
        assert result is True
        
        cached = await cache.get(key)
        assert cached == value
        assert len(cached) == 3
        
        # Clean up
        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test that cache entries expire after TTL."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        key = "test:ttl"
        value = "expiring_value"
        ttl = 2  # 2 seconds
        
        await cache.set(key, value, ttl=ttl)
        
        # Should exist immediately
        cached = await cache.get(key)
        assert cached == value
        
        # Wait for TTL to expire
        time.sleep(ttl + 1)
        
        # Should be None after expiration
        cached = await cache.get(key)
        assert cached is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting a cache entry."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        key = "test:delete"
        value = "to_be_deleted"
        
        await cache.set(key, value, ttl=10)
        
        # Should exist
        cached = await cache.get(key)
        assert cached == value
        
        # Delete
        result = await cache.delete(key)
        assert result is True
        
        # Should be None
        cached = await cache.get(key)
        assert cached is None

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking if a key exists."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        key = "test:exists"
        value = "exists_value"
        
        # Should not exist initially
        exists = await cache.exists(key)
        assert exists is False
        
        # Set value
        await cache.set(key, value, ttl=10)
        
        # Should exist now
        exists = await cache.exists(key)
        assert exists is True
        
        # Clean up
        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_get_or_set(self):
        """Test get_or_set pattern."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        key = "test:get_or_set"
        
        # First call should execute function and cache result
        call_count = 0
        
        async def expensive_function():
            nonlocal call_count
            call_count += 1
            return 45000.0
        
        result1 = await cache.get_or_set(key, expensive_function, ttl=10)
        assert result1 == 45000.0
        assert call_count == 1
        
        # Second call should return cached value without calling function
        result2 = await cache.get_or_set(key, expensive_function, ttl=10)
        assert result2 == 45000.0
        assert call_count == 1  # Function not called again
        
        # Clean up
        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_get_price(self):
        """Test get_price convenience method."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        symbol = "BTCUSDT"
        price_data = {"price": 45000.0, "symbol": symbol}
        
        # Set price
        result = await cache.set_price(symbol, price_data)
        assert result is True
        
        # Get price
        cached = await cache.get_price(symbol)
        assert cached == price_data
        assert cached["price"] == 45000.0
        
        # Clean up
        await cache.delete(f"price:{symbol.lower()}")

    @pytest.mark.asyncio
    async def test_get_economic(self):
        """Test get_economic convenience method."""
        cache = CacheClient()
        await cache.connect()
        
        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")
        
        indicator = "CPI"
        economic_data = {"value": 3.4, "timestamp": "2024-01-01"}
        
        # Set economic data
        result = await cache.set_economic(indicator, economic_data)
        assert result is True
        
        # Get economic data
        cached = await cache.get_economic(indicator)
        assert cached == economic_data
        assert cached["value"] == 3.4
        
        # Clean up
        await cache.delete(f"economic:{indicator.lower()}")

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint."""
        cache = CacheClient()
        await cache.connect()
        
        health = await cache.health_check()
        
        if settings.REDIS_ENABLED and cache.is_connected:
            assert health["status"] == "healthy"
            assert "version" in health
            assert "uptime_seconds" in health
        elif settings.REDIS_ENABLED and not cache.is_connected:
            assert health["status"] == "disconnected"
        else:
            assert health["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_ping(self):
        """Test ping method."""
        cache = CacheClient()
        await cache.connect()
        
        if cache.is_connected:
            result = await cache.ping()
            assert result is True
        else:
            result = await cache.ping()
            assert result is False

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when Redis is unavailable."""
        # Create cache client with Redis disabled
        cache = CacheClient()
        cache.is_enabled = False
        
        # Should not raise exceptions
        result = await cache.set("test", "value")
        assert result is False
        
        cached = await cache.get("test")
        assert cached is None
        
        exists = await cache.exists("test")
        assert exists is False
        
        ping = await cache.ping()
        assert ping is False

    @pytest.mark.asyncio
    async def test_cached_btc_price_snapshot_consistency(self):
        """
        Test that BTC price snapshot data remains unchanged
        after being stored and retrieved from Redis.

        Validates:
        - Redis stores BTC price snapshot correctly
        - Redis returns the same cached data
        - Cached market data fields remain consistent
        """
        cache = CacheClient()
        await cache.connect()

        if not cache.is_connected:
            pytest.skip("Redis not connected, skipping test")

        key = "test:btc_price_snapshot"

        price_snapshot = {
            "current_price": 64000.0,
            "change_24h": -429.19,
            "change_24h_percent": -0.666,
            "high_24h": 64744.81,
            "low_24h": 63267.34,
            "volume_24h": 16893.17508,
            "change_7d": -1066.40,
            "change_7d_percent": -1.6381,
            "updated_at": "2026-07-30T07:08:40Z"
        }

        # Store BTC snapshot in Redis
        result = await cache.set(
            key,
            price_snapshot,
            ttl=10
        )

        assert result is True

        # Retrieve cached snapshot
        cached_snapshot = await cache.get(key)

        assert cached_snapshot is not None

        # Validate complete object consistency
        assert cached_snapshot == price_snapshot

        # Validate important BTC fields
        assert cached_snapshot["current_price"] == 64000.0
        assert cached_snapshot["change_24h"] == -429.19
        assert cached_snapshot["change_7d"] == -1066.40
        assert cached_snapshot["change_7d_percent"] == -1.6381

        # Cleanup
        await cache.delete(key)