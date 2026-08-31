```markdown
# Rate Limiting Guide

This guide explains the rate limiting system in the MacroCrypto AI API.

## Overview

Rate limiting protects the API from abuse and ensures fair usage for all users. Each client is identified by:

1. **User ID** (authenticated users)
2. **API Key** (optional, future feature)
3. **IP Address** (guest users)

## Rate Limits

| Role | Requests per Minute | Use Case |
|------|---------------------|----------|
| **Guest** | 10 | Unauthenticated users, testing |
| **User** | 100 | Standard authenticated users |
| **Admin** | 1000 | Administrative users |

## Rate Limit Headers

Every response includes rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1688754321
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the current window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Timestamp when the limit resets (Unix epoch) |

## Rate Limit Exceeded

When you exceed your rate limit, the API returns:

**Status Code:** `429 Too Many Requests`

**Response:**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1688754321
Retry-After: 30
```

## Best Practices

### 1. Handle Rate Limit Errors

```python
import time

def make_request_with_retry(url, headers, max_retries=3):
    for i in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            # Wait for reset time + 1 second
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(0, reset_time - time.time()) + 1
            time.sleep(wait_time)
            continue
        return response
    return None
```

### 2. Monitor Rate Limit Headers

```python
def check_rate_limits(response):
    limit = response.headers.get('X-RateLimit-Limit')
    remaining = response.headers.get('X-RateLimit-Remaining')
    reset = response.headers.get('X-RateLimit-Reset')
    
    print(f"Limit: {limit}, Remaining: {remaining}, Reset: {reset}")
    
    if int(remaining) < 10:
        print("⚠️  Rate limit is low, slow down requests")
```

### 3. Distribute Requests

For bulk operations, spread requests over time:

```python
import time

def bulk_request(items):
    for i, item in enumerate(items):
        # Request with 1-second delay between requests
        time.sleep(1)
        make_request(item)
```

### 4. Cache Responses

Use the `cached` flag in responses to know when to cache:

```json
{
  "data": {...},
  "cached": true
}
```

## Which Endpoints Are Rate Limited?

All API endpoints are rate limited except:
- `/health` - Health checks
- `/ready` - Readiness probes
- `/docs` - API documentation
- `/redoc` - API documentation
- `/openapi.json` - OpenAPI schema

## Rate Limit Configuration

Rate limits can be configured via environment variables:

```bash
RATE_LIMIT_GUEST=10
RATE_LIMIT_USER=100
RATE_LIMIT_ADMIN=1000
```

## Rate Limit Reset

Rate limits reset at the end of the time window. The `X-RateLimit-Reset` header tells you exactly when.

**Example:**
```python
import time

def wait_for_reset(response):
    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
    current_time = int(time.time())
    if reset_time > current_time:
        time.sleep(reset_time - current_time + 1)
```

## Rate Limit Exceeded Example

```bash
# Make 11 requests as a guest (limit is 10)
for i in {1..11}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://localhost:8000/api/v1/btc/prices?limit=1
done

# Last request returns 429
```

## Rate Limit Headers Example

```bash
curl -v http://localhost:8000/api/v1/btc/prices?limit=1 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response headers:
# < X-RateLimit-Limit: 100
# < X-RateLimit-Remaining: 99
# < X-RateLimit-Reset: 1688754321
```

## Python Example with Rate Limit Handling

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def make_api_request(endpoint, access_token, params=None, max_retries=5):
    """
    Make an API request with automatic rate limit handling.
    """
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=params)
        
        # Success
        if response.status_code == 200:
            return response.json()
        
        # Rate limit exceeded
        if response.status_code == 429:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(0, reset_time - time.time()) + 1
            print(f"⚠️  Rate limit exceeded. Waiting {wait_time:.0f} seconds...")
            time.sleep(wait_time)
            continue
        
        # Other errors
        print(f"❌ Error {response.status_code}: {response.text}")
        return None
    
    print("❌ Max retries exceeded")
    return None

# Usage
token = "YOUR_ACCESS_TOKEN"
result = make_api_request("predict/btc", token, params={"horizon": "24h"})
```

## cURL Rate Limit Monitoring

```bash
# Make requests and monitor rate limit headers
for i in {1..5}; do
  echo "=== Request $i ==="
  curl -s -D - -o /dev/null \
    "http://localhost:8000/api/v1/btc/prices?limit=1" \
    -H "Authorization: Bearer $TOKEN" \
    | grep -E "X-RateLimit|HTTP"
  echo ""
  sleep 1
done
```

## Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

## Rate Limit Headers Table

| Header | Type | Description |
|--------|------|-------------|
| `X-RateLimit-Limit` | Integer | Maximum requests allowed |
| `X-RateLimit-Remaining` | Integer | Requests remaining |
| `X-RateLimit-Reset` | Unix Timestamp | Reset time |

## Common Questions

### Q: What happens if I exceed the rate limit?

A: You will receive a `429 Too Many Requests` response. Wait for the `Retry-After` time before trying again.

### Q: How is my client identified?

A: In order of priority: User ID > API Key > IP Address.

### Q: Does WebSocket have rate limits?

A: No, the WebSocket endpoint is not rate limited.

### Q: Can I increase my rate limit?

A: Rate limits are based on your role. Contact support for higher limits.
```