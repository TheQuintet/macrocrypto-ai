import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from redis.exceptions import RedisError

from app.cache.client import CacheClient


@pytest.fixture
def cache_client():
    client = CacheClient()
    client._connected = True
    client.client = MagicMock()
    return client


@pytest.mark.asyncio
async def test_connect_disabled():
    cache = CacheClient()
    cache.is_enabled = False

    result = await cache.connect()

    assert result is False


@pytest.mark.asyncio
async def test_connect_success():
    cache = CacheClient()
    cache.is_enabled = True

    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(return_value=True)
    cache.client = mock_redis

    result = await cache.connect()

    assert result is True


@pytest.mark.asyncio
async def test_connect_redis_error():
    cache = CacheClient()
    cache.is_enabled = True

    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(
        side_effect=RedisError("connection failed")
    )

    with patch(
        "app.cache.client.redis.from_url",
        return_value=mock_redis,
    ):
        result = await cache.connect()

    assert result is False
    assert cache.is_connected is False
    assert cache.client is None


@pytest.mark.asyncio
async def test_get_json_value(cache_client):
    cache_client.client.get = AsyncMock(
        return_value='{"price":100}'
    )

    result = await cache_client.get("btc")

    assert result == {"price": 100}


@pytest.mark.asyncio
async def test_get_raw_value(cache_client):
    cache_client.client.get = AsyncMock(
        return_value="hello"
    )

    result = await cache_client.get("key")

    assert result == "hello"


@pytest.mark.asyncio
async def test_get_missing_connection():
    cache = CacheClient()

    result = await cache.get("key")

    assert result is None


@pytest.mark.asyncio
async def test_set_dict_value(cache_client):
    # CacheClient.set() uses the async Redis set() method with ex=TTL.
    cache_client.client.set = AsyncMock(return_value=True)

    result = await cache_client.set(
        "btc",
        {"price": 100},
    )

    assert result is True
    cache_client.client.set.assert_called_once()

    call = cache_client.client.set.call_args
    assert call.kwargs["name"] == "btc"
    assert call.kwargs["value"] == '{"price": 100}'
    assert call.kwargs["ex"] == cache_client.default_ttl


@pytest.mark.asyncio
async def test_set_without_connection():
    cache = CacheClient()

    result = await cache.set("key", "value")

    assert result is False


@pytest.mark.asyncio
async def test_delete(cache_client):
    cache_client.client.delete = AsyncMock(return_value=1)

    result = await cache_client.delete("btc")

    assert result is True
    cache_client.client.delete.assert_called_once_with("btc")


@pytest.mark.asyncio
async def test_exists(cache_client):
    cache_client.client.exists = AsyncMock(return_value=1)

    result = await cache_client.exists("btc")

    assert result is True
    cache_client.client.exists.assert_called_once_with("btc")


@pytest.mark.asyncio
async def test_get_or_set_cache_hit(cache_client):
    cache_client.get = AsyncMock(
        return_value={"price": 100}
    )

    result = await cache_client.get_or_set(
        "btc",
        AsyncMock(),
    )

    assert result == {"price": 100}


@pytest.mark.asyncio
async def test_get_or_set_cache_miss(cache_client):
    cache_client.get = AsyncMock(return_value=None)
    cache_client.set = AsyncMock(return_value=True)

    result = await cache_client.get_or_set(
        "btc",
        AsyncMock(return_value={"price": 100}),
    )

    assert result == {"price": 100}
    cache_client.set.assert_called_once()


@pytest.mark.asyncio
async def test_flush_all(cache_client):
    cache_client.client.flushall = AsyncMock(return_value=True)

    result = await cache_client.flush_all()

    assert result is True
    cache_client.client.flushall.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_disabled():
    cache = CacheClient()
    cache.is_enabled = False

    result = await cache.health_check()

    assert result["status"] == "disabled"


@pytest.mark.asyncio
async def test_health_check_disconnected():
    cache = CacheClient()
    cache.is_enabled = True

    result = await cache.health_check()

    assert result["status"] == "disconnected"


@pytest.mark.asyncio
async def test_price_helpers(cache_client):
    cache_client.get = AsyncMock(return_value={})
    cache_client.set = AsyncMock(return_value=True)

    assert await cache_client.get_price("BTC") == {}

    assert await cache_client.set_price("BTC", {}) is True

    cache_client.get.assert_awaited_once_with("price:btc")
    cache_client.set.assert_awaited_once_with(
        "price:btc",
        {},
        ttl=60,
    )