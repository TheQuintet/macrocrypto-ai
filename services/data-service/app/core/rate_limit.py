"""Rate limiting configuration for the data-service"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
import logging

from app.config import settings

# Setup logging
logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """
    Get the rate limit key for the request.

    Uses client IP address by default, but can be extended
    to use user ID or API key if authentication is added.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key string
    """
    # Default: use client IP
    return get_remote_address(request)


class CustomRateLimitExceededHandler:
    """
    Custom handler for rate limit exceeded errors.

    This provides more detailed error messages and logging.
    """

    @staticmethod
    async def handle(request: Request, exc: RateLimitExceeded) -> Response:
        """
        Handle rate limit exceeded errors.

        Args:
            request: FastAPI request object
            exc: RateLimitExceeded exception

        Returns:
            JSON response with error details
        """
        from fastapi.responses import JSONResponse

        logger.warning(
            f"Rate limit exceeded for {request.client.host} "
            f"on {request.url.path}"
        )

        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": "Rate limit exceeded. Please try again later.",
                "limit": getattr(exc, "limit", "unknown"),
                "period": getattr(exc, "period", "unknown"),
                "remaining": getattr(exc, "remaining", 0),
                "reset_after": getattr(exc, "reset_after", "unknown")
            }
        )


# Create the rate limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    headers_enabled=False,
    default_limits=[
        f"{settings.RATE_LIMIT_REQUESTS}/minute" if settings.RATE_LIMIT_ENABLED else "1000000/minute"
    ],
    enabled=settings.RATE_LIMIT_ENABLED,
)

logger.info(
    f"Rate limiter initialized: "
    f"enabled={settings.RATE_LIMIT_ENABLED}, "
    f"limit={settings.RATE_LIMIT_REQUESTS}/minute"
)


# Export for use in main.py
rate_limit_exceeded_handler = CustomRateLimitExceededHandler.handle


# ============================================
# LEGACY SUPPORT
# ============================================

# For backward compatibility with the monolith
# This allows the old import style to still work
def get_limiter():
    """Get the configured limiter instance."""
    return limiter