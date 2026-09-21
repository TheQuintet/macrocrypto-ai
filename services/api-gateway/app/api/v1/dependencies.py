"""API dependencies for route protection and resource injection.

This module provides reusable dependencies for FastAPI routes:
- Authentication dependencies
- Database session management
- Rate limiting checks
- Permission validation
- Pagination parameters
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user, get_current_active_user, get_current_admin_user
from app.core.database import get_db
from app.models.user import User

# ============================================
# AUTHENTICATION DEPENDENCIES
# ============================================

# HTTP Bearer security scheme
security = HTTPBearer(
    auto_error=False,  # Allow optional authentication for some endpoints
    description="Enter your JWT token in the format: Bearer <token>"
)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Require authentication and return the token.

    This is a lightweight dependency that only validates the token format.
    Use get_current_user() for full user validation.

    Args:
        credentials: The HTTP Authorization credentials.

    Returns:
        str: The JWT token.

    Raises:
        HTTPException: If the Authorization header is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Optionally authenticate and return the token if present.

    Use this for endpoints that work with or without authentication.

    Args:
        credentials: The HTTP Authorization credentials (optional).

    Returns:
        Optional[str]: The JWT token if present, otherwise None.
    """
    if credentials is None:
        return None
    return credentials.credentials


# ============================================
# PERMISSION DEPENDENCIES
# ============================================

def require_permission(permission: str):
    """
    Factory for creating permission-based dependencies.

    Args:
        permission: The required permission (e.g., "read:btc", "write:alerts").

    Returns:
        Callable: A dependency that checks the user has the required permission.
    """
    async def check_permission(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """
        Check if the current user has the required permission.

        Args:
            current_user: The authenticated user.

        Returns:
            User: The authenticated user if they have permission.

        Raises:
            HTTPException: If the user lacks the required permission.
        """
        # Admin users have all permissions
        if current_user.role == "admin":
            return current_user

        # Check specific permission (for API keys or custom permissions)
        # This is a placeholder - implement actual permission checking
        # based on your permission system
        user_permissions = getattr(current_user, "permissions", [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )

        return current_user

    return check_permission


# ============================================
# PAGINATION DEPENDENCIES
# ============================================

class PaginationParams:
    """Pagination parameters for list endpoints."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
        order_by: Optional[str] = Query(None, description="Field to order by (e.g., 'created_at' or '-created_at' for descending)"),
    ):
        self.skip = skip
        self.limit = limit
        self.order_by = order_by

    def apply(self, query):
        """
        Apply pagination to a SQLAlchemy query.

        Args:
            query: The SQLAlchemy query object.

        Returns:
            Query: The paginated query.
        """
        if self.order_by:
            # Handle descending order (prefix with '-')
            if self.order_by.startswith('-'):
                field = self.order_by[1:]
                query = query.order_by(getattr(query.column_descriptions[0]['entity'], field).desc())
            else:
                query = query.order_by(getattr(query.column_descriptions[0]['entity'], self.order_by))

        return query.offset(self.skip).limit(self.limit)


# ============================================
# DATE RANGE DEPENDENCIES
# ============================================

class DateRangeParams:
    """Date range parameters for filtering endpoints."""

    def __init__(
        self,
        start_date: Optional[str] = Query(None, description="Start date (ISO 8601, e.g., '2024-01-01')"),
        end_date: Optional[str] = Query(None, description="End date (ISO 8601, e.g., '2024-12-31')"),
    ):
        self.start_date = start_date
        self.end_date = end_date

    def validate(self) -> 'DateRangeParams':
        """
        Validate the date range parameters.

        Returns:
            DateRangeParams: Self for method chaining.

        Raises:
            HTTPException: If the date range is invalid.
        """
        if self.start_date and self.end_date:
            from datetime import datetime
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
            if start > end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date must be before end_date",
                )
        return self


# ============================================
# RATE LIMITING DEPENDENCIES
# ============================================

class RateLimitInfo:
    """Rate limit information for the current request."""

    def __init__(self, request: Request):
        self.request = request
        self.limit = settings.RATE_LIMIT_REQUESTS
        self.period = settings.RATE_LIMIT_PERIOD
        self.remaining = self.limit

    def get_user_id(self) -> Optional[int]:
        """
        Get the authenticated user ID from the request state.

        Returns:
            Optional[int]: The user ID if authenticated, otherwise None.
        """
        return getattr(self.request.state, "user_id", None)

    def get_client_ip(self) -> str:
        """
        Get the client IP address.

        Returns:
            str: The client IP address.
        """
        forwarded = self.request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.request.client.host if self.request.client else "unknown"


# ============================================
# SERVICE DEPENDENCIES (Injection Points)
# ============================================

# These will be implemented as services are built

def get_cache_service():
    """
    Get the cache service instance.

    Returns:
        CacheService: The cache service instance.
    """
    from app.services.cache_service import cache_service
    return cache_service


def get_rabbitmq_client():
    """
    Get the RabbitMQ client instance.

    Returns:
        RabbitMQClient: The RabbitMQ client instance.
    """
    from app.core.rabbitmq import rabbitmq_client
    return rabbitmq_client


# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Authentication
    "security",
    "require_auth",
    "optional_auth",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "require_permission",

    # Pagination
    "PaginationParams",

    # Date Range
    "DateRangeParams",

    # Rate Limiting
    "RateLimitInfo",

    # Services
    "get_cache_service",
    "get_rabbitmq_client",

    # Database
    "get_db",
]