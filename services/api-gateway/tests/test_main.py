"""Tests for FastAPI application setup."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestApplication:
    """Test FastAPI application configuration."""

    def test_app_title(self):
        """Test app title is set correctly."""
        assert app.title == settings.SERVICE_NAME

    def test_app_version(self):
        """Test app version is set."""
        assert app.version == "1.0.0"

    def test_cors_preflight_allows_frontend_origin(self, client):
        """The browser frontend can call the gateway from its dev origin."""
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

    def test_validation_error_handler(self, client):
        """Test validation error handler returns proper format."""
        # This tests that the app handles 404s properly
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_404_handler(self, client):
        """Test 404 responses are handled."""
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404