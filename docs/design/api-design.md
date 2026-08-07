# API Design — MacroCrypto AI

This document defines the REST API endpoints for the MacroCrypto AI platform.

---

## 1. Overview

The API Gateway exposes REST endpoints for all user-facing functionality. All endpoints are protected by JWT authentication and rate limiting.

### 1.1 Base URL

```
https://api.macrocrypto.ai/api/v1/
```

### 1.2 Authentication

All endpoints (except `/auth/*`) require a JWT token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

### 1.3 Rate Limits

| User Type | Rate Limit |
|-----------|------------|
| Guest | 10 requests/minute |
| Registered User | 100 requests/minute |
| Admin | 1000 requests/minute |

---

## 2. API Endpoints

### 2.1 Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predict/btc` | Get BTC predictions (24h/7d) |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| horizon | String | No | 24h or 7d (default: 24h) |
| confidence | Integer | No | 70, 85, 95 (default: 85) |

**Response:**

```json
{
  "symbol": "BTC",
  "currency": "USD",
  "horizon": "24h",
  "current_price": 82450.00,
  "predictions": [
    {
      "time": "2026-08-07T07:00:00Z",
      "predicted_price": 82550.00,
      "lower_bound": 82100.00,
      "upper_bound": 83000.00,
      "confidence": 85
    }
  ],
  "summary": {
    "expected_range": {
      "low": 82100.00,
      "high": 83000.00
    },
    "trend": "slightly_bullish"
  },
  "last_updated": "2026-08-07T06:00:00Z"
}
```

**Error Codes:**

| Code | Description |
|------|-------------|
| 400 | Invalid horizon or confidence value |
| 401 | Missing or invalid JWT token |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

### 2.2 Price

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/btc/price` | Get current BTC price |

**Response:**

```json
{
  "symbol": "BTC",
  "currency": "USD",
  "price": 82450.00,
  "change_24h": {
    "percentage": 2.3,
    "absolute": 1850.00
  },
  "change_7d": {
    "percentage": 5.7,
    "absolute": 4450.00
  },
  "high_24h": 83200.00,
  "low_24h": 81100.00,
  "volume_24h": 24500000000,
  "timestamp": "2026-08-07T10:30:00Z"
}
```

---

### 2.3 Indicators

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/indicators` | Get macroeconomic indicators |

**Response:**

```json
{
  "indicators": [
    {
      "type": "CPI",
      "value": 3.2,
      "previous_value": 3.4,
      "change_percent": -0.2,
      "trend": "falling",
      "impact": "positive",
      "timestamp": "2026-08-06T12:00:00Z"
    }
  ],
  "last_updated": "2026-08-06T12:00:00Z"
}
```

---

### 2.4 Correlation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/correlation/btc` | Get BTC-macro correlation |

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| window | String | No | 30d, 90d, 1y (default: 90d) |

**Response:**

```json
{
  "correlations": [
    {
      "indicator": "CPI",
      "coefficient": 0.65,
      "strength": "strong",
      "direction": "positive",
      "p_value": 0.01,
      "significant": true
    }
  ],
  "window": "90d",
  "last_updated": "2026-08-07T06:00:00Z"
}
```

---

### 2.5 Regimes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/regimes/btc` | Get regime data |

**Response:**

```json
{
  "current_regime": {
    "type": "high_inflation",
    "confidence": 85,
    "indicators": {
      "cpi": 3.2,
      "interest_rate": 5.25
    }
  },
  "historical_regimes": [
    {
      "type": "high_inflation",
      "start_date": "2023-01-01",
      "end_date": "2023-06-30",
      "btc_performance": {
        "avg_return": 12.5,
        "max_drawdown": -8.3,
        "volatility": 4.2,
        "sharpe_ratio": 2.1
      }
    }
  ]
}
```

---

### 2.6 Accuracy

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/accuracy/btc` | Get prediction accuracy |

**Response:**

```json
{
  "accuracy": {
    "24h": 89,
    "7d": 82,
    "overall": 87
  },
  "metrics": {
    "rmse": 1200.00,
    "mae": 950.00,
    "mape": 1.2
  },
  "based_on": 30,
  "time_period": "last_30_days",
  "last_model_training": "2026-08-07T06:00:00Z"
}
```

---

### 2.7 Recommendations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recommendations/btc` | Get trade recommendations |

**Response:**

```json
{
  "recommendation": "BUY",
  "confidence": 85,
  "entry_price": 82450.00,
  "stop_loss": 80800.00,
  "take_profit": 86700.00,
  "risk_level": "medium",
  "risk_reward_ratio": "1:2.6",
  "horizon": "24h",
  "explanation": "Predicted upward trend based on positive macro conditions",
  "accuracy": 87
}
```

---

### 2.8 Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/events/calendar` | Get economic calendar |

**Response:**

```json
{
  "upcoming_events": [
    {
      "name": "CPI Release",
      "date": "2026-08-15",
      "impact": "high",
      "description": "Inflation data release - high impact on BTC"
    }
  ],
  "history": [],
  "timezone": "America/New_York"
}
```

---

### 2.9 Methodology

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/methodology` | Get methodology documentation |

**Response:**

```json
{
  "model": {
    "name": "Prophet",
    "version": "1.0.3",
    "description": "Time-series forecasting model developed by Meta",
    "parameters": {}
  },
  "correlation_method": "Pearson",
  "regime_detection": "Rule-based",
  "data_sources": ["CoinGecko", "FRED"],
  "limitations": ["Predictions are probabilistic, not deterministic"]
}
```

---

### 2.10 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login user |
| POST | `/auth/refresh` | Refresh JWT token |

**Register Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Login Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Login Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 900,
  "user": {
    "id": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  }
}
```

---

### 2.11 Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/alerts/price` | Create price alert |
| POST | `/alerts/prediction` | Create prediction alert |
| POST | `/alerts/events` | Create macro event alert |
| GET | `/alerts` | Get all alerts |
| PUT | `/alerts/{id}` | Update alert |
| DELETE | `/alerts/{id}` | Delete alert |

**Create Price Alert Request:**

```json
{
  "threshold": 85000.00,
  "condition": "crosses_above",
  "type": "price"
}
```

---

### 2.12 Exports

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/export` | Export data |
| GET | `/export/history` | Get export history |
| GET | `/export/{id}` | Download export |

**Export Request:**

```json
{
  "data_type": "correlation",
  "format": "csv",
  "timeframe": "90d"
}
```

---

## 3. Error Responses

### 3.1 Error Response Format

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "status": 429
  }
}
```

### 3.2 Error Codes

| Code | Description | Status |
|------|-------------|--------|
| INVALID_REQUEST | Invalid request parameters | 400 |
| UNAUTHORIZED | Missing or invalid JWT token | 401 |
| FORBIDDEN | Insufficient permissions | 403 |
| NOT_FOUND | Resource not found | 404 |
| RATE_LIMIT_EXCEEDED | Rate limit exceeded | 429 |
| INTERNAL_ERROR | Internal server error | 500 |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — all endpoints defined |