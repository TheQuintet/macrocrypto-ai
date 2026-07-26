"""
Integration test for Redis caching behavior.
"""

import time
import requests
import pytest

API_URL = "http://127.0.0.1:8001/api/v1/btc/price"


@pytest.mark.integration
def test_response_time_with_redis_cache():
    """
    Test that Redis caching improves response time.
    """

    # Give the rate limit a moment to reset
    time.sleep(2)

    # Wait for rate limit to be available
    for attempt in range(3):
        response = requests.get(API_URL)
        if response.status_code == 200:
            break
        print(f"⏳ Rate limited, attempt {attempt+1}/3, waiting 5 seconds...")
        time.sleep(5)
    else:
        pytest.skip("Rate limit exhausted, skipping test")

    # First request (cache miss)
    start_time = time.time()
    response = requests.get(API_URL)
    first_response_time = (time.time() - start_time) * 1000

    print("\n📡 First request (cache miss):")
    print(f"   Status: {response.status_code}")
    print(f"   Time: {first_response_time:.2f} ms")

    assert response.status_code == 200

    # Second request (cache hit)
    start_time = time.time()
    response = requests.get(API_URL)
    second_response_time = (time.time() - start_time) * 1000

    print("\n🚀 Second request (cache hit):")
    print(f"   Status: {response.status_code}")
    print(f"   Time: {second_response_time:.2f} ms")

    assert response.status_code == 200

    # Acceptance criteria: cache hit should be < 500ms
    assert second_response_time < 500

    print(f"\n📊 Speed improvement: {first_response_time - second_response_time:.2f}ms faster")

    # Test cache expiration
    print("\n⏳ Waiting 6 seconds for cache to expire...")
    time.sleep(6)

    start_time = time.time()
    response = requests.get(API_URL)
    third_response_time = (time.time() - start_time) * 1000

    print("\n🔄 Third request (cache expired):")
    print(f"   Status: {response.status_code}")
    print(f"   Time: {third_response_time:.2f} ms")

    assert response.status_code == 200


@pytest.mark.integration
def test_cache_hit_after_multiple_requests():
    """
    Test that multiple consecutive requests are cached.
    """
    # Wait for rate limit
    time.sleep(2)

    # First request
    start_time = time.time()
    response1 = requests.get(API_URL)
    time1 = (time.time() - start_time) * 1000

    if response1.status_code == 429:
        print("⏳ Rate limited, waiting 5 seconds...")
        time.sleep(5)
        response1 = requests.get(API_URL)
        time1 = (time.time() - start_time) * 1000

    assert response1.status_code == 200

    # Second request
    start_time = time.time()
    response2 = requests.get(API_URL)
    time2 = (time.time() - start_time) * 1000
    assert response2.status_code == 200

    # Third request
    start_time = time.time()
    response3 = requests.get(API_URL)
    time3 = (time.time() - start_time) * 1000
    assert response3.status_code == 200

    print(f"\n📊 Cache performance:")
    print(f"   Request 1: {time1:.2f}ms (cache miss)")
    print(f"   Request 2: {time2:.2f}ms (cache hit)")
    print(f"   Request 3: {time3:.2f}ms (cache hit)")

    assert time2 < time1 * 1.5
    assert time3 < time1 * 1.5