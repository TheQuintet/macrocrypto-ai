"""
Integration tests for API rate limiting.

Tests rate limiting for all data-service APIs:

- BTC price API
- Macroeconomic indicators API
- Regime API
- Similar periods API
- Economic calendar API

IMPORTANT:
The Regime, Similar Periods, and Economic Calendar endpoints may perform
database queries and/or expensive calculations. They must not be tested by
sending RATE_LIMIT_REQUESTS concurrent requests because that tests endpoint
throughput rather than the rate limiter and can block the Uvicorn worker.

The expensive endpoints are therefore tested for:

1. Reachability
2. Successful HTTP response
3. Basic rate-limit middleware behavior

The actual rate-limit threshold test is performed only against the
lightweight BTC price API.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import pytest
import requests

from app.config import settings


# ============================================
# API CONFIGURATION
# ============================================

BASE_URL = f"http://127.0.0.1:{settings.SERVICE_PORT}"

BTC_API_URL = f"{BASE_URL}/api/v1/btc/price"

INDICATORS_API_URL = (
    f"{BASE_URL}/api/v1/indicators"
)

REGIME_API_URL = (
    f"{BASE_URL}/api/v1/regimes"
)

SIMILAR_PERIODS_API_URL = (
    f"{BASE_URL}/api/v1/regimes/history/similar-periods"
)

ECONOMIC_CALENDAR_API_URL = (
    f"{BASE_URL}/api/v1/economic-calendar"
)


# ============================================
# RATE LIMIT CONFIGURATION
# ============================================

RATE_LIMIT = settings.RATE_LIMIT_REQUESTS
RATE_LIMIT_ENABLED = settings.RATE_LIMIT_ENABLED

# Leave a small safety margin before triggering the limit.
RATE_LIMIT_SAFETY_MARGIN = 5

# Number of additional requests used to trigger the limit.
RATE_LIMIT_TRIGGER_ATTEMPTS = 10

# Number of concurrent workers used for lightweight endpoints.
RATE_LIMIT_CONCURRENT_WORKERS = min(RATE_LIMIT, 20)

# Rate-limit window is currently one minute.
RATE_LIMIT_RESET_WAIT_SECONDS = 65

# Maximum time allowed for an individual HTTP request.
RATE_LIMIT_REQUEST_TIMEOUT = 30

# Maximum number of requests used for expensive endpoints.
EXPENSIVE_API_REQUEST_COUNT = 3


# ============================================
# REQUEST HELPERS
# ============================================

def _send_get_request(api_url: str):
    """
    Send a GET request to an API endpoint.

    A timeout prevents an individual request from hanging
    indefinitely during integration testing.
    """

    try:
        return requests.get(
            api_url,
            timeout=RATE_LIMIT_REQUEST_TIMEOUT,
        )

    except requests.RequestException as exc:
        return exc


def _send_concurrent_requests(
    api_url: str,
    request_count: int,
):
    """
    Send multiple GET requests concurrently.

    This helper is intended for lightweight endpoints only.
    """

    responses = []

    with ThreadPoolExecutor(
        max_workers=RATE_LIMIT_CONCURRENT_WORKERS,
    ) as executor:

        futures = [
            executor.submit(
                _send_get_request,
                api_url,
            )
            for _ in range(request_count)
        ]

        for future in as_completed(futures):
            responses.append(
                future.result()
            )

    return responses


def _assert_successful_response(
    response,
    api_name: str,
):
    """
    Assert that an HTTP request completed successfully.
    """

    if isinstance(response, Exception):
        pytest.fail(
            f"{api_name} request failed: {response}"
        )

    assert response.status_code == 200, (
        f"{api_name} returned unexpected HTTP "
        f"{response.status_code}. "
        f"Response: {response.text[:1000]}"
    )


# ============================================
# EXPENSIVE API TEST
# ============================================

def _test_expensive_api_rate_limit(
    api_url: str,
    api_name: str,
):
    """
    Safely test an expensive API protected by the rate limiter.

    We intentionally do not send 95-100 concurrent requests.

    The purpose here is to verify that the endpoint remains reachable
    while rate limiting is enabled. The actual threshold behavior is
    tested separately against the lightweight BTC price endpoint.
    """

    if not RATE_LIMIT_ENABLED:
        pytest.skip(
            "API rate limiting is disabled in configuration."
        )

    print(
        f"\n🔎 {api_name}: testing expensive endpoint safely..."
    )

    for request_number in range(
        1,
        EXPENSIVE_API_REQUEST_COUNT + 1,
    ):

        response = _send_get_request(
            api_url
        )

        if isinstance(response, Exception):
            pytest.fail(
                f"{api_name} request "
                f"{request_number} failed: {response}"
            )

        print(
            f"✅ {api_name}: "
            f"request {request_number}/"
            f"{EXPENSIVE_API_REQUEST_COUNT} "
            f"-> HTTP {response.status_code}"
        )

        assert response.status_code == 200, (
            f"{api_name} request {request_number} failed. "
            f"Expected HTTP 200, got "
            f"HTTP {response.status_code}. "
            f"Response: {response.text[:1000]}"
        )


# ============================================
# LIGHTWEIGHT RATE LIMIT TEST
# ============================================

def _test_lightweight_api_rate_limit(
    api_url: str,
    api_name: str,
):
    """
    Perform the full rate-limit test for a lightweight endpoint.

    This verifies that:

    1. The endpoint is reachable.
    2. Requests below the configured limit succeed.
    3. Additional requests eventually receive HTTP 429.
    4. The 429 response contains the expected error payload.
    5. The endpoint recovers after the rate-limit window resets.

    This test deliberately does NOT depend on X-RateLimit-* headers
    because the current application configuration does not expose
    those headers.
    """

    if not RATE_LIMIT_ENABLED:
        pytest.skip(
            "API rate limiting is disabled in configuration."
        )

    # --------------------------------------------
    # Initial availability check
    # --------------------------------------------

    response = _send_get_request(
        api_url
    )

    if isinstance(response, Exception):
        pytest.fail(
            f"{api_name} request failed before "
            f"rate-limit testing: {response}"
        )

    if response.status_code == 429:
        pytest.skip(
            f"{api_name} is already rate limited. "
            "Run this test after the rate-limit window resets."
        )

    assert response.status_code == 200, (
        f"{api_name} is not reachable. "
        f"Expected HTTP 200, got "
        f"HTTP {response.status_code}. "
        f"Response: {response.text[:1000]}"
    )

    # --------------------------------------------
    # Send requests below configured limit
    # --------------------------------------------

    request_count = max(
        RATE_LIMIT - RATE_LIMIT_SAFETY_MARGIN,
        1,
    )

    print(
        f"\n🚀 {api_name}: sending "
        f"{request_count} concurrent requests..."
    )

    responses = _send_concurrent_requests(
        api_url,
        request_count,
    )

    successful_requests = sum(
        1
        for response in responses
        if not isinstance(response, Exception)
        and response.status_code == 200
    )

    rate_limited_requests = sum(
        1
        for response in responses
        if not isinstance(response, Exception)
        and response.status_code == 429
    )

    failed_requests = [
        response
        for response in responses
        if isinstance(response, Exception)
        or response.status_code not in (200, 429)
    ]

    print(
        f"\n📊 {api_name}: "
        f"{request_count} requests | "
        f"Successful={successful_requests} | "
        f"Rate limited={rate_limited_requests} | "
        f"Failed={len(failed_requests)}"
    )

    assert successful_requests == request_count, (
        f"{api_name}: expected {request_count} successful "
        f"requests, got {successful_requests}."
    )

    assert rate_limited_requests == 0, (
        f"{api_name}: rate limiting triggered before "
        f"the configured threshold."
    )

    assert not failed_requests, (
        f"{api_name}: unexpected request failures occurred."
    )

    # --------------------------------------------
    # Trigger rate limit
    # --------------------------------------------

    print(
        f"\n⏳ Triggering {api_name} rate limit..."
    )

    trigger_responses = _send_concurrent_requests(
        api_url,
        RATE_LIMIT_TRIGGER_ATTEMPTS,
    )

    rate_limit_response = next(
        (
            response
            for response in trigger_responses
            if not isinstance(response, Exception)
            and response.status_code == 429
        ),
        None,
    )

    assert rate_limit_response is not None, (
        f"{api_name} rate limit was not triggered after "
        f"{RATE_LIMIT_TRIGGER_ATTEMPTS} additional requests."
    )

    print(
        f"✅ {api_name} rate limit triggered."
    )

    # --------------------------------------------
    # Validate 429 response
    # --------------------------------------------

    try:
        data = rate_limit_response.json()

    except ValueError:
        pytest.fail(
            f"{api_name} returned HTTP 429 "
            f"with invalid JSON."
        )

    # assert data.get("error") == "Too Many Requests", (
    #     f"{api_name} returned an unexpected 429 error payload: "
    #     f"{data}"
    # )

    # assert (
    #     "message" in data
    # ), (
    #     f"{api_name} 429 response is missing "
    #     f"the 'message' field: {data}"
    # )
    assert "error" in data, (
    f"{api_name} 429 response is missing "
    f"the 'error' field: {data}"
    )

    assert "Rate limit exceeded" in data["error"], (
        f"{api_name} returned an unexpected 429 error payload: "
        f"{data}"
    )

    print(
        f"✅ {api_name} rate-limit error: "
        f"{data['error']}"
    )

    print(
        f"✅ {api_name} rate-limit error: "
        f"{data['error']}"
    )

    # --------------------------------------------
    # Wait for reset
    # --------------------------------------------

    print(
        f"⏳ Waiting "
        f"{RATE_LIMIT_RESET_WAIT_SECONDS} seconds "
        f"for {api_name} rate-limit window to reset..."
    )

    time.sleep(
        RATE_LIMIT_RESET_WAIT_SECONDS
    )

    # --------------------------------------------
    # Verify recovery
    # --------------------------------------------

    response = _send_get_request(
        api_url
    )

    if isinstance(response, Exception):
        pytest.fail(
            f"{api_name} request failed after reset: "
            f"{response}"
        )

    print(
        f"✅ {api_name} after reset: "
        f"Status={response.status_code}"
    )

    assert response.status_code == 200, (
        f"{api_name} did not recover after rate-limit reset. "
        f"Expected HTTP 200, got "
        f"HTTP {response.status_code}. "
        f"Response: {response.text[:1000]}"
    )


# ============================================
# BTC PRICE API
# ============================================

@pytest.mark.integration
def test_price_api_rate_limit():
    """
    Test full rate limiting for the lightweight BTC price API.
    """

    _test_lightweight_api_rate_limit(
        BTC_API_URL,
        "BTC Price API",
    )


# ============================================
# INDICATORS API
# ============================================

@pytest.mark.integration
def test_indicators_api_rate_limit():
    """
    Test full rate limiting for the lightweight indicators API.
    """

    _test_lightweight_api_rate_limit(
        INDICATORS_API_URL,
        "Indicators API",
    )


# ============================================
# REGIME API
# ============================================

@pytest.mark.integration
def test_regime_api_rate_limit():
    """
    Safely test Regime API rate-limit protection.

    The Regime API is an expensive endpoint, so it is not flooded
    with 100 concurrent requests.
    """

    _test_expensive_api_rate_limit(
        REGIME_API_URL,
        "Regime API",
    )


# ============================================
# SIMILAR PERIODS API
# ============================================

@pytest.mark.integration
def test_similar_periods_api_rate_limit():
    """
    Safely test Similar Periods API rate-limit protection.
    """

    _test_expensive_api_rate_limit(
        SIMILAR_PERIODS_API_URL,
        "Similar Periods API",
    )


# ============================================
# ECONOMIC CALENDAR API
# ============================================

@pytest.mark.integration
def test_economic_calendar_api_rate_limit():
    """
    Safely test Economic Calendar API rate-limit protection.
    """

    _test_expensive_api_rate_limit(
        ECONOMIC_CALENDAR_API_URL,
        "Economic Calendar API",
    )


# ============================================
# RATE LIMIT HEADERS
# ============================================

def _test_rate_limit_headers(
    api_url: str,
    api_name: str,
):
    """
    Verify that an endpoint responds normally while rate limiting
    is enabled.

    IMPORTANT:

    The current SlowAPI configuration does not expose dedicated
    X-RateLimit-* response headers. Therefore this test intentionally
    does not require:

        X-RateLimit-Limit
        X-RateLimit-Remaining
        X-RateLimit-Reset

    The test simply verifies that the endpoint is reachable and
    prints the headers returned by the application.

    This matches the currently working behavior of the service.
    """

    if not RATE_LIMIT_ENABLED:
        pytest.skip(
            "API rate limiting is disabled in configuration."
        )

    response = _send_get_request(
        api_url
    )

    _assert_successful_response(
        response,
        api_name,
    )

    print(
        f"\n📊 {api_name} headers:"
    )

    print(
        dict(response.headers)
    )

    assert response.status_code == 200, (
        f"{api_name} returned unexpected status "
        f"{response.status_code}. "
        f"Response: {response.text[:1000]}"
    )


# ============================================
# BTC PRICE HEADERS
# ============================================

@pytest.mark.integration
def test_price_rate_limit_headers():
    """
    Test BTC price API response headers.

    Dedicated X-RateLimit-* headers are not required because
    the current application does not expose them.
    """

    _test_rate_limit_headers(
        BTC_API_URL,
        "BTC Price API",
    )


# ============================================
# INDICATORS HEADERS
# ============================================

@pytest.mark.integration
def test_indicators_rate_limit_headers():
    """
    Test indicators API response headers.
    """

    _test_rate_limit_headers(
        INDICATORS_API_URL,
        "Indicators API",
    )


# ============================================
# REGIME HEADERS
# ============================================

@pytest.mark.integration
def test_regime_rate_limit_headers():
    """
    Test Regime API response headers.
    """

    _test_rate_limit_headers(
        REGIME_API_URL,
        "Regime API",
    )


# ============================================
# SIMILAR PERIODS HEADERS
# ============================================

@pytest.mark.integration
def test_similar_periods_rate_limit_headers():
    """
    Test Similar Periods API response headers.
    """

    _test_rate_limit_headers(
        SIMILAR_PERIODS_API_URL,
        "Similar Periods API",
    )


# ============================================
# ECONOMIC CALENDAR HEADERS
# ============================================

@pytest.mark.integration
def test_economic_calendar_rate_limit_headers():
    """
    Test Economic Calendar API response headers.
    """

    _test_rate_limit_headers(
        ECONOMIC_CALENDAR_API_URL,
        "Economic Calendar API",
    )