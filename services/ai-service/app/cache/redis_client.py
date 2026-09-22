"""Async Redis client for the AI Service.

This module provides a lazily-initialized async Redis client and
lifecycle helpers. The client is process-global (one pool per
process) and is disposed gracefully on shutdown.

Design:
    - Lazy creation on first use so importing this module does not
      require a live Redis server
    - Single connection pool shared by all callers
    - Graceful shutdown via close_redis()
    - Exposes get_redis() which raises if the client cannot connect

Usage:
    from app.cache.redis_client import get_redis

    redis = await get_redis()
    await redis.set("key", "value", ex=300)
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# MODULE STATE
# ============================================================
_redis: Optional[aioredis.Redis] = None


# ============================================================
# CLIENT LIFECYCLE
# ============================================================
async def get_redis() -> aioredis.Redis:
    """Return the global async Redis client, creating it on first call.

    The client is backed by a connection pool and is safe to share
    across coroutines. It does not eagerly connect — the first
    command triggers the connection.

    Returns:
        An aioredis.Redis instance.

    Raises:
        redis.exceptions.RedisError: If the connection cannot be
            established (propagated from the first command).
    """
    global _redis

    if _redis is None:
        logger.info(
            f"Creating async Redis client "
            f"(host={settings.redis_host}, port={settings.redis_port}, "
            f"db={settings.redis_db})"
        )
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

    return _redis


async def close_redis() -> None:
    """Close the global Redis client and reset module state.

    Called during application shutdown. Safe to call multiple times;
    subsequent calls to get_redis() will create a fresh client.
    """
    global _redis

    if _redis is not None:
        logger.info("Closing async Redis client")
        try:
            await _redis.aclose()
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")
        finally:
            _redis = None


async def ping_redis() -> bool:
    """Ping Redis to verify connectivity.

    Useful for health checks and startup validation.

    Returns:
        True if Redis responds to PING, False otherwise.
    """
    try:
        client = await get_redis()
        result = await client.ping()
        return bool(result)
    except Exception as e:
        logger.warning(f"Redis ping failed: {e}")
        return False