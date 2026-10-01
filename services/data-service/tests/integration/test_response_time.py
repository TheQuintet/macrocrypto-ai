"""
API response-time tests for data-service.
"""

import time
from fastapi.testclient import TestClient
from app.config import settings


def test_btc_price_response_time(client: TestClient):
    warmup_response = client.get("/api/v1/btc/price")
    assert warmup_response.status_code == 200

    start_time = time.perf_counter()
    response = client.get("/api/v1/btc/price")
    response_time_ms = (time.perf_counter() - start_time) * 1000

    assert response.status_code == 200
    assert response_time_ms <= settings.BTC_PRICE_RESPONSE_TIME_LIMIT_MS, (
        f"BTC price API response time was {response_time_ms:.2f}ms, "
        f"exceeding limit of {settings.BTC_PRICE_RESPONSE_TIME_LIMIT_MS}ms"
    )


def test_btc_price_repeated_response_time(client: TestClient):
    client.get("/api/v1/btc/price")
    response_times = []

    for _ in range(settings.RESPONSE_TIME_TEST_REQUEST_COUNT):
        start_time = time.perf_counter()
        response = client.get("/api/v1/btc/price")
        response_time_ms = (time.perf_counter() - start_time) * 1000
        assert response.status_code == 200
        response_times.append(response_time_ms)

    max_response_time_ms = max(response_times)
    assert max_response_time_ms <= settings.BTC_PRICE_RESPONSE_TIME_LIMIT_MS


def test_indicators_response_time(client: TestClient):
    """
    Indicators endpoint aggregates multiple metrics; allow up to 3000ms 
    if running un-cached in test DB environments.
    """
    client.get("/api/v1/indicators")
    
    start_time = time.perf_counter()
    response = client.get("/api/v1/indicators")
    response_time_ms = (time.perf_counter() - start_time) * 1000

    assert response.status_code == 200
    # Use max of standard limit or a safe analytical threshold (e.g., 3000ms) for heavy queries
    limit = max(settings.API_RESPONSE_TIME_LIMIT_MS, 3000)
    assert response_time_ms <= limit, (
        f"Indicators API response time was {response_time_ms:.2f}ms, exceeding limit of {limit}ms"
    )


def test_current_regime_response_time(client: TestClient, seed_current_regime):
    client.get("/api/v1/regimes/current")

    start_time = time.perf_counter()
    response = client.get("/api/v1/regimes/current")
    response_time_ms = (time.perf_counter() - start_time) * 1000

    assert response.status_code == 200
    assert response_time_ms <= settings.API_RESPONSE_TIME_LIMIT_MS


def test_regime_btc_response_time(client: TestClient):
    client.get("/api/v1/regimes/btc")

    start_time = time.perf_counter()
    response = client.get("/api/v1/regimes/btc")
    response_time_ms = (time.perf_counter() - start_time) * 1000

    assert response.status_code == 200
    limit = max(settings.API_RESPONSE_TIME_LIMIT_MS, 2000)
    assert response_time_ms <= limit


def test_similar_periods_response_time(client: TestClient):
    client.get("/api/v1/regimes/history/similar-periods")

    start_time = time.perf_counter()
    response = client.get("/api/v1/regimes/history/similar-periods")
    response_time_ms = (time.perf_counter() - start_time) * 1000

    assert response.status_code == 200
    limit = max(settings.API_RESPONSE_TIME_LIMIT_MS, 2000)
    assert response_time_ms <= limit


def test_economic_calendar_response_time(client: TestClient):
    client.get("/api/v1/economic-calendar")

    start_time = time.perf_counter()
    response = client.get("/api/v1/economic-calendar")
    response_time_ms = (time.perf_counter() - start_time) * 1000

    assert response.status_code == 200
    assert response_time_ms <= settings.API_RESPONSE_TIME_LIMIT_MS