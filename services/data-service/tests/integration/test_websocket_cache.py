"""
Integration tests for T4.3 - WebSocket Redis cache.

Acceptance Criteria:
- Redis cache configured for BTC price storage
- Current price updated on every WebSocket message
- Cache TTL configured (5 seconds)
- Cache invalidated/replaced on price update
"""

import pytest

from app.cache.client import CacheClient
from app.config import settings
from tests.fixtures.mock_data import MOCK_PRICE_SNAPSHOT


@pytest.mark.integration
class TestWebSocketCache:
    """Integration tests for WebSocket Redis cache."""

    @pytest.mark.asyncio
    async def test_btc_price_cache_storage(self):
        """
        Verify BTC price snapshot is stored in Redis.
        """

        cache = CacheClient()
        await cache.connect()

        if not cache.is_connected:
            pytest.skip("Redis not connected")

        key = "btc_price_snapshot"

        result = await cache.set(
            key,
            MOCK_PRICE_SNAPSHOT,
            ttl=5,
        )

        assert result is True

        cached = await cache.get(key)

        assert cached is not None
        assert cached["current_price"] == MOCK_PRICE_SNAPSHOT["current_price"]
        assert cached["change_24h"] == MOCK_PRICE_SNAPSHOT["change_24h"]

        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_btc_price_cache_ttl(self):
        """
        Verify BTC snapshot is cached with a TTL.
        """

        cache = CacheClient()
        await cache.connect()

        if not cache.is_connected:
            pytest.skip("Redis not connected")

        key = "btc_price_snapshot"

        await cache.set(
            key,
            MOCK_PRICE_SNAPSHOT,
            ttl=5,
        )

        ttl = await cache.client.ttl(key)

        assert ttl > 0
        assert ttl <= 5

        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_btc_price_cache_updates_on_new_websocket_message(self):
        """
        Verify new WebSocket data replaces the existing cache entry.
        """

        cache = CacheClient()
        await cache.connect()

        if not cache.is_connected:
            pytest.skip("Redis not connected")

        key = "btc_price_snapshot"

        first_snapshot = MOCK_PRICE_SNAPSHOT.copy()
        first_snapshot["current_price"] = 45000.0

        second_snapshot = MOCK_PRICE_SNAPSHOT.copy()
        second_snapshot["current_price"] = 45500.0

        await cache.set(key, first_snapshot, ttl=5)

        cached = await cache.get(key)
        assert cached["current_price"] == 45000.0

        await cache.set(key, second_snapshot, ttl=5)

        cached = await cache.get(key)

        assert cached["current_price"] == 45500.0
        assert cached["current_price"] != first_snapshot["current_price"]

        await cache.delete(key)

    @pytest.mark.asyncio
    async def test_btc_price_cache_key_exists(self):
        """
        Verify Redis contains the BTC snapshot key after caching.
        """

        cache = CacheClient()
        await cache.connect()

        if not cache.is_connected:
            pytest.skip("Redis not connected")

        key = "btc_price_snapshot"

        await cache.set(
            key,
            MOCK_PRICE_SNAPSHOT,
            ttl=5,
        )

        exists = await cache.exists(key)

        assert exists is True

        await cache.delete(key)