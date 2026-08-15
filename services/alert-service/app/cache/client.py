"""
Redis cache client for alert-service.
"""

import json
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis cache client with async support."""

    def __init__(self):
        self.client: Optional[Redis] = None
        self.is_enabled = settings.REDIS_ENABLED
        self.default_ttl = settings.REDIS_CACHE_TTL
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if not self.is_enabled:
            logger.info("Redis disabled")
            return False

        try:
            redis_url = settings.REDIS_CONNECTION_URL
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            await self.client.ping()
            self._connected = True
            logger.info("✅ Redis cache connected at %s", redis_url)
            return True
        except RedisError as error:
            logger.error("❌ Redis connection failed: %s", error)
            self.client = None
            self._connected = False
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            try:
                await self.client.aclose()
                self.client = None
                self._connected = False
                logger.info("Redis cache connection closed")
            except Exception as error:
                logger.error("Redis close error: %s", error)

    async def ping(self) -> bool:
        """Check Redis availability."""
        if not self.client or not self._connected:
            return False
        try:
            return await self.client.ping()
        except RedisError:
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.client or not self._connected:
            return None

        try:
            value = await self.client.get(key)
            if value is None:
                return None

            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except RedisError as error:
            logger.error("Redis GET failed %s: %s", key, error)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Store value in Redis."""
        if not self.client or not self._connected:
            return False

        try:
            serialized = json.dumps(value, default=str)
            expire = ttl if ttl is not None else self.default_ttl

            await self.client.set(
                name=key,
                value=serialized,
                ex=expire,
            )
            logger.debug("Redis SET %s TTL=%s", key, expire)
            return True
        except RedisError as error:
            logger.error("Redis SET failed %s: %s", key, error)
            return False

    async def delete(self, key: str) -> bool:
        """Delete Redis key."""
        if not self.client or not self._connected:
            return False

        try:
            await self.client.delete(key)
            return True
        except RedisError as error:
            logger.error("Redis DELETE failed %s: %s", key, error)
            return False

    async def exists(self, key: str) -> bool:
        """Check whether a Redis key exists."""
        if not self.client or not self._connected:
            return False

        try:
            return (await self.client.exists(key)) > 0
        except RedisError:
            return False

    async def get_or_set(
        self,
        key: str,
        func,
        ttl: Optional[int] = None,
    ) -> Optional[Any]:
        """Cache-aside helper."""
        cached = await self.get(key)
        if cached is not None:
            return cached

        try:
            result = await func() if callable(func) else func
            if result is not None:
                await self.set(key, result, ttl)
            return result
        except Exception as error:
            logger.error("get_or_set failed %s: %s", key, error)
            return None

    async def flush_all(self) -> bool:
        """Remove all keys from the current Redis database."""
        if not self.client or not self._connected:
            return False

        try:
            await self.client.flushall()
            return True
        except RedisError:
            return False

    @property
    def is_connected(self) -> bool:
        """Return whether Redis is currently connected."""
        return self._connected and self.client is not None

    async def health_check(self) -> Dict[str, Any]:
        """Return Redis health information."""
        if not self.is_enabled:
            return {"status": "disabled"}

        if not self.is_connected:
            return {"status": "disconnected"}

        try:
            await self.client.ping()
            info = await self.client.info()

            health = {
                "status": "healthy",
                "version": info.get("redis_version", "unknown"),
                "memory": info.get("used_memory_human", "unknown"),
            }

            if "uptime_in_seconds" in info:
                health["uptime_seconds"] = info["uptime_in_seconds"]

            return health
        except RedisError as error:
            return {
                "status": "error",
                "message": str(error),
            }


_global_client: Optional[CacheClient] = None


async def get_redis_client() -> Optional[CacheClient]:
    """Return the backward-compatible global Redis client."""
    global _global_client

    if _global_client is None:
        _global_client = CacheClient()
        await _global_client.connect()

    return _global_client


def check_redis_connection_sync() -> bool:
    """Check Redis connection from synchronous code."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()

        if loop.is_running():
            return False

        result = loop.run_until_complete(get_redis_client())

        return result.is_connected if result else False
    except Exception:
        return False