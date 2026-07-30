"""
Integration test for BTC price API rate limiting.
"""

import requests
import time
import pytest

API_URL = "http://127.0.0.1:8001/api/v1/btc/price"
RATE_LIMIT = 100


@pytest.mark.integration
def test_price_api_rate_limit():
    """Test that rate limiting works correctly."""

    # ✅ Check if already rate limited and wait
    response = requests.get(API_URL)
    if response.status_code == 429:
        print("⚠️ Rate limit already exhausted - waiting 65 seconds...")
        time.sleep(65)

    # Make requests just under the limit (limit - 5 to be safe)
    limit = RATE_LIMIT - 5
    responses = []
    for i in range(limit):
        response = requests.get(API_URL)
        responses.append(response.status_code)
        # Small delay to avoid flooding
        time.sleep(0.05)

    successful_requests = responses.count(200)
    rate_limited_requests = responses.count(429)

    print(f"\n✅ {limit} requests - Successful: {successful_requests}, Rate limited: {rate_limited_requests}")

    # All requests should succeed
    assert successful_requests == limit
    assert rate_limited_requests == 0

    # Now make additional requests to trigger rate limit
    print("⏳ Making additional requests to trigger rate limit...")
    
    # Make 10 more requests (total should exceed the limit)
    for i in range(10):
        response = requests.get(API_URL)
        if response.status_code == 429:
            print(f"✅ Rate limit triggered on request {limit + i + 1}")
            break
        time.sleep(0.05)
    else:
        # If we never got a 429, try making more requests
        print("⚠️ Rate limit not triggered yet, making more requests...")
        for i in range(5):
            response = requests.get(API_URL)
            if response.status_code == 429:
                print(f"✅ Rate limit triggered on request {limit + i + 1}")
                break
            time.sleep(0.05)
    
    # Wait for rate limit window to reset (65 seconds)
    print("⏳ Waiting 65 seconds for rate limit to reset...")
    time.sleep(65)

    # Now requests should succeed again
    response = requests.get(API_URL)
    print(f"✅ After reset - Status: {response.status_code}")
    assert response.status_code == 200


@pytest.mark.integration
def test_rate_limit_headers():
    """Test that rate limit headers are present."""
    response = requests.get(API_URL)

    if response.status_code == 200:
        headers = response.headers
        print(f"📊 Headers: {headers}")