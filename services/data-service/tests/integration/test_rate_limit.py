# """
# Integration test for BTC price API rate limiting.
# """

# import requests
# import time
# import pytest

# API_URL = "http://127.0.0.1:8001/api/v1/btc/price"
# RATE_LIMIT = 100


# @pytest.mark.integration
# def test_price_api_rate_limit():
#     """Test that rate limiting works correctly."""

#     # ✅ Check if already rate limited and wait
#     response = requests.get(API_URL)
#     if response.status_code == 429:
#         print("⚠️ Rate limit already exhausted - waiting 65 seconds...")
#         time.sleep(65)

#     # Make requests just under the limit (limit - 5 to be safe)
#     limit = RATE_LIMIT - 5
#     responses = []
#     for i in range(limit):
#         response = requests.get(API_URL)
#         responses.append(response.status_code)
#         # Small delay to avoid flooding
#         time.sleep(0.05)

#     successful_requests = responses.count(200)
#     rate_limited_requests = responses.count(429)

#     print(f"\n✅ {limit} requests - Successful: {successful_requests}, Rate limited: {rate_limited_requests}")

#     # All requests should succeed
#     assert successful_requests == limit
#     assert rate_limited_requests == 0

#     # Now make additional requests to trigger rate limit
#     print("⏳ Making additional requests to trigger rate limit...")
    
#     # Make 10 more requests (total should exceed the limit)
#     for i in range(10):
#         response = requests.get(API_URL)
#         if response.status_code == 429:
#             print(f"✅ Rate limit triggered on request {limit + i + 1}")
#             break
#         time.sleep(0.05)
#     else:
#         # If we never got a 429, try making more requests
#         print("⚠️ Rate limit not triggered yet, making more requests...")
#         for i in range(5):
#             response = requests.get(API_URL)
#             if response.status_code == 429:
#                 print(f"✅ Rate limit triggered on request {limit + i + 1}")
#                 break
#             time.sleep(0.05)
    
#     # Wait for rate limit window to reset (65 seconds)
#     print("⏳ Waiting 65 seconds for rate limit to reset...")
#     time.sleep(65)

#     # Now requests should succeed again
#     response = requests.get(API_URL)
#     print(f"✅ After reset - Status: {response.status_code}")
#     assert response.status_code == 200


# @pytest.mark.integration
# def test_rate_limit_headers():
#     """Test that rate limit headers are present."""
#     response = requests.get(API_URL)

#     if response.status_code == 200:
#         headers = response.headers
#         print(f"📊 Headers: {headers}")

"""
Integration tests for API rate limiting.

Tests rate limiting for:
- BTC price API
- Macroeconomic indicators API
"""

import time

import pytest
import requests

from app.config import settings


BASE_URL = "http://127.0.0.1:8001"

BTC_API_URL = f"{BASE_URL}/api/v1/btc/price"
INDICATORS_API_URL = f"{BASE_URL}/api/v1/indicators"

RATE_LIMIT = settings.RATE_LIMIT_REQUESTS


@pytest.mark.integration
def test_price_api_rate_limit():
    """Test that BTC price API rate limiting works correctly."""

    response = requests.get(BTC_API_URL)

    if response.status_code == 429:
        print(
            "\n⚠️ BTC API rate limit already exhausted - "
            "waiting 65 seconds..."
        )
        time.sleep(65)

    limit = max(RATE_LIMIT - 5, 1)

    responses = []

    for _ in range(limit):
        response = requests.get(BTC_API_URL)
        responses.append(response.status_code)
        time.sleep(0.05)

    successful_requests = responses.count(200)
    rate_limited_requests = responses.count(429)

    print(
        f"\n✅ BTC API: {limit} requests - "
        f"Successful: {successful_requests}, "
        f"Rate limited: {rate_limited_requests}"
    )

    assert successful_requests == limit
    assert rate_limited_requests == 0

    print("⏳ Triggering BTC API rate limit...")

    rate_limit_triggered = False

    for i in range(10):
        response = requests.get(BTC_API_URL)

        if response.status_code == 429:
            print(
                f"✅ BTC rate limit triggered on "
                f"request {limit + i + 1}"
            )
            rate_limit_triggered = True
            break

        time.sleep(0.05)

    assert rate_limit_triggered is True

    print(
        "⏳ Waiting 65 seconds for BTC rate limit "
        "window to reset..."
    )
    time.sleep(65)

    response = requests.get(BTC_API_URL)

    print(
        f"✅ BTC API after reset - "
        f"Status: {response.status_code}"
    )

    assert response.status_code == 200



@pytest.mark.integration
def test_indicators_api_rate_limit():
    """Test that indicators API rate limiting works correctly."""

    response = requests.get(INDICATORS_API_URL)

    if response.status_code == 429:
        print(
            "\n⚠️ Indicators API rate limit already exhausted - "
            "waiting 65 seconds..."
        )
        time.sleep(65)

    limit = max(RATE_LIMIT - 5, 1)

    responses = []

    for _ in range(limit):
        response = requests.get(INDICATORS_API_URL)
        responses.append(response.status_code)
        time.sleep(0.05)

    successful_requests = responses.count(200)
    rate_limited_requests = responses.count(429)

    print(
        f"\n✅ Indicators API: {limit} requests - "
        f"Successful: {successful_requests}, "
        f"Rate limited: {rate_limited_requests}"
    )

    assert successful_requests == limit
    assert rate_limited_requests == 0

    print("⏳ Triggering indicators API rate limit...")

    rate_limit_triggered = False
    rate_limit_response = None

    for i in range(10):
        response = requests.get(INDICATORS_API_URL)

        if response.status_code == 429:
            print(
                f"✅ Indicators rate limit triggered on "
                f"request {limit + i + 1}"
            )
            rate_limit_triggered = True
            rate_limit_response = response
            break

        time.sleep(0.05)

    assert rate_limit_triggered is True
    assert rate_limit_response is not None

    data = rate_limit_response.json()

    assert "error" in data
    assert "Rate limit exceeded" in data["error"]

    print(
        f"✅ Rate limit error: {data['error']}"
    )

    print(
        "⏳ Waiting 65 seconds for indicators rate limit "
        "window to reset..."
    )
    time.sleep(65)

    response = requests.get(INDICATORS_API_URL)

    print(
        f"✅ Indicators API after reset - "
        f"Status: {response.status_code}"
    )

    assert response.status_code == 200

@pytest.mark.integration
def test_price_rate_limit_headers():
    """Test that BTC API returns its response headers."""

    response = requests.get(BTC_API_URL)

    if response.status_code == 200:
        headers = response.headers
        print(f"\n📊 BTC API headers: {headers}")


@pytest.mark.integration
def test_indicators_rate_limit_headers():
    """Test that indicators API returns its response headers."""

    response = requests.get(INDICATORS_API_URL)

    if response.status_code == 200:
        headers = response.headers
        print(f"\n📊 Indicators API headers: {headers}")