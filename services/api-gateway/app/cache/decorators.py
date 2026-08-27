"""Cache decorators for API endpoints.

This module provides decorators for caching API responses with
configurable TTLs and cache key generation.
"""

import json
import hashlib
from functools import wraps
from typing import Optional, Callable, Any, Dict
from datetime import datetime, timezone

from app.cache.service import cache_service
from app.core.config import settings

import logging
logger = logging.getLogger(settings.SERVICE_NAME)


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    key_func: Optional[Callable] = None,
):
    """Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds. If None, uses default TTL.
        key_prefix: Prefix for the cache key.
        key_func: Function to generate cache key from args and kwargs.

    Returns:
        Callable: Decorated function with caching.

    Example:
        @cached(ttl=300, key_prefix="predictions")
        async def get_predictions(symbol: str, timeframe: str):
            return await fetch_predictions(symbol, timeframe)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, key_prefix, args, kwargs)

            # Try to get from cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                logger.info(f"Cache hit: {cache_key}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            await cache_service.set(cache_key, result, ttl=ttl)
            logger.info(f"Cache set: {cache_key} (TTL: {ttl or cache_service._default_ttl}s)")

            return result

        return wrapper
    return decorator


def cache_clear(
    key_prefix: str = "",
    pattern: Optional[str] = None,
):
    """Decorator to clear cache after function execution.

    Args:
        key_prefix: Prefix for the cache key to clear.
        pattern: Pattern for keys to clear.

    Returns:
        Callable: Decorated function that clears cache.

    Example:
        @cache_clear(key_prefix="predictions")
        async def create_prediction(data: dict):
            return await save_prediction(data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Clear cache
            if pattern:
                await cache_service.clear_pattern(pattern)
            elif key_prefix:
                await cache_service.clear_pattern(f"{key_prefix}_*")

            return result

        return wrapper
    return decorator


def cache_invalidate(
    key_prefix: str = "",
    key_func: Optional[Callable] = None,
):
    """Decorator to invalidate specific cache keys after function execution.

    Args:
        key_prefix: Prefix for the cache key to invalidate.
        key_func: Function to generate cache key from args and kwargs.

    Returns:
        Callable: Decorated function that invalidates cache.

    Example:
        @cache_invalidate(key_prefix="predictions")
        async def update_prediction(id: int, data: dict):
            return await update_prediction_data(id, data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Generate cache key to invalidate
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, key_prefix, args, kwargs)

            # Invalidate cache
            await cache_service.delete(cache_key)
            logger.info(f"Cache invalidated: {cache_key}")

            return result

        return wrapper
    return decorator


def _generate_cache_key(
    func_name: str,
    key_prefix: str,
    args: tuple,
    kwargs: dict,
) -> str:
    """Generate a cache key from function arguments.

    Args:
        func_name: Name of the function.
        key_prefix: Prefix for the cache key.
        args: Positional arguments.
        kwargs: Keyword arguments.

    Returns:
        str: The generated cache key.
    """
    # Build a string representation of the arguments
    arg_str = f"{func_name}"

    if key_prefix:
        arg_str = f"{key_prefix}_{arg_str}"

    # Add args
    if args:
        arg_str += f"_{'_'.join(str(a) for a in args)}"

    # Add kwargs (sorted for consistency)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        kw_str = "_".join(f"{k}={v}" for k, v in sorted_kwargs)
        arg_str += f"_{kw_str}"

    # Hash the key to ensure it's a valid Redis key
    # (Redis keys should be <= 512 bytes)
    if len(arg_str) > 200:
        hash_str = hashlib.md5(arg_str.encode()).hexdigest()
        if key_prefix:
            return f"{key_prefix}_{hash_str}"
        return f"{func_name}_{hash_str}"

    return arg_str