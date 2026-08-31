"""Rate limiting middleware for API Gateway.

This module provides rate limiting functionality using Redis as the backend store.
It implements tiered rate limits based on user roles (guest, user, admin) and
includes proper rate limit headers in responses.
"""

import time
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(settings.SERVICE_NAME)


# ============================================
# RATE LIMIT CONFIGURATION
# ============================================

RATE_LIMITS = {
    "guest": {
        "requests": settings.RATE_LIMIT_GUEST,
        "period": 60,  # 1 minute
    },
    "user": {
        "requests": settings.RATE_LIMIT_USER,
        "period": 60,  # 1 minute
    },
    "admin": {
        "requests": settings.RATE_LIMIT_ADMIN,
        "period": 60,  # 1 minute
    },
}


# ============================================
# RATE LIMITER CLASS
# ============================================

class RateLimiter:
    """Rate limiter using Redis for storage.

    Implements a sliding window counter algorithm for accurate rate limiting.
    """

    def __init__(self):
        """Initialize the rate limiter."""
        self.redis = redis_client
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.default_requests = settings.RATE_LIMIT_REQUESTS
        self.default_period = settings.RATE_LIMIT_PERIOD

    def _get_rate_limit_config(self, role: str) -> Tuple[int, int]:
        """Get rate limit configuration for a given role.

        Args:
            role: User role (guest, user, admin).

        Returns:
            Tuple[int, int]: (max_requests, period_in_seconds).
        """
        if role in RATE_LIMITS:
            return RATE_LIMITS[role]["requests"], RATE_LIMITS[role]["period"]
        return RATE_LIMITS["guest"]["requests"], RATE_LIMITS["guest"]["period"]

    def _get_identifier(self, request: Request) -> str:
        """Get a unique identifier for the client.

        Priority:
        1. Authenticated user ID (from token)
        2. API Key (from header)
        3. Client IP address

        Args:
            request: The FastAPI request object.

        Returns:
            str: Unique client identifier.
        """
        # Check for authenticated user
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key[:8]}"

        # Fallback to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _get_role(self, request: Request) -> str:
        """Get the user role from the request state.

        Args:
            request: The FastAPI request object.

        Returns:
            str: User role (guest, user, admin).
        """
        # Check if user is authenticated
        user = getattr(request.state, "current_user", None)
        if user:
            if hasattr(user, "role"):
                if user.role == "admin":
                    return "admin"
                return "user"
            return "user"

        # Check for API key role
        api_key = getattr(request.state, "api_key", None)
        if api_key:
            return "user"

        return "guest"

    async def check_rate_limit(self, request: Request) -> Tuple[bool, int, int, int]:
        """Check if the request is within rate limits.

        Args:
            request: The FastAPI request object.

        Returns:
            Tuple[bool, int, int, int]: (is_allowed, max_requests, remaining, reset_time).
        """
        if not self.enabled:
            return True, 0, 0, 0

        # Get client identifier and role
        identifier = self._get_identifier(request)
        role = self._get_role(request)
        max_requests, period = self._get_rate_limit_config(role)

        # Build Redis key
        redis_key = f"rate_limit:{identifier}"

        # Get current count
        current = await self.redis.get(redis_key)

        if current is None:
            # First request - set the counter
            await self.redis.set(redis_key, 1, expire=period)
            remaining = max_requests - 1
            reset_time = int(time.time()) + period
            return True, max_requests, remaining, reset_time

        # Get TTL
        ttl = await self.redis.ttl(redis_key)

        # Check if limit is exceeded
        count = int(current) if current else 0
        if count >= max_requests:
            return False, max_requests, 0, int(time.time()) + ttl

        # Increment counter
        await self.redis.incr(redis_key)
        remaining = max_requests - (count + 1)
        reset_time = int(time.time()) + ttl

        return True, max_requests, remaining, reset_time

    async def reset_rate_limit(self, request: Request) -> None:
        """Reset the rate limit for a client.

        Args:
            request: The FastAPI request object.
        """
        if not self.enabled:
            return

        identifier = self._get_identifier(request)
        redis_key = f"rate_limit:{identifier}"
        await self.redis.delete(redis_key)


# ============================================
# RATE LIMIT MIDDLEWARE
# ============================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting.

    Intercepts all requests, applies rate limiting, and adds rate limit headers.
    """

    def __init__(self, app: ASGIApp):
        """Initialize the middleware."""
        super().__init__(app)
        self.limiter = RateLimiter()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request through rate limiting.

        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint.

        Returns:
            Response: The response with rate limit headers.
        """
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/ready", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Check rate limit
        is_allowed, max_requests, remaining, reset_time = await self.limiter.check_rate_limit(request)

        # Create response
        if is_allowed:
            response = await call_next(request)
        else:
            # Rate limit exceeded
            response = Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        if not is_allowed:
            response.headers["Retry-After"] = str(reset_time - int(time.time()))

        return response


# ============================================
# RATE LIMIT DEPENDENCY
# ============================================

class RateLimitInfo:
    """Rate limit information for the current request."""

    def __init__(self, request: Request):
        """Initialize rate limit info from request."""
        self.request = request
        self.limit = int(request.headers.get("X-RateLimit-Limit", 0))
        self.remaining = int(request.headers.get("X-RateLimit-Remaining", 0))
        self.reset = int(request.headers.get("X-RateLimit-Reset", 0))

    @property
    def reset_datetime(self) -> datetime:
        """Get the reset time as a datetime object."""
        return datetime.fromtimestamp(self.reset)

    @property
    def is_limited(self) -> bool:
        """Check if rate limit is being enforced."""
        return self.remaining <= 0


# ============================================
# RATE LIMIT EXCEPTION HANDLER
# ============================================

def rate_limit_exceeded_handler(request: Request, exc: HTTPException) -> Response:
    """Custom handler for rate limit exceeded errors."""
    return Response(
        content='{"detail":"Rate limit exceeded. Please try again later."}',
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        media_type="application/json",
        headers={
            "X-RateLimit-Limit": str(request.headers.get("X-RateLimit-Limit", 0)),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": request.headers.get("X-RateLimit-Reset", ""),
        },
    )


# ============================================
# SINGLETON INSTANCE
# ============================================

rate_limiter = RateLimiter()