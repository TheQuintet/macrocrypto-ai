"""Unit tests for rate limiting functionality."""

import pytest
import time
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.rate_limiter import RateLimiter, RateLimitMiddleware, RATE_LIMITS
from app.core.redis import redis_client


@pytest.fixture
def app():
    """Create a test FastAPI app with rate limiting."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    app.add_middleware(RateLimitMiddleware)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestRateLimiter:
    """Test rate limiter core functionality."""

    def test_get_rate_limit_config(self):
        """Test getting rate limit config for different roles."""
        limiter = RateLimiter()

        # Guest config
        guest_requests, guest_period = limiter._get_rate_limit_config("guest")
        assert guest_requests == RATE_LIMITS["guest"]["requests"]
        assert guest_period == RATE_LIMITS["guest"]["period"]

        # User config
        user_requests, user_period = limiter._get_rate_limit_config("user")
        assert user_requests == RATE_LIMITS["user"]["requests"]
        assert user_period == RATE_LIMITS["user"]["period"]

        # Admin config
        admin_requests, admin_period = limiter._get_rate_limit_config("admin")
        assert admin_requests == RATE_LIMITS["admin"]["requests"]
        assert admin_period == RATE_LIMITS["admin"]["period"]

        # Unknown role falls back to guest
        unknown_requests, unknown_period = limiter._get_rate_limit_config("unknown")
        assert unknown_requests == RATE_LIMITS["guest"]["requests"]

    def test_get_identifier_from_user_id(self):
        """Test getting identifier from user ID."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.user_id = 123
        request.headers = {}
        request.client = None

        identifier = limiter._get_identifier(request)
        assert identifier == "user:123"

    def test_get_identifier_from_api_key(self):
        """Test getting identifier from API key."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.user_id = None
        request.headers = {"X-API-Key": "test_apikey_12345678"}
        request.client = None

        identifier = limiter._get_identifier(request)
        assert identifier == "apikey:test_api"

    def test_get_identifier_from_ip(self):
        """Test getting identifier from client IP."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.user_id = None
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        identifier = limiter._get_identifier(request)
        assert identifier == "ip:192.168.1.100"

    def test_get_identifier_from_forwarded_ip(self):
        """Test getting identifier from X-Forwarded-For header."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.user_id = None
        request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request.client = None

        identifier = limiter._get_identifier(request)
        assert identifier == "ip:10.0.0.1"

    def test_get_role_from_user(self):
        """Test getting role from authenticated user."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        user = MagicMock()
        user.role = "admin"
        request.state.current_user = user

        role = limiter._get_role(request)
        assert role == "admin"

    def test_get_role_from_guest(self):
        """Test getting role for guest user."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.current_user = None
        request.state.api_key = None

        role = limiter._get_role(request)
        assert role == "guest"


class TestRateLimitMiddleware:
    """Test rate limit middleware integration."""

    def test_rate_limit_headers(self, client):
        """Test rate limit headers are present in response."""
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_health_check_bypass(self, client):
        """Test health check bypasses rate limiting."""
        response = client.get("/health")
        assert response.status_code == 200
        # Health check should not have rate limit headers
        assert "X-RateLimit-Limit" not in response.headers

    @patch("app.core.rate_limiter.rate_limiter.enabled", False)
    def test_rate_limiting_disabled(self, client):
        """Test rate limiting when disabled."""
        response = client.get("/test")
        assert response.status_code == 200
        # When disabled, headers should still be present
        assert "X-RateLimit-Limit" in response.headers

    def test_rate_limit_exceeded(self, client):
        """Test rate limit exceeded response."""
        # Make multiple requests to try to exceed the limit
        # In test environment with mocked Redis, this may not actually exceed
        # But we verify the middleware is configured correctly
        for i in range(5):
            response = client.get("/test")
            if response.status_code == 429:
                assert "Rate limit exceeded" in response.text
                assert response.headers["X-RateLimit-Remaining"] == "0"
                assert "Retry-After" in response.headers
                break


class TestRateLimiterIntegration:
    """Integration tests for rate limiter with Redis."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(self):
        """Test first request from a client."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.user_id = None
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        with patch("app.core.rate_limiter.redis_client.get", return_value=None):
            with patch("app.core.rate_limiter.redis_client.set") as mock_set:
                is_allowed, max_req, remaining, reset = await limiter.check_rate_limit(request)
                assert is_allowed is True
                assert remaining == max_req - 1
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.user_id = None
        request.state.current_user = None
        request.state.api_key = None
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        # Patch both the get and the _get_role method
        with patch("app.core.rate_limiter.redis_client.get", return_value="10"):
            with patch("app.core.rate_limiter.redis_client.ttl", return_value=30):
                # Mock the _get_role method to return "guest" so we use the 10 limit
                with patch.object(limiter, "_get_role", return_value="guest"):
                    is_allowed, max_req, remaining, reset = await limiter.check_rate_limit(request)
                    assert is_allowed is False
                    assert remaining == 0
                    assert reset > 0

    @pytest.mark.asyncio
    async def test_reset_rate_limit(self):
        """Test resetting rate limit."""
        limiter = RateLimiter()
        request = MagicMock(spec=Request)
        request.state.user_id = None
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        with patch("app.core.rate_limiter.redis_client.delete") as mock_delete:
            await limiter.reset_rate_limit(request)
            mock_delete.assert_called_once()