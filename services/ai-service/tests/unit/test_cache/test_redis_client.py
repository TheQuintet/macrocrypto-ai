"""Unit tests for the Redis client lifecycle module.

These tests do NOT connect to Redis. They mock
`redis.asyncio.from_url` to verify that:
    - The client is created lazily
    - The client is cached across calls
    - close_redis() disposes the client
    - ping_redis() returns True/False appropriately

Test organization:
    - TestGetRedis: lazy creation + caching
    - TestCloseRedis: disposal + idempotency
    - TestPingRedis: health check wrapper
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.cache import redis_client as redis_module
from app.cache.redis_client import (
    close_redis,
    get_redis,
    ping_redis,
)


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset the module-level `_redis` global between tests."""
    redis_module._redis = None
    yield
    redis_module._redis = None


@pytest.fixture
def fake_client():
    """Return an AsyncMock that mimics aioredis.Redis."""
    client = MagicMock()
    client.ping = AsyncMock(return_value=True)
    client.aclose = AsyncMock()
    return client


# ============================================================
# GET REDIS
# ============================================================
class TestGetRedis:
    """Tests for get_redis()."""

    @pytest.mark.asyncio
    async def test_creates_client_on_first_call(self, fake_client) -> None:
        """Test that the client is created on first call."""
        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ) as mock_from_url:
            client = await get_redis()

        assert client is fake_client
        mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_same_client_on_second_call(
        self, fake_client
    ) -> None:
        """Test that the client is cached across calls."""
        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ) as mock_from_url:
            first = await get_redis()
            second = await get_redis()

        assert first is second
        # from_url called only once
        mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_decode_responses(self, fake_client) -> None:
        """Test that the client is created with decode_responses=True."""
        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ) as mock_from_url:
            await get_redis()

        _, kwargs = mock_from_url.call_args
        assert kwargs.get("decode_responses") is True


# ============================================================
# CLOSE REDIS
# ============================================================
class TestCloseRedis:
    """Tests for close_redis()."""

    @pytest.mark.asyncio
    async def test_closes_client(self, fake_client) -> None:
        """Test that close_redis calls aclose on the client."""
        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ):
            await get_redis()
            await close_redis()

        fake_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_resets_module_state(self, fake_client) -> None:
        """Test that after close_redis, _redis is None."""
        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ):
            await get_redis()
            await close_redis()

        assert redis_module._redis is None

    @pytest.mark.asyncio
    async def test_safe_when_never_created(self) -> None:
        """Test that close_redis is safe when no client exists."""
        await close_redis()  # should not raise

    @pytest.mark.asyncio
    async def test_swallows_close_errors(self, fake_client) -> None:
        """Test that close errors are logged and swallowed."""
        fake_client.aclose = AsyncMock(side_effect=Exception("boom"))

        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ):
            await get_redis()
            await close_redis()  # should not raise

        assert redis_module._redis is None


# ============================================================
# PING REDIS
# ============================================================
class TestPingRedis:
    """Tests for ping_redis()."""

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self, fake_client) -> None:
        """Test that ping_redis returns True on a healthy server."""
        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ):
            result = await ping_redis()

        assert result is True
        fake_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_on_error(self, fake_client) -> None:
        """Test that ping_redis returns False when ping raises."""
        fake_client.ping = AsyncMock(side_effect=ConnectionError("down"))

        with patch.object(
            redis_module.aioredis, "from_url", return_value=fake_client
        ):
            result = await ping_redis()

        assert result is False