"""Prediction cache — cache-aside for the predictions API.

This module implements the cache-aside pattern for the predictions
endpoint (GET /api/v1/predict/btc). It provides:
    - get_cached_prediction(): read a cached response
    - set_cached_prediction(): store a response
    - invalidate_prediction_cache(): delete a specific cached key
    - invalidate_all_prediction_caches(): delete all prediction keys

Design:
    - Best-effort: every Redis operation is wrapped in try/except.
      On failure, we log a warning and return a safe default
      (None on read, False on write/invalidate). The endpoint
      continues to work with a DB round-trip.
    - JSON serialization: cached values are the JSON-serializable
      dict form of the API response. No pickle, no Pydantic
      caching (Pydantic v2 reconstruction is fast).
    - Key scheme: predict:btc:{horizon}:{model_name}:{confidence}
      Confidence is formatted to 2 decimals for deterministic keys.

TTL:
    - Configurable via settings.redis_forecast_ttl (default 300s = 5 min)
"""

import json
import logging
from typing import Any, Dict, Optional

from app.cache.redis_client import get_redis
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
KEY_PREFIX = "predict:btc"

# SCAN batch size when iterating over keys during a full invalidation
SCAN_BATCH_SIZE = 100


# ============================================================
# KEY BUILDING
# ============================================================
def build_cache_key(
    horizon: str,
    model_name: str,
    confidence: float,
) -> str:
    """Build the cache key for a prediction request.

    Format:
        predict:btc:{horizon}:{model_name}:{confidence}

    Confidence is formatted to 2 decimals so that 0.85, 0.850,
    and 0.8500000001 all produce the same key.

    Args:
        horizon: Horizon label ('24h' or '7d').
        model_name: Model identifier ('prophet', 'xgboost', ...).
        confidence: Confidence level (0.70, 0.85, 0.95).

    Returns:
        The cache key string.
    """
    return f"{KEY_PREFIX}:{horizon}:{model_name}:{confidence:.2f}"


# ============================================================
# READ
# ============================================================
async def get_cached_prediction(
    horizon: str,
    model_name: str,
    confidence: float,
) -> Optional[Dict[str, Any]]:
    """Read a cached prediction response.

    Returns None on cache miss or on any Redis error (best-effort).

    Args:
        horizon: Horizon label ('24h' or '7d').
        model_name: Model identifier.
        confidence: Confidence level.

    Returns:
        The cached response as a dict, or None if not found / error.
    """
    key = build_cache_key(horizon, model_name, confidence)

    try:
        client = await get_redis()
        raw = await client.get(key)
    except Exception as e:
        logger.warning(f"Cache read failed for key '{key}': {e}")
        return None

    if raw is None:
        logger.debug(f"Cache MISS: {key}")
        return None

    try:
        cached = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(
            f"Cache value for '{key}' is not valid JSON: {e}. "
            f"Treating as miss."
        )
        return None

    logger.debug(f"Cache HIT: {key}")
    return cached


# ============================================================
# WRITE
# ============================================================
async def set_cached_prediction(
    horizon: str,
    model_name: str,
    confidence: float,
    payload: Dict[str, Any],
    ttl_seconds: Optional[int] = None,
) -> bool:
    """Store a prediction response in the cache.

    Best-effort: on any Redis error, log a warning and return False.
    The caller should still return the DB result.

    Args:
        horizon: Horizon label.
        model_name: Model identifier.
        confidence: Confidence level.
        payload: The response payload (JSON-serializable dict).
        ttl_seconds: Optional TTL override. If None, uses
            settings.redis_forecast_ttl.

    Returns:
        True on success, False on failure.
    """
    key = build_cache_key(horizon, model_name, confidence)
    effective_ttl = ttl_seconds or settings.redis_forecast_ttl

    try:
        serialized = json.dumps(payload, default=str)
    except (TypeError, ValueError) as e:
        logger.warning(
            f"Failed to serialize payload for key '{key}': {e}"
        )
        return False

    try:
        client = await get_redis()
        await client.set(key, serialized, ex=effective_ttl)
    except Exception as e:
        logger.warning(f"Cache write failed for key '{key}': {e}")
        return False

    logger.debug(f"Cache SET: {key} (ttl={effective_ttl}s)")
    return True


# ============================================================
# INVALIDATE
# ============================================================
async def invalidate_prediction_cache(
    horizon: str,
    model_name: str,
    confidence: float,
) -> bool:
    """Invalidate a specific prediction cache key.

    Called after a new prediction batch is saved, so the next
    request re-queries the database and refreshes the cache.

    Best-effort: on any Redis error, log a warning and return False.

    Args:
        horizon: Horizon label.
        model_name: Model identifier.
        confidence: Confidence level.

    Returns:
        True on success, False on failure.
    """
    key = build_cache_key(horizon, model_name, confidence)

    try:
        client = await get_redis()
        deleted = await client.delete(key)
    except Exception as e:
        logger.warning(f"Cache invalidate failed for key '{key}': {e}")
        return False

    logger.debug(f"Cache INVALIDATE: {key} (deleted={deleted})")
    return True


async def invalidate_all_prediction_caches() -> int:
    """Invalidate all prediction cache keys.

    Uses SCAN (not KEYS) to avoid blocking Redis on large datasets.
    Iterates in batches of SCAN_BATCH_SIZE.

    Useful when schema changes or when a broad invalidation is
    needed (e.g. after a model upgrade).

    Returns:
        Number of keys deleted, or 0 on error.
    """
    pattern = f"{KEY_PREFIX}:*"
    deleted_total = 0

    try:
        client = await get_redis()
        cursor = 0
        while True:
            cursor, keys = await client.scan(
                cursor=cursor,
                match=pattern,
                count=SCAN_BATCH_SIZE,
            )
            if keys:
                deleted = await client.delete(*keys)
                deleted_total += deleted
            if cursor == 0:
                break
    except Exception as e:
        logger.warning(f"Cache invalidate-all failed: {e}")
        return 0

    logger.info(f"Invalidated {deleted_total} prediction cache keys")
    return deleted_total