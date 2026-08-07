# Event-Driven Architecture — MacroCrypto AI

This document defines the event-driven architecture for the MacroCrypto AI platform, including the Event Catalog, Commands Catalog, RabbitMQ topology, and event flow diagrams.

---

## 1. Overview

MacroCrypto AI uses an event-driven architecture to enable loose coupling between its 4 microservices. Services communicate asynchronously via events published to RabbitMQ.

### 1.1 Key Concepts

| Concept | Description |
|---------|-------------|
| **Event** | A significant change in state that is communicated to other services |
| **Command** | A request to perform an action |
| **Producer** | The service that publishes an event |
| **Consumer** | The service that consumes and processes an event |
| **Broker** | RabbitMQ — the message broker that routes events |

### 1.2 Event Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                                                         │
│  Data Ingestion ──PriceUpdated──▶ AI Service               │
│       │                           │                        │
│       │                           │                        │
│       │ IndicatorUpdated          │ PredictionGenerated    │
│       │                           │                        │
│       ▼                           ▼                        │
│  Alert Service ◀──────────────────────────────────┘        │
│       │                                                   │
│       │ AlertTriggered                                    │
│       │                                                   │
│       ▼                                                   │
│  API Gateway                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Event Catalog

### 2.1 Event List

| # | Event Name | Producer | Consumers | Description |
|---|------------|----------|-----------|-------------|
| 1 | **PriceUpdated** | Data Ingestion | AI Service, Alert Service | New BTC price recorded |
| 2 | **IndicatorUpdated** | Data Ingestion | AI Service, Alert Service | New macro indicator recorded |
| 3 | **PredictionGenerated** | AI Service | API Gateway, Alert Service | New prediction generated |
| 4 | **AlertTriggered** | Alert Service | API Gateway | Alert condition met |
| 5 | **NotificationSent** | Alert Service | API Gateway | Notification delivered |
| 6 | **AlertAcknowledged** | API Gateway | Alert Service | User acknowledged alert |
| 7 | **ExportCompleted** | API Gateway | — | Export request completed |

### 2.2 Event Details

#### Event 1: PriceUpdated

| Attribute | Type | Description |
|-----------|------|-------------|
| symbol | String | BTC |
| price | Decimal | Current price in USD |
| volume | Decimal | 24h trading volume |
| marketCap | Decimal | Current market cap |
| timestamp | DateTime | When the price was recorded |
| source | String | Data source (CoinGecko) |

**Example:**
```json
{
  "eventType": "PriceUpdated",
  "symbol": "BTC",
  "price": 82450.00,
  "volume": 24500000000,
  "marketCap": 1520000000000,
  "timestamp": "2026-08-07T10:30:00Z",
  "source": "CoinGecko"
}
```

---

#### Event 2: IndicatorUpdated

| Attribute | Type | Description |
|-----------|------|-------------|
| indicatorType | String | CPI, INTEREST_RATE, GDP, UNEMPLOYMENT, M2, DXY, TREASURY_YIELD |
| value | Decimal | Current value |
| previousValue | Decimal | Previous value |
| changePercent | Decimal | Percentage change |
| timestamp | DateTime | When the data was recorded |
| source | String | Data source (FRED) |

**Example:**
```json
{
  "eventType": "IndicatorUpdated",
  "indicatorType": "CPI",
  "value": 3.2,
  "previousValue": 3.4,
  "changePercent": -0.2,
  "timestamp": "2026-08-06T12:00:00Z",
  "source": "FRED"
}
```

---

#### Event 3: PredictionGenerated

| Attribute | Type | Description |
|-----------|------|-------------|
| symbol | String | BTC |
| horizon | String | 24h or 7d |
| predictedPrice | Decimal | Predicted price |
| lowerBound | Decimal | Lower bound of confidence interval |
| upperBound | Decimal | Upper bound of confidence interval |
| confidenceLevel | Integer | 70, 85, or 95 |
| generatedAt | DateTime | When the prediction was generated |
| modelVersion | String | Version of the model |

**Example:**
```json
{
  "eventType": "PredictionGenerated",
  "symbol": "BTC",
  "horizon": "24h",
  "predictedPrice": 83450.00,
  "lowerBound": 82500.00,
  "upperBound": 84400.00,
  "confidenceLevel": 85,
  "generatedAt": "2026-08-07T06:00:00Z",
  "modelVersion": "v1.0.3"
}
```

---

#### Event 4: AlertTriggered

| Attribute | Type | Description |
|-----------|------|-------------|
| alertId | UUID | Unique identifier of the alert |
| userId | UUID | User who owns the alert |
| alertType | String | PRICE, PREDICTION_CHANGE, CONFIDENCE_CHANGE, MACRO_EVENT |
| threshold | Decimal | Threshold that was crossed |
| currentValue | Decimal | Current value that triggered the alert |
| triggeredAt | DateTime | When the alert was triggered |

**Example:**
```json
{
  "eventType": "AlertTriggered",
  "alertId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "userId": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
  "alertType": "PRICE",
  "threshold": 85000.00,
  "currentValue": 85200.00,
  "triggeredAt": "2026-08-07T10:35:00Z"
}
```

---

#### Event 5: NotificationSent

| Attribute | Type | Description |
|-----------|------|-------------|
| notificationId | UUID | Unique identifier of the notification |
| userId | UUID | Recipient user |
| type | String | ALERT, EVENT, SYSTEM |
| channel | String | IN_APP, EMAIL |
| title | String | Notification title |
| message | String | Notification message |
| sentAt | DateTime | When the notification was sent |

**Example:**
```json
{
  "eventType": "NotificationSent",
  "notificationId": "c3d4e5f6-g7h8-9012-cdef-gh3456789012",
  "userId": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
  "type": "ALERT",
  "channel": "EMAIL",
  "title": "BTC Price Alert: $85,000 Reached",
  "message": "BTC has reached your price alert threshold of $85,000.",
  "sentAt": "2026-08-07T10:36:00Z"
}
```

---

#### Event 6: AlertAcknowledged

| Attribute | Type | Description |
|-----------|------|-------------|
| alertId | UUID | Unique identifier of the alert |
| userId | UUID | User who acknowledged the alert |
| acknowledgedAt | DateTime | When the alert was acknowledged |

**Example:**
```json
{
  "eventType": "AlertAcknowledged",
  "alertId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "userId": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
  "acknowledgedAt": "2026-08-07T10:40:00Z"
}
```

---

#### Event 7: ExportCompleted

| Attribute | Type | Description |
|-----------|------|-------------|
| exportId | UUID | Unique identifier of the export request |
| userId | UUID | User who requested the export |
| dataType | String | PRICES, INDICATORS, CORRELATION, REGIMES |
| format | String | CSV, PNG, PDF |
| fileUrl | String | URL to download the file |
| completedAt | DateTime | When the export was completed |

**Example:**
```json
{
  "eventType": "ExportCompleted",
  "exportId": "d4e5f6g7-h8i9-0123-defg-ij4567890123",
  "userId": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
  "dataType": "CORRELATION",
  "format": "CSV",
  "fileUrl": "https://storage.example.com/exports/correlation-2026-08-07.csv",
  "completedAt": "2026-08-07T11:00:00Z"
}
```

---

## 3. Commands Catalog

### 3.1 Command List

| # | Command | Initiator | Handler | Description |
|---|---------|-----------|---------|-------------|
| 1 | **FetchPrice** | Data Ingestion | CoinGecko API | Fetch current BTC price |
| 2 | **FetchIndicator** | Data Ingestion | FRED API | Fetch macro indicator data |
| 3 | **GeneratePrediction** | AI Service | Prophet Model | Generate BTC predictions |
| 4 | **CreateAlert** | API Gateway | Alert Service | Create a new alert |
| 5 | **UpdateAlert** | API Gateway | Alert Service | Update an existing alert |
| 6 | **DeleteAlert** | API Gateway | Alert Service | Delete an alert |
| 7 | **AcknowledgeAlert** | API Gateway | Alert Service | Acknowledge a triggered alert |
| 8 | **SendNotification** | Alert Service | Email/In-App | Send a notification |
| 9 | **ExportData** | API Gateway | Export Service | Export data to CSV/PNG/PDF |
| 10 | **RegisterUser** | API Gateway | API Gateway | Register a new user |
| 11 | **LoginUser** | API Gateway | API Gateway | Authenticate a user |

### 3.2 Command Details

#### Command 1: FetchPrice

| Attribute | Type | Description |
|-----------|------|-------------|
| symbol | String | BTC (constant) |
| source | String | CoinGecko |

**Result:** PriceUpdated event

---

#### Command 2: FetchIndicator

| Attribute | Type | Description |
|-----------|------|-------------|
| indicatorType | String | CPI, INTEREST_RATE, GDP, UNEMPLOYMENT, M2, DXY, TREASURY_YIELD |
| source | String | FRED |

**Result:** IndicatorUpdated event

---

#### Command 3: GeneratePrediction

| Attribute | Type | Description |
|-----------|------|-------------|
| symbol | String | BTC |
| horizon | String | 24h or 7d |
| confidenceLevel | Integer | 70, 85, or 95 |

**Result:** PredictionGenerated event

---

#### Command 4: CreateAlert

| Attribute | Type | Description |
|-----------|------|-------------|
| userId | UUID | User creating the alert |
| alertType | String | PRICE, PREDICTION_CHANGE, CONFIDENCE_CHANGE, MACRO_EVENT |
| threshold | Decimal | Threshold value |
| condition | String | REACHES, CROSSES_ABOVE, CROSSES_BELOW |

**Result:** Alert created

---

## 4. RabbitMQ Design

### 4.1 Exchange

| Exchange Name | Type | Description |
|---------------|------|-------------|
| `macro-crypto-events` | Topic | Main exchange for all domain events |

### 4.2 Queues

| Queue Name | Service | Routing Keys | Description |
|------------|---------|--------------|-------------|
| `ai-service-events` | AI Service | `price.updated`, `indicator.updated` | Events consumed by AI Service |
| `alert-service-events` | Alert Service | `price.updated`, `indicator.updated`, `prediction.generated`, `alert.acknowledged` | Events consumed by Alert Service |
| `api-gateway-events` | API Gateway | `prediction.generated`, `alert.triggered`, `notification.sent` | Events consumed by API Gateway |

### 4.3 Routing Keys

| Routing Key | Event | Description |
|-------------|-------|-------------|
| `price.updated` | PriceUpdated | New BTC price recorded |
| `indicator.updated` | IndicatorUpdated | New macro indicator recorded |
| `prediction.generated` | PredictionGenerated | New prediction generated |
| `alert.triggered` | AlertTriggered | Alert condition met |
| `notification.sent` | NotificationSent | Notification delivered |
| `alert.acknowledged` | AlertAcknowledged | User acknowledged alert |

### 4.4 Dead Letter Queue (DLQ)

| Queue Name | Purpose |
|------------|---------|
| `macro-crypto-dlq` | Failed messages that could not be processed |

### 4.5 Retry Queue

| Queue Name | Purpose |
|------------|---------|
| `macro-crypto-retry` | Messages that require retry after failure |

---

## 5. Broker Topology

### 5.1 Topology Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                     Topic Exchange: macro-crypto-events                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  price.updated ──────────────┐                                     │   │
│  │                               │                                     │   │
│  │  indicator.updated ──────────┼────────────────────────────────────┐ │   │
│  │                               │                                    │ │   │
│  │  prediction.generated ───────┼──────────────────────────────────┐ │ │   │
│  │                               │                                  │ │ │   │
│  │  alert.triggered ────────────┼──────────────────────────────────┼─┼─┼── │
│  │                               │                                  │ │ │   │
│  │  notification.sent ──────────┼──────────────────────────────────┼─┼─┼── │
│  │                               │                                  │ │ │   │
│  │  alert.acknowledged ─────────┼──────────────────────────────────┼─┼─┼── │
│  │                               │                                  │ │ │   │
│  └───────────────────────────────┼──────────────────────────────────┼─┼─┼── │
│                                  │                                  │ │ │   │
│                                  ▼                                  │ │ │   │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────┼─┼─┼── │
│  │  Queue:               │  │  Queue:               │  │  Queue:  │ │ │   │
│  │  ai-service-events    │  │  alert-service-events │  │  api-    │ │ │   │
│  │                       │  │                       │  │  gateway-│ │ │   │
│  │  Routing Keys:        │  │  Routing Keys:        │  │  events  │ │ │   │
│  │  - price.updated      │  │  - price.updated      │  │         │ │ │   │
│  │  - indicator.updated  │  │  - indicator.updated  │  │  Routing│ │ │   │
│  │                       │  │  - prediction.generated│  │  Keys:   │ │ │   │
│  │                       │  │  - alert.acknowledged │  │  - pred. │ │ │   │
│  └───────────────────────┘  └───────────────────────┘  │  generated│ │ │   │
│                                                          │  - alert. │ │ │   │
│                                                          │  triggered│ │ │   │
│                                                          │  - notif. │ │ │   │
│                                                          │  sent    │ │ │   │
│                                                          └──────────┼─┼─┼── │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Dead Letter Queue Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Message    │───▶│   Queue      │───▶│   Consumer   │                   │
│  │   Published  │    │              │    │              │                   │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘                   │
│                             │                    │                          │
│                             │                    │ Failure (retry exhausted) │
│                             │                    ▼                          │
│                             │           ┌──────────────┐                   │
│                             │           │  Dead Letter │                   │
│                             │           │    Queue     │                   │
│                             │           └──────┬───────┘                   │
│                             │                  │                          │
│                             │                  ▼                          │
│                             │           ┌──────────────┐                   │
│                             │           │   DLQ        │                   │
│                             │           │   Consumer   │                   │
│                             │           │   (Logging)  │                   │
│                             │           └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Event Flow Diagrams

### 6.1 BTC Price Flow

```
User/External API
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BTC Price Flow                                     │
│                                                                             │
│  ┌──────────────────┐                                                     │
│  │  Data Ingestion  │                                                     │
│  │     Service      │                                                     │
│  │  Fetch BTC price │                                                     │
│  │  from CoinGecko  │                                                     │
│  └────────┬─────────┘                                                     │
│           │                                                                │
│           │ Store in TimescaleDB & Redis                                  │
│           │                                                                │
│           │ Publish PriceUpdated                                           │
│           ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                    RabbitMQ: PriceUpdated                         │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│           │                                                                │
│     ┌─────┴────────────────────────────────┐                             │
│     │                                      │                             │
│     ▼                                      ▼                             │
│  ┌─────────────┐                   ┌─────────────┐                     │
│  │ AI Service  │                   │Alert Service│                     │
│  │ Process for │                   │ Evaluate    │                     │
│  │ Prediction  │                   │ Price       │                     │
│  │ Generation  │                   │ Alerts      │                     │
│  └─────────────┘                   └─────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Prediction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Prediction Flow                                    │
│                                                                             │
│  ┌──────────────────┐                                                     │
│  │   AI Service     │                                                     │
│  │  Generate 24h    │                                                     │
│  │  and 7d          │                                                     │
│  │  Predictions     │                                                     │
│  └────────┬─────────┘                                                     │
│           │                                                                │
│           │ Store in TimescaleDB & Redis                                  │
│           │                                                                │
│           │ Publish PredictionGenerated                                   │
│           ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                 RabbitMQ: PredictionGenerated                     │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│           │                                                                │
│     ┌─────┴────────────────────────────────┐                             │
│     │                                      │                             │
│     ▼                                      ▼                             │
│  ┌─────────────┐                   ┌─────────────┐                     │
│  │API Gateway  │                   │Alert Service│                     │
│  │ Serve via   │                   │ Evaluate    │                     │
│  │ REST API    │                   │ Prediction  │                     │
│  │             │                   │ Change      │                     │
│  │ WebSocket   │                   │ Alerts      │                     │
│  └─────────────┘                   └─────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Alert Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Alert Flow                                         │
│                                                                             │
│  ┌──────────────────┐                                                     │
│  │  Alert Service   │                                                     │
│  │  Evaluate alert  │                                                     │
│  │  conditions      │                                                     │
│  └────────┬─────────┘                                                     │
│           │                                                                │
│           │ Condition met → Publish AlertTriggered                        │
│           ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                    RabbitMQ: AlertTriggered                       │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│           │                                                                │
│           ▼                                                                │
│  ┌──────────────────┐                                                     │
│  │   API Gateway    │                                                     │
│  │  Notify user     │                                                     │
│  │  via in-app      │                                                     │
│  │  and email       │                                                     │
│  └────────┬─────────┘                                                     │
│           │                                                                │
│           │ Publish NotificationSent                                      │
│           ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                  RabbitMQ: NotificationSent                       │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│           │                                                                │
│           ▼                                                                │
│  ┌──────────────────┐                                                     │
│  │   API Gateway    │                                                     │
│  │  Track delivery  │                                                     │
│  │  status          │                                                     │
│  └──────────────────┘                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Data Ingestion Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Data Ingestion Flow                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                    Scheduled Job (Hourly/Daily)                    │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│           │                                                                │
│           ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                    Fetch BTC Price from CoinGecko                  │    │
│  │                    Fetch Macro Data from FRED                      │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│           │                                                                │
│           ▼                                                                │
│  ┌──────────────────┐                                                     │
│  │   Validate       │                                                     │
│  │   Data Quality   │                                                     │
│  └────────┬─────────┘                                                     │
│           │                                                                │
│           │ Store in TimescaleDB                                         │
│           │                                                                │
│           │ Publish PriceUpdated / IndicatorUpdated                      │
│           ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                 RabbitMQ: PriceUpdated / IndicatorUpdated         │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Message Validation and Schema

### 7.1 Schema Registry

| Schema | Version | Description |
|--------|---------|-------------|
| PriceUpdated | v1 | BTC price update schema |
| IndicatorUpdated | v1 | Macro indicator update schema |
| PredictionGenerated | v1 | Prediction generation schema |
| AlertTriggered | v1 | Alert trigger schema |

### 7.2 Validation Rules

| Rule | Description |
|------|-------------|
| **Required Fields** | All required fields must be present |
| **Data Types** | All fields must be of the correct data type |
| **Value Ranges** | Values must be within expected ranges |
| **Timestamp Format** | ISO 8601 format with UTC timezone |

---

## 8. Fault Tolerance

### 8.1 Retry Strategy

| Parameter | Value |
|-----------|-------|
| Max Retries | 3 |
| Initial Delay | 1 second |
| Backoff | Exponential (2x) |
| Max Delay | 60 seconds |

### 8.2 Dead Letter Queue

| Parameter | Value |
|-----------|-------|
| DLQ Name | `macro-crypto-dlq` |
| Retention | 7 days |
| Alert Trigger | DLQ message count > 10 |

### 8.3 Timeouts

| Service | Timeout |
|---------|---------|
| Data Ingestion (API calls) | 30 seconds |
| AI Service (Prediction) | 60 seconds |
| Alert Service (Email) | 10 seconds |
| API Gateway (External) | 30 seconds |

---

## 9. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — all sections complete |