# API Design and Specification

## MacroCrypto AI

# 1. Introduction

## 1.1 Purpose

This document defines the Application Programming Interface (API) design and implementation structure of the MacroCrypto AI system.

It describes the APIs exposed by the system's backend services, their responsibilities, request and response behavior, data sources, service integration, caching, error handling, security considerations, and current implementation status.

The document is intended to provide a clear technical reference for the MacroCrypto AI backend and to support the project's software architecture, implementation, testing, deployment, and academic project-delivery requirements.

## 1.2 Scope

MacroCrypto AI follows a backend service architecture consisting of four principal services:

* **API Gateway** — Central entry point for frontend API requests and service routing.
* **Data Service** — Provides Bitcoin market data, macroeconomic indicators, economic calendar data, and macroeconomic regime information.
* **Alert Service** — Manages price alerts, prediction alerts, macroeconomic alerts, subscriptions, and notifications.
* **AI Service** — Provides Bitcoin prediction, model performance, correlation analysis, methodology, historical event analysis, and export APIs.

The API Gateway acts as a thin routing and proxy layer between the frontend and backend services.

## 1.3 API Design Objectives

The API design follows the following objectives:

1. Provide a consistent interface between the frontend and backend services.
2. Separate data acquisition, alert management, and AI functionality.
3. Maintain a thin API Gateway without duplicating business logic.
4. Provide structured responses and HTTP status codes.
5. Support caching for frequently accessed data.
6. Provide real-time Bitcoin market data through WebSocket communication.
7. Expose analytical and machine-learning functionality through dedicated AI APIs.
8. Maintain clear separation between implemented, partially implemented, and deferred functionality.

---

# 2. System API Architecture

## 2.1 High-Level Architecture

The MacroCrypto AI API architecture consists of a frontend client communicating with backend services through the API Gateway.

```text
Frontend
    |
    v
API Gateway :8000
    |
    +----------------------+----------------------+----------------------+
    |                      |                      |
    v                      v                      v
Data Service :8001    Alert Service :8003    AI Service :8002
    |                      |                      |
    v                      v                      v
TimescaleDB + Redis   PostgreSQL + Redis    ML/Data Artifacts
```

The API Gateway provides centralized routing while individual services retain their respective business responsibilities.

## 2.2 Service Responsibilities

| Service       | Primary Responsibility                                                          |
| ------------- | ------------------------------------------------------------------------------- |
| API Gateway   | Request routing, proxying, CORS, API-level controls                             |
| Data Service  | Market data, macroeconomic data, calendar, regimes                              |
| Alert Service | Alerts, subscriptions, and notifications                                        |
| AI Service    | Prediction, performance, correlation, historical analysis, methodology, exports |

---

# 3. API Gateway

## 3.1 Gateway Operations

The API Gateway provides:

* Central API entry point
* Service routing and proxying
* Request forwarding
* CORS configuration
* API-level error handling
* Rate limiting where configured
* Authentication integration as a prepared security layer

### Base URL

```text
http://localhost:8000/api/v1
```

### Production URL

```text
https://api.macrocrypto.ai/api/v1
```

The production URL is currently a placeholder.

## 3.2 Authentication

JWT is planned as the primary authentication mechanism.

Authentication dependencies are prepared, but JWT authentication is not yet fully implemented or consistently enforced across the system.

Notification APIs remain accessible without JWT during the current implementation stage.

## 3.3 Service Proxy Configuration

| Service       | Base URL                       |
| ------------- | ------------------------------ |
| Data Service  | `http://localhost:8001/api/v1` |
| Alert Service | `http://localhost:8003/api/v1` |
| AI Service    | `http://localhost:8002/api/v1` |

## 3.4 Data Service Gateway Routes

| Method | Endpoint                                 |
| ------ | ---------------------------------------- |
| GET    | `/api/v1/btc/price`                      |
| GET    | `/api/v1/btc/price/history`              |
| GET    | `/api/v1/btc/dominance`                  |
| GET    | `/api/v1/btc/status`                     |
| WS     | `/api/v1/btc/price/stream`               |
| GET    | `/api/v1/indicators`                     |
| GET    | `/api/v1/indicators/{indicator}`         |
| GET    | `/api/v1/indicators/{indicator}/history` |
| GET    | `/api/v1/calendar/events`                |
| GET    | `/api/v1/calendar/upcoming`              |
| GET    | `/api/v1/regimes/current`                |
| GET    | `/api/v1/regimes/history`                |

## 3.5 Alert Service Gateway Routes

| Method         | Endpoint                                |
| -------------- | --------------------------------------- |
| GET/POST       | `/api/v1/alerts`                        |
| GET/PUT/DELETE | `/api/v1/alerts/{id}`                   |
| GET/POST       | `/api/v1/price-alerts`                  |
| GET/PUT/DELETE | `/api/v1/price-alerts/{id}`             |
| GET/POST       | `/api/v1/prediction-alerts`             |
| GET/PUT/DELETE | `/api/v1/prediction-alerts/{id}`        |
| GET/POST       | `/api/v1/macro-alerts`                  |
| GET/PUT/DELETE | `/api/v1/macro-alerts/{id}`             |
| GET/POST       | `/api/v1/macro/subscriptions`           |
| DELETE         | `/api/v1/macro/subscriptions/{id}`      |
| GET            | `/api/v1/macro/notifications`           |
| PUT            | `/api/v1/macro/notifications/{id}/read` |
| GET            | `/api/v1/notifications`                 |
| PUT            | `/api/v1/notifications/{id}/read`       |
| POST           | `/api/v1/notifications/read-all`        |

## 3.6 AI Service Gateway Integration

The AI APIs are implemented at the service level. Gateway exposure remains pending.

Current AI routes are:

| Method | Endpoint                        |
| ------ | ------------------------------- |
| GET    | `/api/v1/predict/btc`           |
| GET    | `/api/v1/performance/btc`       |
| GET    | `/api/v1/correlation/btc`       |
| GET    | `/api/v1/events/historical`     |
| GET    | `/api/v1/methodology`           |
| GET    | `/api/v1/methodology/versions`  |
| GET    | `/api/v1/methodology/changelog` |
| GET    | `/api/v1/exports/{file_name}`   |

---

# 4. Data Service API

The Data Service provides market, macroeconomic, calendar, and regime information required by the application.

## 4.1 Bitcoin Current Price

**GET** `/api/v1/btc/price`

Returns the latest Bitcoin market price and related statistics.

### Response Fields

* `price`
* `change_24h`
* `change_24h_percent`
* `high_24h`
* `low_24h`
* `volume_24h`
* `change_7d`
* `change_7d_percent`
* `updated_at`

### Caching

Redis cache key:

```text
btc_price_snapshot
```

Cache TTL:

```text
5 seconds
```

Rate limiting is configured.

JWT support is prepared but not fully enforced.

Bitcoin market data is primarily sourced from Binance.

---

## 4.2 Bitcoin Price History

**GET** `/api/v1/btc/price/history`

### Query Parameters

| Parameter    | Default  | Description                                            |
| ------------ | -------- | ------------------------------------------------------ |
| `range`      | `7d`     | Historical time range                                  |
| `interval`   | `1h`     | Data interval                                          |
| `max_points` | Optional | Maximum number of returned points; `0` means unlimited |

### Supported Ranges

* `24h`
* `7d`
* `30d`
* `90d`

### Supported Intervals

* `1m`
* `5m`
* `1h`
* `1d`
* `1w`
* `1y`

Redis cache keys are generated using the requested range, interval, and `max_points`.

Historical daily BTC market data is collected using the Binance historical candles API.

---

## 4.3 Bitcoin Dominance

**GET** `/api/v1/btc/dominance`

Returns the latest Bitcoin market dominance percentage.

Response model:

`BTCDominanceResponse`

The implementation uses CoinGecko as the configured market-cap and dominance data source.

### CoinGecko Configuration

```text
https://api.coingecko.com/api/v3
```

BTC dominance cache TTL:

```text
900 seconds
```

### Example Response

```json
{
  "dominance": 58.42,
  "updated_at": "2026-09-19T00:00:00Z"
}
```

The endpoint returns `404` if dominance data is unavailable.

---

## 4.4 Bitcoin Service Status

**GET** `/api/v1/btc/status`

Returns operational information about the Bitcoin data service.

### Response Fields

* `service`
* `status`
* `current_price`
* `price_7d_reference`
* `cache_enabled`
* `cache_connected`
* `data_processor_initialized`
* `websocket_connected`

---

## 4.5 Real-Time Bitcoin Price Stream

**WS** `/api/v1/btc/price/stream`

Direct Data Service endpoint:

```text
ws://localhost:8001/api/v1/btc/price/stream
```

The API Gateway exposes the corresponding WebSocket route.

The real-time Bitcoin market stream uses Binance WebSocket infrastructure.

---

# 5. Macroeconomic Indicators API

## 5.1 Indicator Endpoints

**GET** `/api/v1/indicators`

**GET** `/api/v1/indicators/{indicator}`

**GET** `/api/v1/indicators/{indicator}/history`

The Data Service provides current and historical macroeconomic indicators.

## 5.2 Supported Indicators

| Indicator                        | FRED Series    |
| -------------------------------- | -------------- |
| Consumer Price Index (CPI)       | `CPIAUCSL`     |
| Federal Funds Effective Rate     | `FEDFUNDS`     |
| M2 Money Supply                  | `M2SL`         |
| US Dollar Index (DXY)            | `DTWEXBGS`     |
| Volatility Index (VIX)           | `VIXCLS`       |
| 10-Year Treasury Yield           | `DGS10`        |
| Gross Domestic Product (GDP)     | `GDP`          |
| Unemployment Rate                | `UNRATE`       |
| High Yield Corporate Bond Spread | `BAMLH0A0HYM2` |
| NASDAQ Composite Index           | `NASDAQCOM`    |

FRED is the primary economic data source.

FRED API base URL:

```text
https://api.stlouisfed.org/fred
```

A configurable FRED API key is supported.

A request delay of `0.5` seconds is configured to prevent excessive requests.

---

# 6. Economic Calendar API

## 6.1 Calendar Events

**GET** `/api/v1/calendar/events`

Provides economic calendar release information.

## 6.2 Upcoming Calendar Events

**GET** `/api/v1/calendar/upcoming`

Provides upcoming economic events based on configured FRED release mappings.

## 6.3 FRED Release Mapping

| Event Type        | FRED Release ID |
| ----------------- | --------------: |
| Fed               |             101 |
| CPI               |              10 |
| Employment        |              50 |
| GDP               |              53 |
| VIX               |             200 |
| M2 Money Supply   |              21 |
| DXY               |             245 |
| NASDAQ            |             328 |
| High Yield Spread |             209 |
| 10-Year Treasury  |              18 |

---

# 7. Macroeconomic Regimes

**GET** `/api/v1/regimes/current`

**GET** `/api/v1/regimes/history`

These endpoints provide current and historical macroeconomic regime classifications used by the application.

---

# 8. Alert Service API

The Alert Service manages user-defined alerts, subscriptions, and notification generation.

Supported alert categories include:

* Price Alerts
* Prediction Alerts
* Confidence Alerts
* Macroeconomic Alerts

---

# 9. Price Alerts

The Price Alert API manages user-defined Bitcoin price conditions.

| Method | Endpoint                    |
| ------ | --------------------------- |
| GET    | `/api/v1/price-alerts`      |
| POST   | `/api/v1/price-alerts`      |
| GET    | `/api/v1/price-alerts/{id}` |
| PUT    | `/api/v1/price-alerts/{id}` |
| DELETE | `/api/v1/price-alerts/{id}` |

---

# 10. Prediction Alerts

The Prediction Alert API manages alerts associated with AI-generated predictions.

| Method | Endpoint                         |
| ------ | -------------------------------- |
| GET    | `/api/v1/prediction-alerts`      |
| POST   | `/api/v1/prediction-alerts`      |
| GET    | `/api/v1/prediction-alerts/{id}` |
| PUT    | `/api/v1/prediction-alerts/{id}` |
| DELETE | `/api/v1/prediction-alerts/{id}` |

Prediction and confidence events can generate notifications included in the unified notification feed.

---

# 11. Macroeconomic Event Subscriptions

The Macro Subscription API manages subscriptions to configured macroeconomic events.

| Method | Endpoint                           |
| ------ | ---------------------------------- |
| GET    | `/api/v1/macro/subscriptions`      |
| POST   | `/api/v1/macro/subscriptions`      |
| DELETE | `/api/v1/macro/subscriptions/{id}` |

---

# 12. Macroeconomic Alerts

The Macro Alert API manages user-defined macroeconomic alert conditions.

| Method | Endpoint                    |
| ------ | --------------------------- |
| GET    | `/api/v1/macro-alerts`      |
| POST   | `/api/v1/macro-alerts`      |
| GET    | `/api/v1/macro-alerts/{id}` |
| PUT    | `/api/v1/macro-alerts/{id}` |
| DELETE | `/api/v1/macro-alerts/{id}` |

---

# 13. Macro Notifications

**GET** `/api/v1/macro/notifications`

**PUT** `/api/v1/macro/notifications/{id}/read`

Provides macroeconomic notifications and supports marking individual notifications as read.

---

# 14. Unified Notifications

The Unified Notification API provides a single notification feed combining:

* Price alerts
* Prediction alerts
* Confidence alerts
* Macroeconomic alerts

This enables the frontend to consume notifications through a single endpoint.

## 14.1 Get Unified Notifications

**GET** `/api/v1/notifications`

### Example Response

```json
{
  
  "total": 3,
  "limit": 20,
  "offset": 0,
  "notifications": [
    {
      "id": 1,
      "user_id": 1,
      "alert_id": 12,
      "title": "BTC Price Alert",
      "message": "Bitcoin price has crossed the configured threshold.",
      "notification_type": "price_alert",
      "data": {},
      "action_url": "/alerts/12",
      "read": false,
      "is_archived": false,
      "created_at": "2026-09-29T10:00:00Z",
      "read_at": null
    },
    {
      "id": 2,
      "user_id": 1,
      "alert_id": 18,
      "title": "BTC Prediction Alert",
      "message": "The latest BTC prediction has reached the configured target.",
      "notification_type": "prediction_alert",
      "data": {},
      "action_url": "/predictions/18",
      "read": false,
      "is_archived": false,
      "created_at": "2026-09-29T10:05:00Z",
      "read_at": null
    },
    {
      "id": 3,
      "user_id": 1,
      "alert_id": 25,
      "title": "Macro Economic Alert",
      "message": "A significant change has been detected in the configured macroeconomic indicator.",
      "notification_type": "macro_alert",
      "data": {},
      "action_url": "/macro-alerts/25",
      "read": true,
      "is_archived": false,
      "created_at": "2026-09-29T10:10:00Z",
      "read_at": "2026-09-29T10:15:00Z"
    }
  ]
}
```

### Response Fields

* `total`
* `limit`
* `offset`
* `notifications`
* `id`
* `user_id`
* `alert_id`
* `title`
* `message`
* `notification_type`
* `data`
* `action_url`
* `read`
* `is_archived`
* `created_at`
* `read_at`

### Notification Types

* `price_alert`
* `prediction_alert`
* `confidence_alert`
* `macro_alert`

## 14.2 Mark Notification as Read

**PUT** `/api/v1/notifications/{id}/read`

Marks an individual notification as read.

## 14.3 Mark All Notifications as Read

**POST** `/api/v1/notifications/read-all`

Marks available notifications as read.

## 14.4 Authentication

JWT is not currently implemented or enforced for the notification endpoints. They remain freely accessible during the current implementation stage.

---

# 15. AI Service API

The AI Service provides machine-learning and analytical functionality for:

* Bitcoin forecasting
* Model evaluation
* Macroeconomic correlation analysis
* Historical event analysis
* Methodology information
* Data export

### Base URL

```text
http://localhost:8002/api/v1
```

The runtime service is implemented and service-level APIs are available.

Gateway integration remains pending.

## 15.1 Supported Models

The AI Service currently supports:

* Prophet
* XGBoost
* LightGBM

---

# 16. Bitcoin Prediction API

**GET** `/api/v1/predict/btc`

Provides AI-generated Bitcoin predictions using the configured forecasting models.

The endpoint is intended to provide forecast results and prediction metadata.

Gateway exposure remains pending.

---

# 17. Correlation Analysis API

**GET** `/api/v1/correlation/btc`

Provides Pearson correlation analysis between Bitcoin and configured macroeconomic indicators.

## 17.1 Correlation Windows

* 30 days
* 90 days
* 365 days / 1 year

## 17.2 Query Parameters

| Parameter         | Default | Description                              |
| ----------------- | ------- | ---------------------------------------- |
| `window_days`     | —       | Correlation window                       |
| `include_history` | `false` | Include historical correlation           |
| `history_limit`   | `30`    | Number of historical records; maximum 90 |
| `history_days`    | `90`    | Historical period; maximum 365           |

## 17.3 Response

Correlation results include:

* coefficient
* strength
* direction
* arrow
* p-value
* significance
* confidence
* human-readable insight
* optional historical correlation data

Invalid windows return `422`.

An empty dataset returns a successful empty response.

Display fields are derived at response time, while correlation data is retrieved from the repository.

No authentication or rate limiting is currently applied.

---

# 18. Prediction Performance API

**GET** `/api/v1/performance/btc`

Provides aggregate Bitcoin prediction performance across configured models and horizons.

## 18.1 Supported Horizons

* 24h
* 7d

## 18.2 Metrics

* MAE
* RMSE
* MAPE
* Directional accuracy
* Market-condition breakdown
* Threshold status
* Recent threshold breach count
* Warning/streak information
* Optional performance history

Directional accuracy is currently `null` because it is not persisted on a per-row basis.

## 18.3 Query Parameters

| Parameter         | Default  | Description                         |
| ----------------- | -------- | ----------------------------------- |
| `days`            | `30`     | Evaluation period, 1–365 days       |
| `horizon`         | Optional | Prediction horizon                  |
| `model_name`      | Optional | Model filter                        |
| `models`          | Optional | Comma-separated model list          |
| `include_history` | `false`  | Include historical performance      |
| `history_limit`   | `30`     | Historical record limit; maximum 90 |

When both `model_name` and `models` are provided, `models` takes precedence.

Invalid parameters return `422`.

Unknown model names are filtered.

Thresholds are evaluated in the response and streak monitoring/recent threshold breaches are included.

---

# 19. Bitcoin Recommendations

The AI Service is intended to provide AI-generated Bitcoin recommendations based on prediction and macroeconomic analysis.

This functionality is currently under development.

---

# 20. Methodology APIs

## 20.1 Current Methodology

**GET** `/api/v1/methodology`

Accepts an optional `version` parameter.

When omitted, the current methodology is returned.

An unknown version returns a structured `404`.

Methodology information includes:

* Model variants
* Training strategies
* Pearson correlation method
* Correlation windows
* Correlation thresholds and labels
* Regime classification
* Regime thresholds
* External data sources
* Limitations
* Version information
* Changelog

The methodology content is static and does not require database or Redis access.

## 20.2 Methodology Versions

**GET** `/api/v1/methodology/versions`

Returns methodology versions in chronological order, oldest first.

## 20.3 Methodology Changelog

**GET** `/api/v1/methodology/changelog`

Returns methodology changes in reverse chronological order, newest first.

---

# 21. Historical Events API

**GET** `/api/v1/events/historical`

Provides historical macroeconomic events and their observed Bitcoin reactions.

## 21.1 Filters

* `event_type`
* `start_date`
* `end_date`

## 21.2 Supported Event Types

* `fed`
* `cpi`
* `gdp`
* `employment`

Multiple event types can be supplied.

Invalid event types or invalid date ranges return `422`.

An empty result returns a successful empty response.

## 21.3 Response

The response includes:

* Historical events
* By-type aggregates
* Unmapped event names
* Insufficient event types
* Applied filters
* Event count
* Generation timestamp

## 21.4 Aggregate Metrics

Aggregates include:

* Mean Bitcoin price change
* Mean volatility
* Direction frequencies
* Minimum
* Maximum
* Confidence interval

Event types with fewer than three observations are reported as insufficient.

## 21.5 Caching

Redis is used as a best-effort cache.

Cache prefix:

```text
ai-service:events:historical
```

TTL:

```text
60 seconds
```

---

# 22. Export API

**GET** `/api/v1/exports/{file_name}`

Downloads a completed export by filename.

The endpoint:

1. Looks up the export record.
2. Verifies that the export is completed.
3. Checks that the corresponding file exists in storage.
4. Marks the export as downloaded on a best-effort basis.
5. Returns the file.

## 22.1 Supported Formats

* CSV
* PNG
* PDF

The endpoint returns `404` when:

* The export record does not exist.
* The export is not completed.
* The exported file is missing.

Export expiry cleanup is handled separately.

Ownership and authorization enforcement are deferred.

---

# 23. External Data Sources

MacroCrypto AI integrates external data providers according to the type of data required by the application.

## 23.1 Binance — Bitcoin Market Data

Binance is the primary crypto market-data source.

### REST API

Production REST base URL:

```text
https://api.binance.com/api/v3
```

Testnet REST base URL:

```text
https://testnet.binance.vision/api/v3
```

The application is currently configured to use the production endpoint.

### WebSocket

Production WebSocket:

```text
wss://stream.binance.com:9443/ws
```

Testnet WebSocket:

```text
wss://testnet.binance.vision/ws
```

The application is currently configured to use the production endpoint.

### Default Symbol

```text
BTCUSDT
```

### Historical Daily Candles

```text
https://api.binance.com/api/v3/klines
```

### Configured Rate Limit

```text
1200 requests/minute
```

---

## 23.2 Yahoo Finance — Gold Market Data

Yahoo Finance is used as a market-data source for gold.

Base URL:

```text
https://query1.finance.yahoo.com/v8/finance/chart
```

### Configured Symbols

| Symbol     | Description  |
| ---------- | ------------ |
| `XAUUSD=X` | Gold Spot    |
| `GC=F`     | Gold Futures |

The gold spot symbol is the configured primary symbol, with gold futures available as an alternative source.

---

## 23.3 Blockchain.com — Bitcoin On-Chain Data

Blockchain.com is used as a source for Bitcoin on-chain metrics.

Base URL:

```text
https://api.blockchain.info/charts
```

### Active Addresses

Chart:

```text
n-unique-addresses
```

The active-address metric is used as a Bitcoin on-chain indicator.

---

## 23.4 CoinGecko — Market Capitalization and Dominance

CoinGecko is configured as the market-cap and Bitcoin-dominance market-data source.

Base URL:

```text
https://api.coingecko.com/api/v3
```

Market-cap cache TTL:

```text
900 seconds
```

Bitcoin dominance cache TTL:

```text
900 seconds
```

---

## 23.5 FRED — Economic Indicators

The Federal Reserve Bank of St. Louis FRED API is the primary economic-data source.

Base URL:

```text
https://api.stlouisfed.org/fred
```

### Configured Series

| Indicator                        | Series ID      |
| -------------------------------- | -------------- |
| Consumer Price Index             | `CPIAUCSL`     |
| Federal Funds Effective Rate     | `FEDFUNDS`     |
| M2 Money Supply                  | `M2SL`         |
| US Dollar Index                  | `DTWEXBGS`     |
| Volatility Index                 | `VIXCLS`       |
| 10-Year Treasury Yield           | `DGS10`        |
| Gross Domestic Product           | `GDP`          |
| Unemployment Rate                | `UNRATE`       |
| High Yield Corporate Bond Spread | `BAMLH0A0HYM2` |
| NASDAQ Composite Index           | `NASDAQCOM`    |

The FRED API key is configurable.

A request delay of `0.5` seconds is configured to prevent excessive requests.

---

# 24. Storage and Infrastructure

## 24.1 TimescaleDB/PostgreSQL

The database layer stores:

* BTC price history
* Macro indicators
* BTC dominance
* Alert configuration
* Notification data
* AI performance data
* Export history
* Correlation data

## 24.2 Redis

Redis is used for:

* API response caching
* Latest BTC price
* Historical BTC price
* BTC dominance
* Market-cap data
* Historical events
* Data Service caching

## 24.3 File Storage

File storage is used for generated:

* CSV exports
* PNG exports
* PDF exports

---

# 25. API Error Handling

The API uses standard HTTP status codes to communicate request outcomes.

| Status | Meaning                                  |
| ------ | ---------------------------------------- |
| `200`  | Successful request                       |
| `201`  | Resource created                         |
| `204`  | Successful request with no response body |
| `400`  | Bad request                              |
| `401`  | Unauthorized                             |
| `403`  | Forbidden                                |
| `404`  | Resource not found                       |
| `422`  | Validation error                         |
| `429`  | Rate limit exceeded                      |
| `500`  | Internal server error                    |

Structured validation errors are returned where implemented.

---

# 26. Health and Operational Endpoints

## 26.1 Data Service

* GET `/`
* GET `/health`
* GET `/version`
* GET `/api/v1/btc/status`

## 26.2 Alert Service

* GET `/`
* GET `/health`
* GET `/ready`

## 26.3 AI Service

* GET `/`
* GET `/health`
* GET `/health/live`
* GET `/health/ready`
* GET `/ready`

## 26.4 API Gateway

* GET `/`
* GET `/health`
* GET `/version`
* GET `/ready`

---

# 27. Rate Limiting

Rate limiting is applied where configured.

The Data Service applies configured application-level rate limiting to:

* BTC current price
* BTC price history
* BTC dominance

The configured Binance external API rate limit is:

```text
1200 requests/minute
```

The exact application-level rate-limit values are controlled through service configuration.

AI analytical endpoints currently do not apply rate limiting.

---

# 28. Security Considerations

JWT authentication is planned as the primary authentication mechanism but is not yet fully implemented across the system.

The current implementation therefore distinguishes between:

* Authentication infrastructure that has been prepared.
* Endpoints where authentication is currently enforced.
* Endpoints that remain accessible during the current implementation stage.

In particular, the notification APIs remain accessible without JWT.

Additional authorization requirements, including ownership enforcement for exported files, are deferred.

---

# 29. API Implementation Status

## 29.1 Implemented

The following functionality is implemented:

* API Gateway routing
* Data Service
* BTC current price
* BTC history
* BTC dominance
* BTC real-time WebSocket
* BTC status
* Macro indicators
* Economic calendar
* Macro regimes
* Price alerts
* Prediction alerts
* Macro alerts
* Macro subscriptions
* Macro notifications
* Unified notifications
* Notification read
* Notification read-all
* AI runtime
* AI prediction
* AI performance
* AI correlation
* AI methodology
* AI historical events
* AI export download

## 29.2 Partially Implemented / In Progress

* JWT authentication
* AI Gateway integration
* AI recommendations
* Production prediction model deployment
* Prediction confidence intervals
* Directional accuracy persistence and reporting

## 29.3 Deferred

* Full authentication and authorization
* Export ownership enforcement
* AI rate limiting
* Additional AI recommendation functionality

---

# 30. Architectural Considerations

The API architecture separates the system into independently responsible services while maintaining a centralized access point through the API Gateway.

The Gateway is intentionally maintained as a thin routing/proxy layer and does not duplicate service business logic.

The Data Service isolates external data collection and market/economic data processing.

The Alert Service manages user-defined alert conditions and notification generation.

The AI Service isolates machine-learning and analytical functionality, including forecasting, performance evaluation, correlation analysis, historical event analysis, methodology information, and exports.

This separation supports maintainability and allows the individual services to evolve independently while maintaining a consistent API interface for the frontend.

---

# 31. API Design Summary

The MacroCrypto AI API provides the backend interface required by the application across four primary functional areas:

1. **Market and Economic Data**

   * Bitcoin price and history
   * Bitcoin dominance
   * Real-time Bitcoin price streaming
   * Macroeconomic indicators
   * Economic calendar
   * Macroeconomic regimes

2. **Alerts and Notifications**

   * Price alerts
   * Prediction alerts
   * Macroeconomic alerts
   * Macro subscriptions
   * Macro notifications
   * Unified notifications

3. **AI and Analytics**

   * Bitcoin prediction
   * Prediction performance
   * Correlation analysis
   * Historical event analysis
   * Methodology information
   * Bitcoin recommendations under development

4. **Data Export**

   * CSV
   * PNG
   * PDF

The API implementation reflects the current state of the MacroCrypto AI system as of the final documented revision date.

---

# 32. Revision History

| Version | Date              | Author | Description                                                                                                                                                                                                                                                                                |
| ------- | ----------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1.0     | 07 August 2026    | Sid   | Initial API Design                                                                                                                                                                                                                                                                         |
| 1.1     | 05 September 2026    | Mael   | Updated data and alert service endpoints and API Gateway routes                                                                                                                                                                                                                                           |
| 1.2     | 29 September 2026 | Mael   | Updated AI service endpoints |

---
