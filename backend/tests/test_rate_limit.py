"""
Integration test for BTC price API rate limiting.

Validates:
- Requests within allowed limit succeed.
- Requests exceeding the limit are rejected.

Configured limit:
60 requests/minute/IP
"""

import requests
import time

API_URL = "http://127.0.0.1:8000/api/v1/btc/price"


def test_price_api_rate_limit():
    """Test that rate limiting works correctly."""
    
    # Check if we're already rate limited
    response = requests.get(API_URL)
    if response.status_code == 429:
        print("⚠️ Rate limit already exhausted - waiting 61 seconds...")
        time.sleep(61)
    
    # Make exactly 59 requests (just under the limit) - should all succeed
    responses = []
    for i in range(59):
        response = requests.get(API_URL)
        responses.append(response.status_code)
    
    successful_requests = responses.count(200)
    rate_limited_requests = responses.count(429)
    
    print(f"\n✅ 59 requests - Successful: {successful_requests}, Rate limited: {rate_limited_requests}")
    
    # All 59 requests should succeed
    assert successful_requests == 59
    assert rate_limited_requests == 0
    
    # Now make the 60th request - should be rate limited
    response = requests.get(API_URL)
    print(f"✅ 60th request - Status: {response.status_code}")
    
    # The 60th request should be rate limited (429)
    assert response.status_code == 429
    
    # Wait 61 seconds for rate limit window to reset
    print("⏳ Waiting 61 seconds for rate limit to reset...")
    time.sleep(61)
    
    # Now requests should succeed again
    response = requests.get(API_URL)
    print(f"✅ After reset - Status: {response.status_code}")
    assert response.status_code == 200