"""Tests for FastAPI application setup."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from app.main import (
    app,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.config import settings
from app.core.rabbitmq import rabbitmq_client
from app.core.redis import redis_client


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


class TestApplication:
    """Test FastAPI application configuration."""

    def test_app_title(self):
        """Test app title is set correctly."""
        assert app.title == settings.SERVICE_NAME

    def test_app_version(self):
        """Test app version is set correctly."""
        assert app.version == "1.0.0"

    def test_app_description(self):
        """Test application description is configured."""
        assert "API Gateway for MacroCrypto AI" in app.description

    def test_docs_are_enabled(self, client):
        """Test Swagger and ReDoc endpoints are available."""
        docs_response = client.get("/docs")
        redoc_response = client.get("/redoc")

        assert docs_response.status_code == 200
        assert redoc_response.status_code == 200

    def test_openapi_endpoint(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200

        data = response.json()

        assert data["info"]["title"] == settings.SERVICE_NAME
        assert data["info"]["version"] == "1.0.0"
        assert "/" in data["paths"]
        assert "/health" in data["paths"]
        assert "/ready" in data["paths"]
        assert "/version" in data["paths"]

    def test_cors_preflight_allows_frontend_origin(self, client):
        """Test browser frontend can call the gateway from its dev origin."""
        response = client.options(
            "/api/v1/btc/price",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert (
            response.headers["access-control-allow-origin"]
            == "http://localhost:3000"
        )

    def test_cors_rejects_unconfigured_origin(self, client):
        """Test an unconfigured origin is not granted CORS access."""
        response = client.options(
            "/api/v1/btc/price",
            headers={
                "Origin": "http://malicious.example",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 400

    def test_root_endpoint(self, client):
        """Test root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200

        data = response.json()

        assert data["service"] == settings.SERVICE_NAME
        assert data["version"] == app.version
        assert data["status"] == "operational"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"

    def test_health_endpoint(self, client):
        """Test health endpoint returns service health information."""
        with patch.object(
            rabbitmq_client,
            "is_connected",
            return_value=True,
        ):
            response = client.get("/health")

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == settings.SERVICE_NAME
        assert data["version"] == app.version
        assert data["redis_enabled"] == settings.REDIS_ENABLED
        assert data["rabbitmq_connected"] is True
        assert data["database"] == "connected"

    def test_health_endpoint_when_rabbitmq_disconnected(self, client):
        """Test health endpoint reports disconnected RabbitMQ."""
        with patch.object(
            rabbitmq_client,
            "is_connected",
            return_value=False,
        ):
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["rabbitmq_connected"] is False

    def test_readiness_endpoint(self, client):
        """Test readiness endpoint."""
        with patch.object(
            rabbitmq_client,
            "is_connected",
            return_value=True,
        ):
            response = client.get("/ready")

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "ready"
        assert data["service"] == settings.SERVICE_NAME
        assert data["version"] == app.version
        assert data["rabbitmq_connected"] is True

    def test_readiness_endpoint_when_rabbitmq_disconnected(self, client):
        """Test readiness endpoint reports RabbitMQ state."""
        with patch.object(
            rabbitmq_client,
            "is_connected",
            return_value=False,
        ):
            response = client.get("/ready")

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "ready"
        assert data["rabbitmq_connected"] is False

    def test_version_endpoint(self, client):
        """Test version endpoint."""
        response = client.get("/version")

        assert response.status_code == 200

        data = response.json()

        assert data["service"] == settings.SERVICE_NAME
        assert data["version"] == app.version

    def test_404_handler(self, client):
        """Test unknown routes return HTTP 404."""
        response = client.get("/non-existent-endpoint")

        assert response.status_code == 404

    def test_api_404_handler(self, client):
        """Test unknown API routes return HTTP 404."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    def test_validation_error_handler(self):
        """Test custom request validation error handler."""

        class TestModel(BaseModel):
            """Model used to generate a validation error."""

            required_field: int

        try:
            TestModel(required_field="invalid")
        except ValidationError as exc:
            validation_error = RequestValidationError(exc.errors())

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/test",
                "headers": [],
                "query_string": b"",
            }
        )

        response = asyncio.run(
            validation_exception_handler(
                request,
                validation_error,
            )
        )

        assert response.status_code == 422

        body = json.loads(response.body)

        assert body["detail"] == "Request validation failed"
        assert len(body["errors"]) == 1
        assert body["errors"][0]["field"] == "required_field"
        assert body["errors"][0]["message"]
        assert body["errors"][0]["type"]

    def test_generic_exception_handler_debug_disabled(self):
        """Test generic exception hides details when debug is disabled."""
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [],
                "query_string": b"",
            }
        )

        exception = RuntimeError("secret internal error")

        with patch.object(settings, "DEBUG", False):
            response = asyncio.run(
                generic_exception_handler(
                    request,
                    exception,
                )
            )

        assert response.status_code == 500

        body = json.loads(response.body)

        assert body["detail"] == "An internal server error occurred"
        assert body["message"] is None

    def test_generic_exception_handler_debug_enabled(self):
        """Test generic exception exposes details when debug is enabled."""
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [],
                "query_string": b"",
            }
        )

        exception = RuntimeError("test internal error")

        with patch.object(settings, "DEBUG", True):
            response = asyncio.run(
                generic_exception_handler(
                    request,
                    exception,
                )
            )

        assert response.status_code == 500

        body = json.loads(response.body)

        assert body["detail"] == "An internal server error occurred"
        assert body["message"] == "test internal error"


class TestLifespan:
    """Test application startup and shutdown lifecycle."""

    def test_lifespan_with_redis_and_rabbitmq(self):
        """Test successful startup and shutdown with enabled dependencies."""
        mock_redis_connect = AsyncMock()
        mock_redis_disconnect = AsyncMock()
        mock_rabbitmq_connect = AsyncMock(return_value=True)
        mock_rabbitmq_close = MagicMock()
        mock_consumer = AsyncMock()

        with (
            patch.object(
                settings,
                "REDIS_ENABLED",
                True,
            ),
            patch.object(
                redis_client,
                "connect",
                mock_redis_connect,
            ),
            patch.object(
                redis_client,
                "disconnect",
                mock_redis_disconnect,
            ),
            patch.object(
                rabbitmq_client,
                "connect",
                mock_rabbitmq_connect,
            ),
            patch.object(
                rabbitmq_client,
                "close",
                mock_rabbitmq_close,
            ),
            patch(
                "app.main._start_rabbitmq_consumer",
                mock_consumer,
            ),
        ):
            with TestClient(app):
                pass

        mock_redis_connect.assert_awaited_once()
        mock_redis_disconnect.assert_awaited_once()
        mock_rabbitmq_connect.assert_awaited_once()
        mock_rabbitmq_close.assert_called_once()

    def test_lifespan_with_redis_disabled(self):
        """Test startup when Redis is disabled."""
        mock_redis_connect = AsyncMock()
        mock_redis_disconnect = AsyncMock()
        mock_rabbitmq_connect = AsyncMock(return_value=False)
        mock_rabbitmq_close = MagicMock()

        with (
            patch.object(
                settings,
                "REDIS_ENABLED",
                False,
            ),
            patch.object(
                redis_client,
                "connect",
                mock_redis_connect,
            ),
            patch.object(
                redis_client,
                "disconnect",
                mock_redis_disconnect,
            ),
            patch.object(
                rabbitmq_client,
                "connect",
                mock_rabbitmq_connect,
            ),
            patch.object(
                rabbitmq_client,
                "close",
                mock_rabbitmq_close,
            ),
        ):
            with TestClient(app):
                pass

        mock_redis_connect.assert_not_awaited()
        mock_redis_disconnect.assert_awaited_once()
        mock_rabbitmq_connect.assert_awaited_once()
        mock_rabbitmq_close.assert_called_once()

    def test_lifespan_when_rabbitmq_connection_fails(self):
        """Test startup continues when RabbitMQ cannot connect."""
        mock_redis_connect = AsyncMock()
        mock_redis_disconnect = AsyncMock()
        mock_rabbitmq_connect = AsyncMock(return_value=False)
        mock_rabbitmq_close = MagicMock()

        with (
            patch.object(
                settings,
                "REDIS_ENABLED",
                True,
            ),
            patch.object(
                redis_client,
                "connect",
                mock_redis_connect,
            ),
            patch.object(
                redis_client,
                "disconnect",
                mock_redis_disconnect,
            ),
            patch.object(
                rabbitmq_client,
                "connect",
                mock_rabbitmq_connect,
            ),
            patch.object(
                rabbitmq_client,
                "close",
                mock_rabbitmq_close,
            ),
        ):
            with TestClient(app):
                pass

        mock_redis_connect.assert_awaited_once()
        mock_redis_disconnect.assert_awaited_once()
        mock_rabbitmq_connect.assert_awaited_once()
        mock_rabbitmq_close.assert_called_once()

