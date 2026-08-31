"""Redis client for caching and rate limiting."""

import json
import logging
from typing import Optional, Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


class RedisClient:
    """Async Redis client for the API Gateway."""

    def __init__(self):
        """Initialize Redis client."""
        self.client: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Redis."""
        if not settings.REDIS_ENABLED:
            logger.info("Redis is disabled")
            return

        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            await self.client.ping()
            self._connected = True
            logger.info(f"✅ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
            self._connected = False

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        if not self._connected or not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a value in Redis."""
        if not self._connected or not self.client:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def incr(self, key: str) -> int:
        """Increment a key in Redis."""
        if not self._connected or not self.client:
            return 0
        try:
            return await self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis incr error: {e}")
            return 0

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self._connected or not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL for a key."""
        if not self._connected or not self.client:
            return 0
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl error: {e}")
            return 0


# ============================================
# SINGLETON INSTANCE
# ============================================

redis_client = RedisClient()