"""Cache service for managing Redis caching operations.

This module provides a service layer for Redis caching operations
with support for different TTLs per cache key prefix.
"""

import json
import logging
from typing import Optional, Any, Dict, Callable
from datetime import datetime, timedelta

from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


# ============================================
# CACHE TTL CONFIGURATION
# ============================================

class CacheTTL:
    """Cache TTL constants for different endpoint types."""

    PREDICTIONS = 300  # 5 minutes
    PRICES = 300  # 5 minutes
    INDICATORS = 3600  # 1 hour
    CORRELATION = 3600  # 1 hour
    REGIMES = 3600  # 1 hour
    RECOMMENDATIONS = 3600  # 1 hour
    ACCURACY = 600  # 10 minutes
    DEFAULT = 300  # 5 minutes


# ============================================
# CACHE SERVICE
# ============================================

class CacheService:
    """Service for managing Redis cache operations.

    Provides methods for getting, setting, and invalidating cache entries
    with support for JSON serialization and TTL configuration.
    """

    def __init__(self):
        """Initialize the cache service."""
        self.redis = redis_client
        self.enabled = settings.REDIS_ENABLED
        self._default_ttl = CacheTTL.DEFAULT

    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key.

        Args:
            key: The cache key.

        Returns:
            Optional[Any]: The cached value, or None if not found.
        """
        if not self.enabled:
            return None

        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Cache hit: {key}")
                return json.loads(data)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a cached value with TTL.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time-to-live in seconds.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.enabled:
            return False

        try:
            ttl = ttl or self._default_ttl
            data = json.dumps(value, default=self._json_serializer)
            result = await self.redis.set(key, data, expire=ttl)
            if result:
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return result
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached value by key.

        Args:
            key: The cache key.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.enabled:
            return False

        try:
            result = await self.redis.delete(key)
            if result:
                logger.debug(f"Cache deleted: {key}")
            return result
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all cache keys matching a pattern.

        Args:
            pattern: The pattern to match (e.g., "predictions_*").

        Returns:
            int: Number of keys deleted.
        """
        if not self.enabled:
            return 0

        try:
            # Get all matching keys using scan for better performance
            keys = []
            cursor = 0
            # Check if redis client is connected
            if self.redis.client is None:
                logger.warning("Redis client is not connected")
                return 0

            while True:
                cursor, batch = await self.redis.client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(batch)
                if cursor == 0:
                    break

            if not keys:
                return 0

            # Delete each key
            deleted = 0
            for key in keys:
                if await self.redis.delete(key):
                    deleted += 1

            logger.info(f"Cache cleared: {deleted} keys matching pattern '{pattern}'")
            return deleted
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a cache key exists.

        Args:
            key: The cache key.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        if not self.enabled:
            return False

        try:
            value = await self.redis.get(key)
            return value is not None
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get the remaining TTL for a cache key.

        Args:
            key: The cache key.

        Returns:
            int: Remaining TTL in seconds, or -1 if no expiry, -2 if key doesn't exist.
        """
        if not self.enabled:
            return -2

        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-serializable objects.

        Args:
            obj: The object to serialize.

        Returns:
            Any: The serialized object.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    # ============================================
    # CONVENIENCE METHODS FOR SPECIFIC ENDPOINTS
    # ============================================

    async def get_predictions(self, symbol: str, timeframe: str, model_type: str) -> Optional[Any]:
        """Get cached predictions."""
        key = f"predictions_{symbol}_{timeframe}_{model_type}"
        return await self.get(key)

    async def set_predictions(
        self,
        symbol: str,
        timeframe: str,
        model_type: str,
        value: Any,
    ) -> bool:
        """Cache predictions."""
        key = f"predictions_{symbol}_{timeframe}_{model_type}"
        return await self.set(key, value, ttl=CacheTTL.PREDICTIONS)

    async def get_prices(self, symbol: str, start_date: str, end_date: str, limit: int, offset: int) -> Optional[Any]:
        """Get cached prices."""
        key = f"prices_{symbol}_{start_date}_{end_date}_{limit}_{offset}"
        return await self.get(key)

    async def set_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        limit: int,
        offset: int,
        value: Any,
    ) -> bool:
        """Cache prices."""
        key = f"prices_{symbol}_{start_date}_{end_date}_{limit}_{offset}"
        return await self.set(key, value, ttl=CacheTTL.PRICES)

    async def get_indicators(self, indicators: str) -> Optional[Any]:
        """Get cached indicators."""
        key = f"indicators_{indicators or 'all'}"
        return await self.get(key)

    async def set_indicators(self, indicators: str, value: Any) -> bool:
        """Cache indicators."""
        key = f"indicators_{indicators or 'all'}"
        return await self.set(key, value, ttl=CacheTTL.INDICATORS)

    async def get_correlation(self, symbol: str, window: str) -> Optional[Any]:
        """Get cached correlation."""
        key = f"correlation_{symbol}_{window}"
        return await self.get(key)

    async def set_correlation(self, symbol: str, window: str, value: Any) -> bool:
        """Cache correlation."""
        key = f"correlation_{symbol}_{window}"
        return await self.set(key, value, ttl=CacheTTL.CORRELATION)

    async def get_regimes(self, symbol: str, timeframe: str) -> Optional[Any]:
        """Get cached regimes."""
        key = f"regimes_{symbol}_{timeframe}"
        return await self.get(key)

    async def set_regimes(self, symbol: str, timeframe: str, value: Any) -> bool:
        """Cache regimes."""
        key = f"regimes_{symbol}_{timeframe}"
        return await self.set(key, value, ttl=CacheTTL.REGIMES)

    async def get_recommendations(self, timeframe: str, risk_level: str) -> Optional[Any]:
        """Get cached recommendations."""
        key = f"recommendations_btc_{timeframe}_{risk_level}"
        return await self.get(key)

    async def set_recommendations(self, timeframe: str, risk_level: str, value: Any) -> bool:
        """Cache recommendations."""
        key = f"recommendations_btc_{timeframe}_{risk_level}"
        return await self.set(key, value, ttl=CacheTTL.RECOMMENDATIONS)

    async def get_accuracy(self, symbol: str, days: int) -> Optional[Any]:
        """Get cached accuracy metrics."""
        key = f"accuracy_{symbol}_{days}"
        return await self.get(key)

    async def set_accuracy(self, symbol: str, days: int, value: Any) -> bool:
        """Cache accuracy metrics."""
        key = f"accuracy_{symbol}_{days}"
        return await self.set(key, value, ttl=CacheTTL.ACCURACY)


# ============================================
# SINGLETON INSTANCE
# ============================================

cache_service = CacheService()