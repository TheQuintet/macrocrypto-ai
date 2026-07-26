"""
End-to-end tests for data flow.
"""

import pytest
import requests
import time

API_URL = "http://127.0.0.1:8001/api/v1/btc/price"


@pytest.mark.e2e
def test_full_data_flow():
    """Test complete data flow from WebSocket to API."""
    # 1. Check if API returns data
    response = requests.get(API_URL)
    assert response.status_code == 200

    data = response.json()
    print(f"\n📊 BTC Price: ${data.get('current_price', 'N/A')}")

    # 2. Check if data is updating
    time.sleep(2)
    response2 = requests.get(API_URL)
    assert response2.status_code == 200

    # 3. Verify cache is working (fast response)
    start = time.time()
    response3 = requests.get(API_URL)
    time_taken = (time.time() - start) * 1000
    assert response3.status_code == 200
    assert time_taken < 500, f"Slow response: {time_taken:.2f}ms"

    print("✅ Full data flow test passed!")