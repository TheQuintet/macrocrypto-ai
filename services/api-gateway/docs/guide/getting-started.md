```markdown
# Getting Started with MacroCrypto AI API

Welcome to the MacroCrypto AI API Gateway. This guide will help you get started with using the API.

## Base URL

All API endpoints are accessible at:

```
http://localhost:8000/api/v1
```

For production:
```
https://api.macrocrypto.ai/api/v1
```

## Quick Start

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type": application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 3. Use the Access Token

Include the token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token

When your access token expires (after 15 minutes), use the refresh token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Token Lifecycle

| Token | Expiry | Purpose |
|-------|--------|---------|
| Access Token | 15 minutes | Authorize API requests |
| Refresh Token | 7 days | Obtain new access tokens |

### Authentication Flow

1. **Register** a new user account
2. **Login** to receive access and refresh tokens
3. **Include** the access token in all API requests
4. **Refresh** when the access token expires

## Rate Limits

| Role | Requests per Minute |
|------|---------------------|
| Guest | 10 |
| User | 100 |
| Admin | 1000 |

Rate limit headers are included in every response:
- `X-RateLimit-Limit`: Max requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time until limit resets

## Quick Examples

### Get BTC Price

```bash
curl -X GET "http://localhost:8000/api/v1/btc/prices?limit=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get BTC Predictions

```bash
curl -X GET "http://localhost:8000/api/v1/predict/btc?horizon=24h" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Trade Recommendations

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/btc?timeframe=24h&risk_level=moderate" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Export Data

```bash
curl -o predictions.csv \
  "http://localhost:8000/api/v1/export?export_type=predictions&format=csv&timeframe=24h" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## WebSocket Connection

Connect to receive real-time price updates:

```bash
wscat -c "ws://localhost:8000/ws?token=YOUR_TOKEN"
```

Once connected, you will receive:

```json
{
  "type": "connection",
  "status": "connected",
  "message": "Connected to MacroCrypto AI WebSocket",
  "timestamp": "..."
}
```

And periodic price updates:

```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTC",
    "price": 45000.00,
    "change_24h_percent": 2.5,
    "volume": 1500000.00,
    "timestamp": "..."
  },
  "timestamp": "..."
}
```

## Error Handling

### Common Errors

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Missing or invalid token |
| 429 | Too Many Requests - Rate limit exceeded |
| 503 | Service Unavailable - Downstream service down |

### Example Error Response

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

### Handling Rate Limits

```python
import time

def handle_rate_limit(response):
    if response.status_code == 429:
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        wait_time = max(0, reset_time - time.time()) + 1
        time.sleep(wait_time)
        return True
    return False
```

## Python Quick Start

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "johndoe",
    "password": "SecurePass123!"
})
token = response.json()["access_token"]

# Get predictions
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/predict/btc", params={
    "horizon": "24h"
}, headers=headers)

print(response.json())
```

## JavaScript Quick Start

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// Login
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    username: "johndoe",
    password: "SecurePass123!"
  })
});
const { access_token } = await loginResponse.json();

// Get predictions
const response = await fetch(`${BASE_URL}/predict/btc?horizon=24h`, {
  headers: { "Authorization": `Bearer ${access_token}` }
});
const data = await response.json();
console.log(data);
```

## Next Steps

- Explore all endpoints at `/docs`
- Read the [Authentication Guide](./authentication.md)
- Check [Rate Limiting](./rate-limiting.md)
- See [Error Handling](./error-handling.md)
- Learn about [WebSocket](./websocket.md)

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Need Help?

If you have questions or issues, please contact the MacroCrypto AI support team.
```