"""Core utilities and configurations for API Gateway service.

This package contains foundational components used across the service:

Modules:
- config.py: Pydantic settings with environment variable loading
- security.py: JWT authentication, password hashing (to be added)
- rate_limiter.py: Tiered rate limiting middleware (to be added)
- cache.py: Redis client and caching utilities (to be added)
- rabbitmq.py: RabbitMQ producer/consumer client (to be added)
- websocket_manager.py: WebSocket connection management (to be added)
"""

from app.core.config import settings, get_settings

__all__ = [
    "settings",
    "get_settings",
]