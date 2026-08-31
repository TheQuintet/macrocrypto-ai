```markdown
# Error Handling Guide

This guide explains the error handling system in the MacroCrypto AI API.

## Error Response Format

All error responses follow a consistent JSON format:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

For validation errors, additional details are provided:

```json
{
  "detail": "Request validation failed",
  "errors": [
    {
      "field": "body.password",
      "message": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

## HTTP Status Codes

| Code | Name | Description |
|------|------|-------------|
| **200** | OK | Request succeeded |
| **201** | Created | Resource created successfully |
| **400** | Bad Request | Invalid parameters or request format |
| **401** | Unauthorized | Missing or invalid authentication token |
| **403** | Forbidden | Insufficient permissions |
| **404** | Not Found | Resource not found |
| **422** | Unprocessable Entity | Validation error |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server-side error |
| **503** | Service Unavailable | Downstream service unavailable |
| **504** | Gateway Timeout | Downstream service timeout |

## Common Errors

### 401 Unauthorized

**Cause:** Missing or invalid token

**Response:**
```json
{
  "detail": "Not authenticated"
}
```

**Solution:** Include a valid JWT token in the `Authorization` header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 403 Forbidden

**Cause:** Insufficient permissions

**Response:**
```json
{
  "detail": "Admin privileges required"
}
```

**Solution:** Use an account with higher permissions.

### 404 Not Found

**Cause:** Resource doesn't exist or route is incorrect

**Response:**
```json
{
  "detail": "Not Found"
}
```

**Solution:** Check the URL and resource ID.

### 422 Validation Error

**Cause:** Request validation failed

**Response:**
```json
{
  "detail": "Request validation failed",
  "errors": [
    {
      "field": "body.email",
      "message": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Solution:** Fix the validation errors in your request.

### 429 Too Many Requests

**Cause:** Rate limit exceeded

**Response:**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

**Solution:** Wait for the rate limit to reset. Check the `Retry-After` header.

### 503 Service Unavailable

**Cause:** Downstream service is unavailable

**Response:**
```json
{
  "detail": "AI Service unavailable: 503"
}
```

**Solution:** Try again later or check service status.

### 504 Gateway Timeout

**Cause:** Downstream service timed out

**Response:**
```json
{
  "detail": "AI Service request timed out"
}
```

**Solution:** Try again later with a smaller request.

## Error Handling Best Practices

### 1. Check Status Code First

```python
def handle_response(response):
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit exceeded")
        return None
    elif response.status_code == 503:
        print("Service unavailable, retrying...")
        return None
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None
```

### 2. Parse Error Details

```python
def parse_error(response):
    try:
        error = response.json()
        if "errors" in error:
            for e in error["errors"]:
                print(f"Field: {e['field']}")
                print(f"Message: {e['message']}")
        else:
            print(f"Error: {error.get('detail', 'Unknown error')}")
    except:
        print(f"Error: {response.text}")
```

### 3. Retry with Exponential Backoff

```python
import time
import random

def request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code in [200, 201]:
            return response
        
        if response.status_code == 429:
            wait_time = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait_time)
            continue
        
        if response.status_code in [503, 504]:
            wait_time = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait_time)
            continue
        
        return response
    
    return None
```

### 4. Log Errors

```python
import logging

logger = logging.getLogger(__name__)

def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"API Error {response.status_code}: {response.text}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None
```

## Example: Handling Errors in Python

```python
def get_predictions_with_error_handling(access_token):
    url = "http://localhost:8000/api/v1/predict/btc"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"horizon": "24h"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("Token expired, refreshing...")
            # Refresh token logic here
        elif response.status_code == 429:
            print("Rate limit exceeded, waiting...")
            time.sleep(60)
            return get_predictions_with_error_handling(access_token)
        elif response.status_code == 503:
            print("Service unavailable, retrying...")
            time.sleep(5)
            return get_predictions_with_error_handling(access_token)
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
```

## Error Codes Quick Reference

| Code | Name | When It Happens |
|------|------|-----------------|
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Downstream service down |
| 504 | Gateway Timeout | Downstream service timeout |

## Error Response Fields

| Field | Description |
|-------|-------------|
| `detail` | Human-readable error description |
| `errors` | Optional list of validation errors |
| `errors[].field` | Field that caused the error |
| `errors[].message` | Specific error message |
| `errors[].type` | Error type identifier |

## Example Error Scenarios

### Invalid Request Parameters

```bash
curl "http://localhost:8000/api/v1/predict/btc?horizon=invalid" \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "detail": "Request validation failed",
  "errors": [
    {
      "field": "query.horizon",
      "message": "String should match pattern '^(24h|7d)$'",
      "type": "string_pattern_mismatch"
    }
  ]
}
```

### Missing Token

```bash
curl "http://localhost:8000/api/v1/auth/me"
```

Response:
```json
{
  "detail": "Not authenticated"
}
```

### Invalid Token

```bash
curl "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer invalid_token"
```

Response:
```json
{
  "detail": "Could not validate credentials: Not enough segments"
}
```

### Resource Not Found

```bash
curl "http://localhost:8000/api/v1/export/999/download" \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "detail": "Export not found"
}
```

## Error Handling with cURL

```bash
# Check status code only
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://localhost:8000/api/v1/health"

# Get full response with error details
curl -s "http://localhost:8000/api/v1/predict/btc?horizon=invalid" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Error Recovery Strategies

### 1. Retry with Backoff

```python
def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = func()
            if result:
                return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)
    return None
```

### 2. Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, max_failures=3, timeout=60):
        self.max_failures = max_failures
        self.timeout = timeout
        self.failures = 0
        self.last_failure = 0
        
    def is_open(self):
        if self.failures >= self.max_failures:
            if time.time() - self.last_failure > self.timeout:
                self.failures = 0
                return False
            return True
        return False
    
    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
    
    def record_success(self):
        self.failures = 0
```
```