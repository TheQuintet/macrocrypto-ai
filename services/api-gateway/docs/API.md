# MacroCrypto AI API Documentation

## Overview

The MacroCrypto AI API Gateway provides REST API endpoints for BTC traders, investment analysts, and platform users. It offers AI-powered predictions, market data, trade recommendations, and real-time price updates via WebSocket.

**Base URL:** `http://localhost:8000/api/v1`

**Interactive Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limits](#rate-limits)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Authentication](#authentication-endpoints)
   - [Predictions](#predictions-endpoints)
   - [Market Data](#market-data-endpoints)
   - [Recommendations](#recommendations-endpoints)
   - [Exports](#exports-endpoints)
   - [WebSocket](#websocket)
5. [Examples](#examples)
   - [Python](#python-examples)
   - [cURL](#curl-examples)

---

## Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Token Lifecycle

| Token | Expiry | Purpose |
|-------|--------|---------|
| Access Token | 15 minutes | Authorize API requests |
| Refresh Token | 7 days | Obtain new access tokens |

### Endpoints

#### Register User

**POST** `/api/v1/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "status": "pending",
  "is_email_verified": false,
  "created_at": "2026-08-28T..."
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 400 | Email already registered, username taken, or invalid input |
| 422 | Validation error (e.g., weak password) |

#### Login

**POST** `/api/v1/auth/login`

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error Responses:**
| Code | Description |
|------|-------------|
| 401 | Invalid username or password |
| 403 | Account is pending, inactive, or suspended |

#### Refresh Token

**POST** `/api/v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Get Current User

**GET** `/api/v1/auth/me`

**Headers:** `Authorization: Bearer YOUR_ACCESS_TOKEN`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "status": "active",
  "is_email_verified": true,
  "created_at": "2026-08-28T..."
}
```

#### Change Password

**POST** `/api/v1/auth/change-password`

**Headers:** `Authorization: Bearer YOUR_ACCESS_TOKEN`

**Request:**
```json
{
  "current_password": "SecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

#### Logout

**POST** `/api/v1/auth/logout`

**Headers:** `Authorization: Bearer YOUR_ACCESS_TOKEN`

---

## Rate Limits

### Limits by Role

| Role | Requests per Minute |
|------|---------------------|
| Guest | 10 |
| User | 100 |
| Admin | 1000 |

### Rate Limit Headers

Every response includes these headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Requests remaining |
| `X-RateLimit-Reset` | Timestamp when limit resets |

### Rate Limit Exceeded

**Status:** `429 Too Many Requests`

**Response:**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message explaining what went wrong"
}
```

**Validation Errors:**
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

### HTTP Status Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Downstream service down |
| 504 | Gateway Timeout | Downstream service timeout |

---

## Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user |
| POST | `/auth/logout` | Logout |
| POST | `/auth/change-password` | Change password |

### Predictions Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predict/btc` | BTC predictions (24h/7d) |
| GET | `/predict/btc/accuracy` | Prediction accuracy metrics |

#### GET /predict/btc

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `horizon` | string | `24h` | `24h` or `7d` |
| `model_type` | string | `ensemble` | `ensemble`, `lstm`, `transformer` |

**Response:**
```json
{
  "symbol": "BTC",
  "timeframe": "24h",
  "model_type": "ensemble",
  "current_price": 45000.00,
  "change_percent": 2.5,
  "trend_direction": "up",
  "predictions": [
    {
      "timestamp": "2026-08-28T...",
      "price": 45100.00,
      "lower_bound": 44800.00,
      "upper_bound": 45400.00,
      "confidence": 0.85
    }
  ],
  "timestamp": "2026-08-28T...",
  "cached": false
}
```

#### GET /predict/btc/accuracy

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | `30` | Days to analyze (1-365) |

**Response:**
```json
{
  "symbol": "BTC",
  "days": 30,
  "overall_accuracy": 85.5,
  "rmse": 125.30,
  "mae": 98.75,
  "mape": 2.1,
  "predictions_count": 720,
  "market_condition_breakdown": {
    "bull": {"accuracy": 88.0, "count": 240},
    "bear": {"accuracy": 82.0, "count": 240},
    "sideways": {"accuracy": 86.5, "count": 240}
  },
  "threshold_warning": false
}
```

### Market Data Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/btc/prices` | Historical BTC prices |
| GET | `/indicators` | Macroeconomic indicators |
| GET | `/correlation/btc` | BTC-macro correlation |
| GET | `/regimes/btc` | Market regime data |

#### GET /btc/prices

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | - | ISO 8601 date |
| `end_date` | string | - | ISO 8601 date |
| `limit` | int | `100` | Records per page (max 1000) |
| `offset` | int | `0` | Pagination offset |

**Response:**
```json
{
  "symbol": "BTC",
  "prices": [
    {
      "timestamp": "2026-08-28T...",
      "price": 45000.00,
      "volume": 1500000.00,
      "market_cap": 855000000000.00
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0,
  "timestamp": "2026-08-28T...",
  "cached": false
}
```

#### GET /indicators

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `indicators` | string | - | Comma-separated list (e.g., `GDP,Inflation`) |

**Response:**
```json
{
  "indicators": {
    "GDP": {
      "value": 28.78,
      "previous": 28.52,
      "change_percent": 0.91,
      "source": "BEA",
      "unit": "trillion USD"
    },
    "Inflation": {
      "value": 3.2,
      "previous": 3.5,
      "change_percent": -8.57,
      "source": "BLS",
      "unit": "percent"
    }
  },
  "timestamp": "2026-08-28T...",
  "cached": false
}
```

#### GET /correlation/btc

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `window` | string | `30d` | `30d`, `90d`, `1y` |

**Response:**
```json
{
  "symbol": "BTC",
  "window": "30d",
  "days": 30,
  "correlations": {
    "S&P 500": {"value": 0.65, "strength": "moderate"},
    "DXY": {"value": -0.45, "strength": "moderate"},
    "Gold": {"value": 0.35, "strength": "weak"}
  },
  "timestamp": "2026-08-28T...",
  "cached": false
}
```

#### GET /regimes/btc

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | string | `1w` | `1w`, `1m`, `3m` |

**Response:**
```json
{
  "symbol": "BTC",
  "timeframe": "1w",
  "regimes": [
    {
      "regime_type": "bull",
      "start_date": "2026-07-28T...",
      "end_date": "2026-08-28T...",
      "duration_days": 30,
      "avg_return": 12.5,
      "max_drawdown": -3.2,
      "volatility": 18.5,
      "sharpe_ratio": 2.1
    }
  ],
  "current_regime": {
    "regime_type": "bull",
    "start_date": "2026-07-28T...",
    "duration_days": 30,
    "avg_return": 12.5
  },
  "timestamp": "2026-08-28T...",
  "cached": false
}
```

### Recommendations Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recommendations/btc` | Trade recommendations |

#### GET /recommendations/btc

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | string | `24h` | `24h` or `7d` |
| `risk_level` | string | `moderate` | `low`, `moderate`, `high` |

**Response:**
```json
{
  "symbol": "BTC",
  "timeframe": "24h",
  "risk_level": "moderate",
  "recommendation": {
    "recommendation": "BUY",
    "confidence": 0.85,
    "entry_price": 45000.00,
    "stop_loss": 43650.00,
    "take_profit": 47700.00,
    "risk_level": "moderate",
    "risk_reward_ratio": 2.0,
    "time_horizon": "24h",
    "explanation": "Based on 24h predictions showing up trend...",
    "historical_accuracy": 0.88
  },
  "timestamp": "2026-08-28T...",
  "cached": false
}
```

### Exports Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/export` | Export data |
| GET | `/export/history` | Get export history |
| GET | `/export/{id}/download` | Download previous export |

#### GET /export

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `export_type` | string | `predictions`, `accuracy`, `correlations`, `regimes` |
| `format` | string | `csv`, `png`, `pdf` |
| `timeframe` | string | `24h`, `7d`, `1w`, `1m` |
| `symbol` | string | Trading symbol (default: BTC) |
| `days` | int | Days for accuracy (1-365) |
| `window` | string | `30d`, `90d`, `1y` |
| `model_type` | string | `ensemble`, `lstm`, `transformer` |

**Response:** The exported file (CSV, PNG, or PDF)

**Headers:**
```
Content-Disposition: attachment; filename=predictions_BTC_24h_20260828_120000.csv
X-Export-ID: 1
```

#### GET /export/history

**Response:**
```json
{
  "total": 3,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": 1,
      "export_type": "predictions",
      "format": "csv",
      "file_name": "predictions_BTC_24h_20260828_120000.csv",
      "file_size": 1633,
      "status": "completed",
      "created_at": "2026-08-28T...",
      "completed_at": "2026-08-28T...",
      "expires_at": "2026-09-04T...",
      "download_count": 2,
      "error_message": null
    }
  ],
  "timestamp": "2026-08-28T..."
}
```

#### GET /export/{id}/download

**Response:** The exported file (CSV, PNG, or PDF)

**Error Responses:**
| Code | Description |
|------|-------------|
| 404 | Export not found |
| 400 | Export not completed |
| 410 | Export file expired |

---

## WebSocket

### Connection

**Endpoint:** `ws://localhost:8000/ws`

**Authentication (Optional):** `ws://localhost:8000/ws?token=YOUR_ACCESS_TOKEN`

### Message Types

#### Server → Client

**Connection Message:**
```json
{
  "type": "connection",
  "status": "connected",
  "user_id": null,
  "message": "Connected to MacroCrypto AI WebSocket",
  "timestamp": "2026-08-28T..."
}
```

**Price Update:**
```json
{
  "type": "price_update",
  "data": {
    "symbol": "BTC",
    "price": 45000.00,
    "change_24h_percent": 2.5,
    "volume": 1500000.00,
    "timestamp": "2026-08-28T..."
  },
  "timestamp": "2026-08-28T..."
}
```

**Heartbeat (Ping):**
```json
{"type": "ping"}
```

**Alert:**
```json
{
  "type": "alert",
  "data": {
    "alert_id": 1,
    "message": "BTC price alert",
    "type": "price_alert"
  },
  "timestamp": "2026-08-28T..."
}
```

#### Client → Server

```json
{"type": "ping"}       // Responds with "pong"
{"type": "subscribe"}  // Subscribe to updates
{"type": "unsubscribe"} // Unsubscribe from updates
```

### WebSocket Status

**GET** `/ws/status`

**Response:**
```json
{
  "active_connections": 3,
  "user_connections": 2,
  "status": "operational",
  "timestamp": "2026-08-28T..."
}
```

---

## Examples

### Python Examples

#### Authentication

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Register
def register_user():
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "user@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "full_name": "John Doe"
    })
    return response.json()

# Login
def login():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "johndoe",
        "password": "SecurePass123!"
    })
    return response.json()

# Get current user
def get_current_user(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    return response.json()

# Refresh token
def refresh_token(refresh_token):
    response = requests.post(f"{BASE_URL}/auth/refresh", json={
        "refresh_token": refresh_token
    })
    return response.json()
```

#### Predictions

```python
# Get 24h predictions
def get_predictions_24h(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"horizon": "24h", "model_type": "ensemble"}
    response = requests.get(f"{BASE_URL}/predict/btc", headers=headers, params=params)
    return response.json()

# Get accuracy
def get_accuracy(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"days": 30}
    response = requests.get(f"{BASE_URL}/predict/btc/accuracy", headers=headers, params=params)
    return response.json()
```

#### Market Data

```python
# Get prices
def get_prices(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 10, "offset": 0}
    response = requests.get(f"{BASE_URL}/btc/prices", headers=headers, params=params)
    return response.json()

# Get indicators
def get_indicators(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/indicators", headers=headers)
    return response.json()

# Get correlation
def get_correlation(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"window": "30d"}
    response = requests.get(f"{BASE_URL}/correlation/btc", headers=headers, params=params)
    return response.json()

# Get regimes
def get_regimes(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"timeframe": "1w"}
    response = requests.get(f"{BASE_URL}/regimes/btc", headers=headers, params=params)
    return response.json()
```

#### Recommendations

```python
def get_recommendations(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"timeframe": "24h", "risk_level": "moderate"}
    response = requests.get(f"{BASE_URL}/recommendations/btc", headers=headers, params=params)
    return response.json()
```

#### Exports

```python
def export_predictions_csv(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"export_type": "predictions", "format": "csv", "timeframe": "24h"}
    response = requests.get(f"{BASE_URL}/export", headers=headers, params=params)
    
    if response.status_code == 200:
        with open("predictions.csv", "wb") as f:
            f.write(response.content)
        print("✅ CSV saved to predictions.csv")
    return response

def get_export_history(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/export/history", headers=headers)
    return response.json()
```

#### WebSocket

```python
import asyncio
import websockets
import json

async def connect_websocket(access_token=None):
    uri = "ws://localhost:8000/ws"
    if access_token:
        uri += f"?token={access_token}"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected to WebSocket")
        
        # Receive welcome message
        response = await websocket.recv()
        data = json.loads(response)
        print(f"📩 {data.get('type')}: {data.get('message', '')}")
        
        # Subscribe to updates
        await websocket.send(json.dumps({"type": "subscribe"}))
        
        # Listen for updates
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                
                if data.get('type') == 'price_update':
                    price_data = data.get('data', {})
                    print(f"💰 BTC: ${price_data.get('price', 0):,.2f} "
                          f"({price_data.get('change_24h_percent', 0):+.2f}%)")
                elif data.get('type') == 'ping':
                    await websocket.send(json.dumps({"type": "pong"}))
                    
            except asyncio.TimeoutError:
                await websocket.send(json.dumps({"type": "ping"}))

# Run: asyncio.run(connect_websocket())
```

### cURL Examples

#### Authentication

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"johndoe","password":"SecurePass123!"}' | jq -r '.access_token')

# Get current user
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"YOUR_REFRESH_TOKEN\"}"
```

#### Predictions

```bash
# Get 24h predictions
curl -X GET "http://localhost:8000/api/v1/predict/btc?horizon=24h&model_type=ensemble" \
  -H "Authorization: Bearer $TOKEN"

# Get accuracy
curl -X GET "http://localhost:8000/api/v1/predict/btc/accuracy?days=30" \
  -H "Authorization: Bearer $TOKEN"
```

#### Market Data

```bash
# Get prices
curl -X GET "http://localhost:8000/api/v1/btc/prices?limit=5&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Get indicators
curl -X GET http://localhost:8000/api/v1/indicators \
  -H "Authorization: Bearer $TOKEN"

# Get correlation
curl -X GET "http://localhost:8000/api/v1/correlation/btc?window=30d" \
  -H "Authorization: Bearer $TOKEN"

# Get regimes
curl -X GET "http://localhost:8000/api/v1/regimes/btc?timeframe=1w" \
  -H "Authorization: Bearer $TOKEN"
```

#### Recommendations

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/btc?timeframe=24h&risk_level=moderate" \
  -H "Authorization: Bearer $TOKEN"
```

#### Exports

```bash
# Export CSV
curl -o predictions.csv \
  "http://localhost:8000/api/v1/export?export_type=predictions&format=csv&timeframe=24h" \
  -H "Authorization: Bearer $TOKEN"

# Export PNG
curl -o predictions.png \
  "http://localhost:8000/api/v1/export?export_type=predictions&format=png&timeframe=24h" \
  -H "Authorization: Bearer $TOKEN"

# Export PDF
curl -o predictions.pdf \
  "http://localhost:8000/api/v1/export?export_type=predictions&format=pdf&timeframe=24h" \
  -H "Authorization: Bearer $TOKEN"

# Get export history
curl -X GET http://localhost:8000/api/v1/export/history \
  -H "Authorization: Bearer $TOKEN"
```

#### WebSocket

```bash
# Check WebSocket status
curl -X GET http://localhost:8000/ws/status | jq

# Connect with wscat
wscat -c "ws://localhost:8000/ws?token=$TOKEN"
```

---

## Getting Started Quick Guide

### 1. Register and Login

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"johndoe","password":"SecurePass123!","full_name":"John Doe"}'

# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"johndoe","password":"SecurePass123!"}' | jq -r '.access_token')
```

### 2. Make Your First API Call

```bash
# Get BTC price
curl -X GET "http://localhost:8000/api/v1/btc/prices?limit=1" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Get Predictions

```bash
# Get 24h predictions
curl -X GET "http://localhost:8000/api/v1/predict/btc?horizon=24h" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Connect to WebSocket

```bash
wscat -c "ws://localhost:8000/ws?token=$TOKEN"
```

---

## Support

For issues or questions, please contact the MacroCrypto AI support team.

**Last Updated:** 2026-08-28
**API Version:** 1.0.0