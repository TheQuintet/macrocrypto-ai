"""
API response-time tests for data-service.

Each API endpoint has its own dedicated test function.
Response-time thresholds and request counts are loaded
from application settings.
"""

import time

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


# ============================================================
# BTC PRICE API
# ============================================================

def test_btc_price_response_time():
    """
    Verify BTC price API responds within the configured
    BTC response-time limit.
    """

    with TestClient(app) as client:
        start_time = time.perf_counter()

        response = client.get(
            "/api/v1/btc/price"
        )

        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

    assert response.status_code == 200

    assert response_time_ms <= (
        settings.BTC_PRICE_RESPONSE_TIME_LIMIT_MS
    ), (
        f"BTC price API response time was "
        f"{response_time_ms:.2f}ms, exceeding the configured "
        f"limit of "
        f"{settings.BTC_PRICE_RESPONSE_TIME_LIMIT_MS}ms"
    )


def test_btc_price_repeated_response_time():
    """
    Verify repeated BTC price requests remain within the
    configured BTC response-time limit.
    """

    response_times = []

    with TestClient(app) as client:
        for _ in range(
            settings.RESPONSE_TIME_TEST_REQUEST_COUNT
        ):
            start_time = time.perf_counter()

            response = client.get(
                "/api/v1/btc/price"
            )

            response_time_ms = (
                time.perf_counter() - start_time
            ) * 1000

            assert response.status_code == 200

            response_times.append(response_time_ms)

    max_response_time_ms = max(response_times)

    assert max_response_time_ms <= (
        settings.BTC_PRICE_RESPONSE_TIME_LIMIT_MS
    ), (
        f"BTC price API maximum response time was "
        f"{max_response_time_ms:.2f}ms, exceeding the configured "
        f"limit of "
        f"{settings.BTC_PRICE_RESPONSE_TIME_LIMIT_MS}ms"
    )


# ============================================================
# INDICATORS API
# ============================================================

def test_indicators_response_time():
    """
    Verify cached indicators API responds within the configured
    standard API response-time limit.
    """

    with TestClient(app) as client:

        # Populate the Redis cache.
        response = client.get(
            "/api/v1/indicators"
        )

        assert response.status_code == 200

        # Measure cached response.
        start_time = time.perf_counter()

        response = client.get(
            "/api/v1/indicators"
        )

        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

    assert response.status_code == 200

    assert response_time_ms <= (
        settings.API_RESPONSE_TIME_LIMIT_MS
    ), (
        f"Indicators API response time was "
        f"{response_time_ms:.2f}ms, exceeding the configured "
        f"limit of "
        f"{settings.API_RESPONSE_TIME_LIMIT_MS}ms"
    )


# ============================================================
# CURRENT REGIME API
# ============================================================

def test_current_regime_response_time():
    """
    Verify current regime API responds within the configured
    standard API response-time limit.
    """

    with TestClient(app) as client:
        start_time = time.perf_counter()

        response = client.get(
            "/api/v1/regimes/current"
        )

        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

    assert response.status_code == 200

    assert response_time_ms <= (
        settings.API_RESPONSE_TIME_LIMIT_MS
    ), (
        f"Current regime API response time was "
        f"{response_time_ms:.2f}ms, exceeding the configured "
        f"limit of "
        f"{settings.API_RESPONSE_TIME_LIMIT_MS}ms"
    )


# ============================================================
# REGIME BTC API
# ============================================================

def test_regime_btc_response_time():
    """
    Verify regime BTC API responds within the configured
    standard API response-time limit.
    """

    with TestClient(app) as client:
        start_time = time.perf_counter()

        response = client.get(
            "/api/v1/regimes/btc"
        )

        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

    assert response.status_code == 200

    assert response_time_ms <= (
        settings.API_RESPONSE_TIME_LIMIT_MS
    ), (
        f"Regime BTC API response time was "
        f"{response_time_ms:.2f}ms, exceeding the configured "
        f"limit of "
        f"{settings.API_RESPONSE_TIME_LIMIT_MS}ms"
    )


# ============================================================
# SIMILAR HISTORICAL PERIODS API
# ============================================================

def test_similar_periods_response_time():
    """
    Verify similar historical periods API responds within
    the configured standard API response-time limit.
    """

    with TestClient(app) as client:
        start_time = time.perf_counter()

        response = client.get(
            "/api/v1/regimes/history/similar-periods"
        )

        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

    assert response.status_code == 200

    assert response_time_ms <= (
        settings.API_RESPONSE_TIME_LIMIT_MS
    ), (
        f"Similar periods API response time was "
        f"{response_time_ms:.2f}ms, exceeding the configured "
        f"limit of "
        f"{settings.API_RESPONSE_TIME_LIMIT_MS}ms"
    )


# ============================================================
# ECONOMIC CALENDAR API
# ============================================================

def test_economic_calendar_response_time():
    """
    Verify economic calendar API responds within the configured
    standard API response-time limit.
    """

    with TestClient(app) as client:
        start_time = time.perf_counter()

        response = client.get(
            "/api/v1/economic-calendar"
        )

        response_time_ms = (
            time.perf_counter() - start_time
        ) * 1000

    assert response.status_code == 200

    assert response_time_ms <= (
        settings.API_RESPONSE_TIME_LIMIT_MS
    ), (
        f"Economic calendar API response time was "
        f"{response_time_ms:.2f}ms, exceeding the configured "
        f"limit of "
        f"{settings.API_RESPONSE_TIME_LIMIT_MS}ms"
    )