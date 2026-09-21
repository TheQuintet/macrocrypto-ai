"""AI Service — Cache package.

Provides the async Redis client and the prediction cache layer
used by the HTTP API.

Public API:
    - get_redis, close_redis, ping_redis: Redis client lifecycle
    - get_cached_prediction, set_cached_prediction: prediction
      cache-aside helpers
    - invalidate_prediction_cache, invalidate_all_prediction_caches:
      invalidation helpers
    - build_cache_key: key construction (for tests and debugging)
"""

from app.cache.redis_client import (
    close_redis,
    get_redis,
    ping_redis,
)
from app.cache.prediction_cache import (
    build_cache_key,
    get_cached_prediction,
    invalidate_all_prediction_caches,
    invalidate_prediction_cache,
    set_cached_prediction,
    KEY_PREFIX,
)

__all__ = [
    "get_redis",
    "close_redis",
    "ping_redis",
    "get_cached_prediction",
    "set_cached_prediction",
    "invalidate_prediction_cache",
    "invalidate_all_prediction_caches",
    "build_cache_key",
    "KEY_PREFIX",
]