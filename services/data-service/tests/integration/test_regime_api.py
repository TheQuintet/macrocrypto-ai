"""
Integration tests for the macroeconomic regime API.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ============================================================
# CURRENT REGIME
# ============================================================

def test_get_current_regime():
    """
    Verify the current regime endpoint returns a valid response.
    """

    response = client.get(
        "/api/v1/regimes/current"
    )

    assert response.status_code in (200, 404)

    if response.status_code == 200:
        data = response.json()

        assert "id" in data
        assert "regime_type" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "performance" in data


# ============================================================
# REGIME HISTORY
# ============================================================

def test_get_regime_history():
    """
    Verify the regime history endpoint returns a list.
    """

    response = client.get(
        "/api/v1/regimes"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for regime in data:
        assert "id" in regime
        assert "regime_type" in regime
        assert "start_date" in regime
        assert "end_date" in regime
        assert "performance" in regime


# ============================================================
# REGIME BY ID
# ============================================================

def test_get_regime_by_id():
    """
    Verify a specific regime can be retrieved.
    """

    history_response = client.get(
        "/api/v1/regimes"
    )

    assert history_response.status_code == 200

    regimes = history_response.json()

    if not regimes:
        pytest.skip(
            "No macroeconomic regimes available"
        )

    regime_id = regimes[0]["id"]

    response = client.get(
        f"/api/v1/regimes/{regime_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == regime_id
    assert "regime_type" in data
    assert "start_date" in data
    assert "end_date" in data
    assert "performance" in data


# ============================================================
# NOT FOUND
# ============================================================

def test_get_regime_not_found():
    """
    Verify requesting a nonexistent regime returns 404.
    """

    response = client.get(
        "/api/v1/regimes/999999"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == (
        "Macroeconomic regime 999999 not found"
    )


# ============================================================
# PERFORMANCE DATA
# ============================================================

def test_regime_includes_performance():
    """
    Verify completed regimes expose BTC performance data
    when performance has been calculated.
    """

    response = client.get(
        "/api/v1/regimes"
    )

    assert response.status_code == 200

    regimes = response.json()

    if not regimes:
        pytest.skip(
            "No macroeconomic regimes available"
        )

    for regime in regimes:

        performance = regime.get(
            "performance"
        )

        if performance is not None:
            assert "avg_return" in performance
            assert "max_drawdown" in performance
            assert "volatility" in performance
            assert "sharpe_ratio" in performance
            assert "btc_price_start" in performance
            assert "btc_price_end" in performance