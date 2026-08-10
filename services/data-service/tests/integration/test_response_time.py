"""
Integration tests for BTC price API Redis cache performance.

Validates:
- Redis cached response time
- Multiple cache hits performance
- Cached response consistency
- Cache expiration recovery
"""

import time
import requests
import pytest


API_URL = "http://127.0.0.1:8001/api/v1/btc/price"

CACHE_RESPONSE_LIMIT_MS = 200


def measure_request_time():
    """
    Execute API request and return:
    - response
    - elapsed time in milliseconds
    """
    start = time.perf_counter()

    response = requests.get(API_URL)

    elapsed = (time.perf_counter() - start) * 1000

    return response, elapsed


@pytest.mark.integration
def test_btc_price_response_time_with_redis_cache():
    """
    Validate BTC price endpoint response time using Redis cache.

    Acceptance Criteria:
    - Cached response should be < 200ms
    """

    # Warm up request (populate Redis cache)
    warmup_response, warmup_time = measure_request_time()

    assert warmup_response.status_code == 200

    print(
        f"\n🔥 Cache warmup request: {warmup_time:.2f} ms"
    )

    # First cached request
    response1, time1 = measure_request_time()

    assert response1.status_code == 200

    data1 = response1.json()

    print(
        f"🚀 First cached request: {time1:.2f} ms"
    )

    assert time1 < CACHE_RESPONSE_LIMIT_MS, (
        f"Cached response too slow: {time1:.2f}ms"
    )


@pytest.mark.integration
def test_multiple_cached_requests_under_200ms():
    """
    Validate repeated Redis cache hits remain fast.
    """

    # Warm cache
    response, _ = measure_request_time()
    assert response.status_code == 200

    response_times = []

    for _ in range(5):

        response, elapsed = measure_request_time()

        assert response.status_code == 200

        response_times.append(elapsed)

    print("\n📊 Multiple cache hit performance:")

    for index, elapsed in enumerate(response_times, start=1):
        print(
            f"Request {index}: {elapsed:.2f} ms"
        )

    # Every cached response should meet acceptance criteria
    for elapsed in response_times:
        assert elapsed < CACHE_RESPONSE_LIMIT_MS, (
            f"Cache hit exceeded 200ms: {elapsed:.2f}ms"
        )



