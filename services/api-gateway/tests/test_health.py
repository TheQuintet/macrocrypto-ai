"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test GET /health returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
        assert "version" in data

    def test_readiness_check(self, client):
        """Test GET /ready returns ready status."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "api-gateway"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test GET / returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "api-gateway"
        assert data["status"] == "operational"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"

    def test_version_endpoint(self, client):
        """Test GET /version returns version."""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "api-gateway"
        assert "version" in data

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "api-gateway"
        assert "paths" in data

    def test_docs_redirect(self, client):
        """Test docs endpoint redirects to Swagger UI."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()