"""
Integration test for BTC price API endpoint.

Validates:
- Endpoint availability
- HTTP response status
- Response schema fields
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client with app state initialized."""
    # Create a new client for each test
    return TestClient(app)


def test_get_btc_price_endpoint(client):
    """Test GET /api/v1/btc/price endpoint."""
    response = client.get("/api/v1/btc/price")

    assert response.status_code == 200

    data = response.json()

    # Validate response fields
    assert "current_price" in data
    assert "change_24h" in data
    assert "change_24h_percent" in data

    assert "high_24h" in data
    assert "low_24h" in data
    assert "volume_24h" in data

    assert "change_7d" in data
    assert "change_7d_percent" in data

    assert "updated_at" in data


def test_get_btc_price_endpoint_returns_float_values(client):
    """Test that price fields return float values."""
    response = client.get("/api/v1/btc/price")
    assert response.status_code == 200

    data = response.json()

    # Check that price fields are either float or None
    if data["current_price"] is not None:
        assert isinstance(data["current_price"], float)
    if data["change_24h"] is not None:
        assert isinstance(data["change_24h"], float)
    if data["change_24h_percent"] is not None:
        assert isinstance(data["change_24h_percent"], float)