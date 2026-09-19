"""Shared pytest fixtures for API tests.

Patches `app.cache.redis_client.get_redis` to return an in-memory
AsyncMock, so API tests never touch a real Redis instance.

The fake client stores data in a plain dict on the mock itself,
which gives us working GET/SET/DELETE semantics for the duration
of each test.

This fixture is autouse — every test under tests/unit/test_api/
gets a working fake Redis by default, and individual tests can
override behavior if needed.
"""

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest


# ============================================================
# FAKE REDIS CLIENT
# ============================================================
class FakeRedis:
    """A minimal in-memory fake of the redis.asyncio.Redis client.

    Supports the subset of commands used by the AI Service:
        - get(key)
        - set(key, value, ex=...)
        - delete(*keys)
        - scan(cursor, match=..., count=...)
        - ping()
        - aclose()
    """

    def __init__(self) -> None:
        """Initialize the fake store and call counters."""
        self._store: Dict[str, str] = {}
        self.get_calls: int = 0
        self.set_calls: int = 0
        self.delete_calls: int = 0
        self.ping_calls: int = 0

    async def get(self, key: str) -> Optional[str]:
        """Return the stored value for a key, or None."""
        self.get_calls += 1
        return self._store.get(key)

    async def set(
        self, key: str, value: str, ex: Optional[int] = None
    ) -> bool:
        """Store a value (ignores TTL for simplicity)."""
        self.set_calls += 1
        self._store[key] = value
        return True

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys; return the count deleted."""
        self.delete_calls += 1
        deleted = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                deleted += 1
        return deleted

    async def scan(
        self,
        cursor: int = 0,
        match: Optional[str] = None,
        count: int = 100,
    ):
        """Return all keys matching `match` in a single pass.

        Simplified: ignores `count` and returns cursor=0 on the
        first call, so callers see all keys in one iteration.
        """
        import fnmatch

        if match is None:
            keys = list(self._store.keys())
        else:
            keys = [
                k for k in self._store.keys() if fnmatch.fnmatch(k, match)
            ]
        return (0, keys)

    async def ping(self) -> bool:
        """Return True (simulates a healthy server)."""
        self.ping_calls += 1
        return True

    async def aclose(self) -> None:
        """Close the client (no-op for the fake)."""
        self._store.clear()


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(autouse=True)
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    """Replace the real Redis client with an in-memory fake.

    Autouse: every test in tests/unit/test_api/ gets this fixture.
    Patches `app.cache.redis_client.get_redis` so any import path
    (e.g. via `app.cache.prediction_cache`) resolves to the fake.

    Returns:
        The FakeRedis instance (for tests that want to inspect it).
    """
    fake = FakeRedis()

    async def _fake_get_redis():
        return fake

    # Patch the source (redis_client) so all importers get the fake
    monkeypatch.setattr(
        "app.cache.redis_client.get_redis", _fake_get_redis
    )
    # Also patch the re-exported name in prediction_cache, because
    # it does `from app.cache.redis_client import get_redis` — the
    # name is bound at import time.
    monkeypatch.setattr(
        "app.cache.prediction_cache.get_redis", _fake_get_redis
    )

    return fake