"""Redis cache client for data-service"""

import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

# Setup logging
logger = logging.getLogger(__name__)


class CacheClient:
    """
    Redis cache client with async support.

    Features:
    - Async/await support
    - Automatic connection management
    - TTL support
    - JSON serialization
    - Graceful degradation when Redis is disabled
    - Health check support
    """

    def __init__(self):
        """Initialize the cache client."""
        self.client: Optional[Redis] = None
        self.is_enabled = settings.REDIS_ENABLED
        self.default_ttl = settings.REDIS_CACHE_TTL
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish connection to Redis.

        Returns:
            True if connected successfully, False otherwise.
        """
        if not self.is_enabled:
            logger.info("Redis is disabled (REDIS_ENABLED=false)")
            return False

        try:
            # Build connection URL from settings
            redis_url = settings.REDIS_CONNECTION_URL

            # Create Redis client
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            await self.client.ping()
            self._connected = True
            logger.info(f"✅ Redis cache connected at {redis_url}")
            return True

        except RedisError as error:
            logger.error(f"❌ Redis connection failed: {error}")
            logger.warning("⚠️  Running without Redis cache")
            self._connected = False
            self.client = None
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client and self._connected:
            try:
                await self.client.close()
                self._connected = False
                logger.info("✅ Redis cache connection closed")
            except Exception as error:
                logger.error(f"Error closing Redis connection: {error}")

    async def ping(self) -> bool:
        """
        Check Redis availability.

        Returns:
            True if Redis is available, False otherwise.
        """
        if not self._connected or not self.client:
            return False

        try:
            return await self.client.ping()
        except RedisError:
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._connected or not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value is None:
                return None

            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return raw value if not JSON
                return value

        except RedisError as error:
            logger.error(f"Error getting cache key '{key}': {error}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)

        Returns:
            True if set successfully, False otherwise.
        """
        if not self._connected or not self.client:
            return False

        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value, default=str)
            else:
                serialized = str(value)

            # Use provided TTL or default
            ttl = ttl or self.default_ttl

            await self.client.setex(key, ttl, serialized)
            logger.debug(f"✅ Cached key: {key} (TTL: {ttl}s)")
            return True

        except RedisError as error:
            logger.error(f"Error setting cache key '{key}': {error}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not self._connected or not self.client:
            return False

        try:
            await self.client.delete(key)
            logger.debug(f"🗑️  Deleted cache key: {key}")
            return True

        except RedisError as error:
            logger.error(f"Error deleting cache key '{key}': {error}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise.
        """
        if not self._connected or not self.client:
            return False

        try:
            return await self.client.exists(key) > 0
        except RedisError as error:
            logger.error(f"Error checking cache key '{key}': {error}")
            return False

    async def get_or_set(
        self,
        key: str,
        func,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get from cache or execute function and cache result.

        This is a convenience method for the "cache-aside" pattern.

        Args:
            key: Cache key
            func: Async function to execute if cache miss
            ttl: Time to live in seconds

        Returns:
            Cached or computed value, or None if failed.
        """
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"📦 Cache hit: {key}")
            return cached

        # Cache miss - execute function
        logger.debug(f"🔄 Cache miss: {key}, executing function")
        try:
            result = await func() if callable(func) else func
            if result is not None:
                await self.set(key, result, ttl)
            return result
        except Exception as error:
            logger.error(f"Error executing function for key '{key}': {error}")
            return None

    async def flush_all(self) -> bool:
        """
        Flush all cache (use with caution!).

        Returns:
            True if flushed successfully, False otherwise.
        """
        if not self._connected or not self.client:
            return False

        try:
            await self.client.flushall()
            logger.warning("🗑️  Flushed ALL Redis cache!")
            return True
        except RedisError as error:
            logger.error(f"Error flushing cache: {error}")
            return False

    # ============================================
    # CONVENIENCE METHODS FOR SPECIFIC DATA TYPES
    # ============================================

    async def get_price(self, symbol: str) -> Optional[Dict]:
        """Get cached price data for a symbol."""
        key = f"price:{symbol.lower()}"
        return await self.get(key)

    async def set_price(self, symbol: str, price_data: Dict) -> bool:
        """Cache price data (1 minute TTL)."""
        key = f"price:{symbol.lower()}"
        return await self.set(key, price_data, ttl=60)

    async def get_economic(self, indicator: str) -> Optional[Dict]:
        """Get cached economic indicator."""
        key = f"economic:{indicator.lower()}"
        return await self.get(key)

    async def set_economic(self, indicator: str, data: Dict) -> bool:
        """Cache economic data (1 hour TTL)."""
        key = f"economic:{indicator.lower()}"
        return await self.set(key, data, ttl=3600)

    async def get_forecast(self, symbol: str) -> Optional[Dict]:
        """Get cached forecast data."""
        key = f"forecast:{symbol.lower()}"
        return await self.get(key)

    async def set_forecast(self, symbol: str, forecast_data: Dict) -> bool:
        """Cache forecast data (30 minutes TTL)."""
        key = f"forecast:{symbol.lower()}"
        return await self.set(key, forecast_data, ttl=1800)

    async def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Get cached alert data."""
        key = f"alert:{alert_id}"
        return await self.get(key)

    async def set_alert(self, alert_id: str, alert_data: Dict) -> bool:
        """Cache alert data (5 minutes TTL)."""
        key = f"alert:{alert_id}"
        return await self.set(key, alert_data, ttl=300)

    # ============================================
    # STATUS AND HEALTH
    # ============================================

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected and self.client is not None

    async def health_check(self) -> Dict[str, Any]:
        """
        Get Redis health status.

        Returns:
            Dictionary with status information.
        """
        if not self.is_enabled:
            return {"status": "disabled", "message": "Redis is disabled"}

        if not self._connected:
            return {"status": "disconnected", "message": "Redis not connected"}

        try:
            await self.client.ping()
            info = await self.client.info()
            return {
                "status": "healthy",
                "version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown")
            }
        except RedisError as error:
            return {
                "status": "error",
                "message": str(error)
            }


# ============================================
# LEGACY SUPPORT FUNCTIONS
# ============================================

# Global client instance (for backward compatibility)
_global_client: Optional[CacheClient] = None


async def get_redis_client() -> Optional[CacheClient]:
    """
    Get the global Redis client instance.

    This is a convenience function for backward compatibility
    with the monolith style.
    """
    global _global_client

    if _global_client is None:
        _global_client = CacheClient()
        await _global_client.connect()

    return _global_client


def check_redis_connection_sync() -> bool:
    """
    Synchronous Redis connection check (for health checks).

    This is kept for backward compatibility with the monolith.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Can't run async in a running loop
            return False
        result = loop.run_until_complete(
            get_redis_client()
        )
        return result.is_connected if result else False
    except Exception:
        return False