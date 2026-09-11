"""
Integration tests for the macroeconomic regime API.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
import time

import httpx

from app.cache.client import CacheClient
from app.config import settings
from app.api.regime import get_btc_regime_cache_key
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
        assert "confidence" in data
        assert "visual_indicator" in data
        assert "identified_at" in data
        assert "expires_at" in data

        assert isinstance(data["id"], int)
        assert isinstance(data["regime_type"], str)
        assert isinstance(
            data["confidence"],
            (int, float),
        )
        assert isinstance(
            data["visual_indicator"],
            str,
        )

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

# ============================================================
# BTC REGIME SUMMARY
# ============================================================

def test_get_btc_regime_success():
    """
    Verify GET /api/v1/regimes/btc returns a successful response.
    """

    response = client.get(
        "/api/v1/regimes/btc"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert "current_regime" in data
    assert "historical_regimes" in data
    assert "similar_periods" in data
    assert "event_analysis" in data


def test_get_btc_regime_response_schema():
    """
    Verify the response structure and nested fields.
    """

    response = client.get(
        "/api/v1/regimes/btc"
    )

    assert response.status_code == 200

    data = response.json()

    # Top-level schema
    assert isinstance(data["current_regime"], (dict, type(None)))
    assert isinstance(data["historical_regimes"], list)
    assert isinstance(data["similar_periods"], list)
    assert isinstance(data["event_analysis"], list)

    # Current regime
    if data["current_regime"] is not None:
        current = data["current_regime"]

        assert "id" in current
        assert "regime_type" in current
        assert "confidence" in current
        assert "visual_indicator" in current
        assert "identified_at" in current
        assert "expires_at" in current

    # Historical regimes
    for regime in data["historical_regimes"]:
        assert "id" in regime
        assert "regime_type" in regime
        assert "start_date" in regime
        assert "end_date" in regime
        assert "duration_days" in regime
        assert "performance" in regime

    # Similar periods
    for period in data["similar_periods"]:
        assert "period_start" in period
        assert "period_end" in period
        assert "distance" in period
        assert "similarity_score" in period
        assert "reason" in period
        assert "matching_indicators" in period
        assert "macro_conditions" in period
        assert "btc_performance" in period

    # Event analysis
    for event in data["event_analysis"]:
        assert "id" in event
        assert "regime_id" in event
        assert "event_type" in event
        assert "event_date" in event
        assert "btc_price_before" in event
        assert "btc_price_after" in event
        assert "btc_return" in event
        assert "created_at" in event


def test_get_btc_regime_regime_filter():
    """
    Verify regime_type filtering works.
    """

    response = client.get(
        "/api/v1/regimes/btc",
        params={"regime_type": "high_inflation"},
    )

    assert response.status_code == 200

    data = response.json()

    for regime in data["historical_regimes"]:
        assert regime["regime_type"] == "high_inflation"


def test_get_btc_regime_date_range_filter():
    """
    Verify start_date and end_date filtering works.
    """

    response = client.get(
        "/api/v1/regimes/btc",
        params={
            "start_date": "2026-08-13",
            "end_date": "2026-08-14",
        },
    )

    assert response.status_code == 200

    data = response.json()

    for regime in data["historical_regimes"]:
        regime_start = date.fromisoformat(
            regime["start_date"]
        )

        assert regime_start >= date(2026, 8, 13)
        assert regime_start <= date(2026, 8, 14)


def test_get_btc_regime_current_regime_data():
    """
    Verify current regime data is included.
    """

    response = client.get(
        "/api/v1/regimes/btc"
    )

    assert response.status_code == 200

    data = response.json()

    current = data["current_regime"]

    if current is None:
        pytest.skip(
            "No current macroeconomic regime available"
        )

    assert isinstance(current["id"], int)
    assert isinstance(current["regime_type"], str)
    assert isinstance(current["confidence"], (int, float))
    assert isinstance(current["visual_indicator"], str)
    assert current["identified_at"] is not None


def test_get_btc_regime_similar_periods():
    """
    Verify similar historical periods are returned correctly.
    """

    response = client.get(
        "/api/v1/regimes/btc"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data["similar_periods"],
        list,
    )

    for period in data["similar_periods"]:
        assert 0 <= period["similarity_score"] <= 1
        assert period["distance"] >= 0
        assert isinstance(
            period["matching_indicators"],
            list,
        )
        assert isinstance(
            period["macro_conditions"],
            dict,
        )


def test_get_btc_regime_event_analysis():
    """
    Verify macro event analysis data is returned correctly.
    """

    response = client.get(
        "/api/v1/regimes/btc"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data["event_analysis"],
        list,
    )

    for event in data["event_analysis"]:
        assert isinstance(event["id"], int)
        assert isinstance(event["regime_id"], int)
        assert isinstance(event["event_type"], str)
        assert event["event_date"] is not None


def test_get_btc_regime_invalid_similar_limit():
    """
    Verify invalid similar_limit values are rejected.
    """

    response = client.get(
        "/api/v1/regimes/btc",
        params={"similar_limit": 11},
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "similar_limit must be between 1 and 10"
    )


def test_get_btc_regime_invalid_date_range():
    """
    Verify an invalid date range is rejected.
    """

    response = client.get(
        "/api/v1/regimes/btc",
        params={
            "start_date": "2026-08-14",
            "end_date": "2026-08-13",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "start_date cannot be later than end_date"
    )


@pytest.mark.skip(
    reason="JWT authentication is not implemented yet; deferred with PO agreement."
)
def test_get_btc_regime_authentication():
    """
    Authentication test deferred because JWT is not currently implemented.
    """
    pass
@pytest.mark.asyncio
async def test_get_btc_regime_response_time(
    seed_current_regime,
    seed_regime_history,
):
    """
    Verify the BTC regime endpoint meets the <500 ms
    response-time acceptance criterion using Redis cache.
    """

    cache = CacheClient()
    connected = await cache.connect()

    if not connected:
        pytest.skip("Redis not available")

    app.state.cache_client = cache

    transport = httpx.ASGITransport(app=app)

    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as async_client:

            # Warm the endpoint and populate the Redis cache.
            warmup_response = await async_client.get(
                "/api/v1/regimes/btc"
            )

            assert warmup_response.status_code == 200

            cache_key = get_btc_regime_cache_key(
                regime_type=None,
                start_date=None,
                end_date=None,
                similar_limit=5,
            )

            cached = await cache.get(cache_key)

            assert cached is not None, (
                "BTC regime response was not written to Redis cache"
            )

            # Measure the cached request only.
            start = time.perf_counter()

            response = await async_client.get(
                "/api/v1/regimes/btc"
            )

            elapsed_ms = (
                time.perf_counter() - start
            ) * 1000

            assert response.status_code == 200

            assert elapsed_ms < 500, (
                f"Response time {elapsed_ms:.2f} ms "
                "exceeds the 500 ms acceptance criterion"
            )

    finally:
        await cache.delete(cache_key)
        await cache.close()
        app.state.cache_client = None