"""
Integration test for BTC price API endpoint.

Validates:
- Endpoint availability
- HTTP response status
- Response schema fields
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_btc_price_endpoint():
    """
    Test GET /api/v1/btc/price endpoint.
    """

    response = client.get(
        "/api/v1/btc/price"
    )

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