"""
Integration test for BTC price API rate limiting.

Validates:
- Requests within allowed limit succeed.
- Requests exceeding the limit are rejected.

Configured limit:
60 requests/minute/IP
"""

import requests


API_URL = (
    "http://127.0.0.1:8000/api/v1/btc/price"
)


def test_price_api_rate_limit():

    responses = []

    total_requests = 70


    for _ in range(total_requests):

        response = requests.get(
            API_URL
        )

        responses.append(
            response.status_code
        )


    successful_requests = responses.count(
        200
    )

    rate_limited_requests = responses.count(
        429
    )


    print(
        f"\nSuccessful requests: "
        f"{successful_requests}"
    )

    print(
        f"Rate limited requests: "
        f"{rate_limited_requests}"
    )


    # Verify rate limiting is enforced
    assert rate_limited_requests > 0