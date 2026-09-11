import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
def test_get_btc_dominance_endpoint(client):
    """Test GET /api/v1/btc/dominance endpoint."""

    dominance_data = {
        "btc_dominance": 56.42,
        "time": "2026-09-10T10:00:00+00:00",
        "source": "coingecko",
    }

    mock_service = MagicMock()
    mock_service.get_dominance = AsyncMock(
        return_value=dominance_data
    )
    mock_service.close = AsyncMock()

    with patch(
        "app.api.btc.BTCDominanceService",
        return_value=mock_service,
    ):
        response = client.get("/api/v1/btc/dominance")

    assert response.status_code == 200

    data = response.json()

    assert data["btc_dominance"] == 56.42
    assert data["source"] == "coingecko"
    assert "time" in data

    mock_service.get_dominance.assert_awaited_once()
    mock_service.close.assert_awaited_once()


def test_get_btc_dominance_endpoint_returns_404_when_no_data(client):
    """Test BTC dominance endpoint returns 404 when no data exists."""

    mock_service = MagicMock()
    mock_service.get_dominance = AsyncMock(
        return_value=None
    )
    mock_service.close = AsyncMock()

    with patch(
        "app.api.btc.BTCDominanceService",
        return_value=mock_service,
    ):
        response = client.get("/api/v1/btc/dominance")

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "BTC dominance data is not available"

    mock_service.get_dominance.assert_awaited_once()
    mock_service.close.assert_awaited_once()