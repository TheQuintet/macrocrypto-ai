"""
Integration test for Redis caching behavior.

Validates:
- API endpoint response
- Redis cache hit performance
- Cached response time requirement (<200ms)
"""

import time
import requests


API_URL = "http://127.0.0.1:8000/api/v1/btc/price"


def test_response_time_with_redis_cache():

    # -----------------------------
    # First request
    # Expected:
    # - Cache miss
    # - Data retrieved from PriceService
    # - Response stored in Redis
    # -----------------------------

    start_time = time.time()

    response = requests.get(
        API_URL
    )

    first_response_time = (
        time.time() - start_time
    ) * 1000


    print("\nFirst request:")
    print(
        f"Status: {response.status_code}"
    )
    print(
        f"Time: {first_response_time:.2f} ms"
    )


    assert response.status_code == 200


    # -----------------------------
    # Second request
    # Expected:
    # - Data retrieved from Redis cache
    # - Faster response time
    # -----------------------------

    start_time = time.time()

    response = requests.get(
        API_URL
    )

    second_response_time = (
        time.time() - start_time
    ) * 1000


    print(
        "\nSecond request (Redis expected):"
    )

    print(
        f"Status: {response.status_code}"
    )

    print(
        f"Time: {second_response_time:.2f} ms"
    )


    assert response.status_code == 200

    # T4.6 acceptance criteria
    assert second_response_time < 200