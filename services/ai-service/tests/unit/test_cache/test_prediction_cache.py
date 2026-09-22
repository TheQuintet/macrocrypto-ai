"""Unit tests for the prediction cache module.

These tests use a FakeRedis instance and monkeypatch the
`get_redis` function referenced by `app.cache.prediction_cache`,
so no live Redis is required.

Test organization:
    - TestBuildCacheKey: key construction
    - TestGetCachedPrediction: cache reads (hit, miss, error)
    - TestSetCachedPrediction: cache writes (success, error, serialization)
    - TestInvalidatePredictionCache: single-key invalidation
    - TestInvalidateAllPredictionCaches: SCAN-based bulk invalidation
    - TestCacheConstants: module constants
"""

import json
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock

import pytest

from app.cache import prediction_cache as cache_module
from app.cache.prediction_cache import (
    KEY_PREFIX,
    SCAN_BATCH_SIZE,
    build_cache_key,
    get_cached_prediction,
    invalidate_all_prediction_caches,
    invalidate_prediction_cache,
    set_cached_prediction,
)


# ============================================================
# FAKE REDIS
# ============================================================
class FakeRedis:
    """Minimal in-memory fake matching the commands we use."""

    def __init__(self) -> None:
        self.store: Dict[str, str] = {}
        self.raise_on_get: Optional[Exception] = None
        self.raise_on_set: Optional[Exception] = None
        self.raise_on_delete: Optional[Exception] = None
        self.raise_on_scan: Optional[Exception] = None

    async def get(self, key: str) -> Optional[str]:
        if self.raise_on_get:
            raise self.raise_on_get
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self.raise_on_set:
            raise self.raise_on_set
        self.store[key] = value
        return True

    async def delete(self, *keys: str) -> int:
        if self.raise_on_delete:
            raise self.raise_on_delete
        deleted = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                deleted += 1
        return deleted

    async def scan(
        self,
        cursor: int = 0,
        match: Optional[str] = None,
        count: int = 100,
    ):
        if self.raise_on_scan:
            raise self.raise_on_scan
        import fnmatch

        keys = (
            [k for k in self.store if fnmatch.fnmatch(k, match)]
            if match
            else list(self.store.keys())
        )
        return (0, keys)


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    """Patch the cache module's get_redis to return a fake."""
    fake = FakeRedis()

    async def _get_redis():
        return fake

    monkeypatch.setattr(cache_module, "get_redis", _get_redis)
    return fake


# ============================================================
# KEY BUILDING
# ============================================================
class TestBuildCacheKey:
    """Tests for build_cache_key()."""

    def test_basic_key(self) -> None:
        """Test the key format for a typical input."""
        key = build_cache_key("24h", "prophet", 0.85)
        assert key == "predict:btc:24h:prophet:0.85"

    def test_7d_key(self) -> None:
        """Test a 7d horizon key."""
        key = build_cache_key("7d", "xgboost", 0.95)
        assert key == "predict:btc:7d:xgboost:0.95"

    def test_confidence_normalized_to_2_decimals(self) -> None:
        """Test that confidence is formatted to 2 decimals."""
        assert build_cache_key("24h", "prophet", 0.8) == (
            "predict:btc:24h:prophet:0.80"
        )
        assert build_cache_key("24h", "prophet", 0.850) == (
            "predict:btc:24h:prophet:0.85"
        )

    def test_key_starts_with_prefix(self) -> None:
        """Test that every key starts with the module prefix."""
        key = build_cache_key("24h", "prophet", 0.85)
        assert key.startswith(KEY_PREFIX + ":")


# ============================================================
# GET
# ============================================================
class TestGetCachedPrediction:
    """Tests for get_cached_prediction()."""

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, fake_redis) -> None:
        """Test that a missing key returns None."""
        result = await get_cached_prediction("24h", "prophet", 0.85)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_returns_dict(self, fake_redis) -> None:
        """Test that a stored value is deserialized and returned."""
        key = build_cache_key("24h", "prophet", 0.85)
        payload = {"horizon": "24h", "current_price": 63_000.0}
        fake_redis.store[key] = json.dumps(payload)

        result = await get_cached_prediction("24h", "prophet", 0.85)
        assert result == payload

    @pytest.mark.asyncio
    async def test_invalid_json_returns_none(self, fake_redis) -> None:
        """Test that corrupt JSON is treated as a miss."""
        key = build_cache_key("24h", "prophet", 0.85)
        fake_redis.store[key] = "not valid json {"

        result = await get_cached_prediction("24h", "prophet", 0.85)
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_error_returns_none(self, fake_redis) -> None:
        """Test that a Redis error is swallowed and returns None."""
        fake_redis.raise_on_get = ConnectionError("redis down")

        result = await get_cached_prediction("24h", "prophet", 0.85)
        assert result is None


# ============================================================
# SET
# ============================================================
class TestSetCachedPrediction:
    """Tests for set_cached_prediction()."""

    @pytest.mark.asyncio
    async def test_set_stores_serialized_payload(self, fake_redis) -> None:
        """Test that a payload is JSON-serialized and stored."""
        payload = {"horizon": "24h", "current_price": 63_000.0}
        ok = await set_cached_prediction("24h", "prophet", 0.85, payload)
        assert ok is True

        key = build_cache_key("24h", "prophet", 0.85)
        assert key in fake_redis.store
        assert json.loads(fake_redis.store[key]) == payload

    @pytest.mark.asyncio
    async def test_redis_error_returns_false(self, fake_redis) -> None:
        """Test that a Redis error is swallowed and returns False."""
        fake_redis.raise_on_set = ConnectionError("redis down")
        ok = await set_cached_prediction(
            "24h", "prophet", 0.85, {"x": 1}
        )
        assert ok is False

    @pytest.mark.asyncio
    async def test_unserializable_payload_returns_false(
        self, fake_redis
    ) -> None:
        """Test that a payload that cannot be serialized returns False.

        Note: `json.dumps(..., default=str)` handles most non-JSON
        types by calling str() on them. The only thing it cannot
        handle is a circular reference, which raises ValueError.
        """
        payload: Dict[str, Any] = {}
        payload["self"] = payload  # circular reference → ValueError
        ok = await set_cached_prediction("24h", "prophet", 0.85, payload)
        assert ok is False


# ============================================================
# INVALIDATE — SINGLE
# ============================================================
class TestInvalidatePredictionCache:
    """Tests for invalidate_prediction_cache()."""

    @pytest.mark.asyncio
    async def test_deletes_existing_key(self, fake_redis) -> None:
        """Test that an existing key is deleted."""
        key = build_cache_key("24h", "prophet", 0.85)
        fake_redis.store[key] = "x"

        ok = await invalidate_prediction_cache("24h", "prophet", 0.85)
        assert ok is True
        assert key not in fake_redis.store

    @pytest.mark.asyncio
    async def test_missing_key_is_still_success(self, fake_redis) -> None:
        """Test that invalidating a missing key still returns True."""
        ok = await invalidate_prediction_cache("24h", "prophet", 0.85)
        assert ok is True

    @pytest.mark.asyncio
    async def test_redis_error_returns_false(self, fake_redis) -> None:
        """Test that a Redis error is swallowed and returns False."""
        fake_redis.raise_on_delete = ConnectionError("redis down")
        ok = await invalidate_prediction_cache("24h", "prophet", 0.85)
        assert ok is False


# ============================================================
# INVALIDATE — ALL
# ============================================================
class TestInvalidateAllPredictionCaches:
    """Tests for invalidate_all_prediction_caches()."""

    @pytest.mark.asyncio
    async def test_deletes_all_matching_keys(self, fake_redis) -> None:
        """Test that all predict:* keys are deleted."""
        fake_redis.store["predict:btc:24h:prophet:0.85"] = "a"
        fake_redis.store["predict:btc:24h:prophet:0.95"] = "b"
        fake_redis.store["predict:btc:7d:xgboost:0.85"] = "c"
        fake_redis.store["unrelated:key"] = "d"

        deleted = await invalidate_all_prediction_caches()
        assert deleted == 3
        assert "predict:btc:24h:prophet:0.85" not in fake_redis.store
        assert "predict:btc:24h:prophet:0.95" not in fake_redis.store
        assert "predict:btc:7d:xgboost:0.85" not in fake_redis.store
        # Unrelated keys are untouched
        assert "unrelated:key" in fake_redis.store

    @pytest.mark.asyncio
    async def test_empty_store_returns_zero(self, fake_redis) -> None:
        """Test that an empty store returns 0."""
        deleted = await invalidate_all_prediction_caches()
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_redis_error_returns_zero(self, fake_redis) -> None:
        """Test that a Redis error is swallowed and returns 0."""
        fake_redis.raise_on_scan = ConnectionError("redis down")
        deleted = await invalidate_all_prediction_caches()
        assert deleted == 0


# ============================================================
# CONSTANTS
# ============================================================
class TestCacheConstants:
    """Tests for module-level constants."""

    def test_key_prefix(self) -> None:
        """Test that KEY_PREFIX is 'predict:btc'."""
        assert KEY_PREFIX == "predict:btc"

    def test_scan_batch_size(self) -> None:
        """Test that SCAN_BATCH_SIZE is positive."""
        assert SCAN_BATCH_SIZE > 0