"""Tests for the Redis client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.redis import RedisClient, redis_client
from app.core.config import settings


@pytest.fixture
def client():
    """Create a fresh RedisClient for each test."""
    return RedisClient()


@pytest.fixture
def mock_redis():
    """Create a mock async Redis connection."""
    mock = MagicMock()
    mock.ping = AsyncMock()
    mock.close = AsyncMock()
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.incr = AsyncMock()
    mock.delete = AsyncMock()
    mock.ttl = AsyncMock()
    return mock


class TestRedisClientInitialization:
    """Test Redis client initialization."""

    def test_initial_state(self, client):
        """Test client starts disconnected."""
        assert client.client is None
        assert client._connected is False

    def test_singleton_exists(self):
        """Test module-level Redis client exists."""
        assert isinstance(redis_client, RedisClient)


class TestRedisConnect:
    """Test Redis connection handling."""

    @pytest.mark.asyncio
    async def test_connect_when_redis_disabled(self, client):
        """Test connection is skipped when Redis is disabled."""
        with patch("app.core.redis.settings.REDIS_ENABLED", False):
            await client.connect()

        assert client.client is None
        assert client._connected is False




    @pytest.mark.asyncio
    async def test_connect_success(self, client, mock_redis):
        """Test successful Redis connection."""
        with (
            patch("app.core.redis.settings.REDIS_ENABLED", True),
            patch(
                "app.core.redis.redis.from_url",
                return_value=mock_redis,
            ) as mock_from_url,
        ):
            await client.connect()

        mock_from_url.assert_called_once_with(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        mock_redis.ping.assert_awaited_once()

        assert client.client is mock_redis
        assert client._connected is True


    @pytest.mark.asyncio
    async def test_connect_failure(self, client, mock_redis):
        """Test Redis connection failure is handled."""
        mock_redis.ping.side_effect = Exception("Redis unavailable")

        with (
            patch("app.core.redis.settings.REDIS_ENABLED", True),
            patch(
                "app.core.redis.redis.from_url",
                return_value=mock_redis,
            ),
        ):
            await client.connect()

        assert client.client is None
        assert client._connected is False


class TestRedisDisconnect:
    """Test Redis disconnection handling."""

    @pytest.mark.asyncio
    async def test_disconnect_when_connected(
        self,
        client,
        mock_redis,
    ):
        """Test closing an active Redis connection."""
        client.client = mock_redis
        client._connected = True

        await client.disconnect()

        mock_redis.close.assert_awaited_once()
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, client):
        """Test disconnect does nothing when no client exists."""
        await client.disconnect()

        assert client.client is None
        assert client._connected is False


class TestRedisGet:
    """Test Redis get operations."""

    @pytest.mark.asyncio
    async def test_get_when_not_connected(self, client):
        """Test get returns None when disconnected."""
        result = await client.get("test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_when_client_missing(self, client):
        """Test get returns None when connected flag is set but client is missing."""
        client._connected = True

        result = await client.get("test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_success(self, client, mock_redis):
        """Test successful get operation."""
        mock_redis.get.return_value = "test-value"

        client.client = mock_redis
        client._connected = True

        result = await client.get("test-key")

        assert result == "test-value"
        mock_redis.get.assert_awaited_once_with("test-key")

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(
        self,
        client,
        mock_redis,
    ):
        """Test get returns None when key does not exist."""
        mock_redis.get.return_value = None

        client.client = mock_redis
        client._connected = True

        result = await client.get("missing-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_handles_error(self, client, mock_redis):
        """Test get handles Redis errors."""
        mock_redis.get.side_effect = Exception("Redis error")

        client.client = mock_redis
        client._connected = True

        result = await client.get("test-key")

        assert result is None


class TestRedisSet:
    """Test Redis set operations."""

    @pytest.mark.asyncio
    async def test_set_when_not_connected(self, client):
        """Test set returns False when disconnected."""
        result = await client.set("test-key", "value")

        assert result is False

    @pytest.mark.asyncio
    async def test_set_string_value(self, client, mock_redis):
        """Test setting a string value."""
        client.client = mock_redis
        client._connected = True

        result = await client.set("test-key", "test-value")

        assert result is True
        mock_redis.set.assert_awaited_once_with(
            "test-key",
            "test-value",
            ex=None,
        )

    @pytest.mark.asyncio
    async def test_set_with_expiration(self, client, mock_redis):
        """Test setting a value with expiration."""
        client.client = mock_redis
        client._connected = True

        result = await client.set(
            "test-key",
            "test-value",
            expire=300,
        )

        assert result is True
        mock_redis.set.assert_awaited_once_with(
            "test-key",
            "test-value",
            ex=300,
        )

    @pytest.mark.asyncio
    async def test_set_dict_serializes_to_json(
        self,
        client,
        mock_redis,
    ):
        """Test dictionaries are serialized before storage."""
        client.client = mock_redis
        client._connected = True

        result = await client.set(
            "test-key",
            {"symbol": "BTC", "price": 75000},
        )

        assert result is True

        mock_redis.set.assert_awaited_once_with(
            "test-key",
            '{"symbol": "BTC", "price": 75000}',
            ex=None,
        )

    @pytest.mark.asyncio
    async def test_set_list_serializes_to_json(
        self,
        client,
        mock_redis,
    ):
        """Test lists are serialized before storage."""
        client.client = mock_redis
        client._connected = True

        result = await client.set(
            "test-key",
            ["BTC", "ETH"],
        )

        assert result is True

        mock_redis.set.assert_awaited_once_with(
            "test-key",
            '["BTC", "ETH"]',
            ex=None,
        )

    @pytest.mark.asyncio
    async def test_set_handles_error(self, client, mock_redis):
        """Test set handles Redis errors."""
        mock_redis.set.side_effect = Exception("Redis error")

        client.client = mock_redis
        client._connected = True

        result = await client.set("test-key", "value")

        assert result is False


class TestRedisIncrement:
    """Test Redis increment operations."""

    @pytest.mark.asyncio
    async def test_incr_when_not_connected(self, client):
        """Test incr returns zero when disconnected."""
        result = await client.incr("counter")

        assert result == 0

    @pytest.mark.asyncio
    async def test_incr_success(self, client, mock_redis):
        """Test successful increment."""
        mock_redis.incr.return_value = 5

        client.client = mock_redis
        client._connected = True

        result = await client.incr("counter")

        assert result == 5
        mock_redis.incr.assert_awaited_once_with("counter")

    @pytest.mark.asyncio
    async def test_incr_handles_error(self, client, mock_redis):
        """Test incr handles Redis errors."""
        mock_redis.incr.side_effect = Exception("Redis error")

        client.client = mock_redis
        client._connected = True

        result = await client.incr("counter")

        assert result == 0


class TestRedisDelete:
    """Test Redis delete operations."""

    @pytest.mark.asyncio
    async def test_delete_when_not_connected(self, client):
        """Test delete returns False when disconnected."""
        result = await client.delete("test-key")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self, client, mock_redis):
        """Test successful delete."""
        client.client = mock_redis

        client._connected = True

        result = await client.delete("test-key")

        assert result is True
        mock_redis.delete.assert_awaited_once_with("test-key")

    @pytest.mark.asyncio
    async def test_delete_handles_error(self, client, mock_redis):
        """Test delete handles Redis errors."""
        mock_redis.delete.side_effect = Exception("Redis error")

        client.client = mock_redis
        client._connected = True

        result = await client.delete("test-key")

        assert result is False


class TestRedisTTL:
    """Test Redis TTL operations."""

    @pytest.mark.asyncio
    async def test_ttl_when_not_connected(self, client):
        """Test ttl returns zero when disconnected."""
        result = await client.ttl("test-key")

        assert result == 0

    @pytest.mark.asyncio
    async def test_ttl_success(self, client, mock_redis):
        """Test successful TTL lookup."""
        mock_redis.ttl.return_value = 120

        client.client = mock_redis
        client._connected = True

        result = await client.ttl("test-key")

        assert result == 120
        mock_redis.ttl.assert_awaited_once_with("test-key")

    @pytest.mark.asyncio
    async def test_ttl_handles_error(self, client, mock_redis):
        """Test ttl handles Redis errors."""
        mock_redis.ttl.side_effect = Exception("Redis error")

        client.client = mock_redis
        client._connected = True

        result = await client.ttl("test-key")

        assert result == 0

