# Microservice Design — MacroCrypto AI

This document defines the 4 microservices that comprise the MacroCrypto AI platform, including their responsibilities, owned data, events, APIs, and dependencies.

---

## 1. Service Overview

| Service | Purpose | Primary User |
|---------|---------|--------------|
| **Data Ingestion Service** | Collect and store BTC and macro data | Internal (AI Service, Alert Service) |
| **AI Service** | Generate BTC price predictions | Internal (API Gateway, Alert Service) |
| **API Gateway** | Expose REST API to external users | External (Traders, Analysts) |
| **Alert Service** | Evaluate alerts and send notifications | Internal (API Gateway) |

---

## 2. Data Ingestion Service

### 2.1 Overview

**Service Name:** `data-ingestion-service`

**Purpose:** Responsible for collecting, validating, and storing all data used by the platform.

**Primary User:** Internal services (AI Service, Alert Service)

### 2.2 Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **BTC Price Collection** | Fetch real-time BTC price data from CoinGecko API |
| **Macro Data Collection** | Fetch macroeconomic indicator data from FRED API |
| **Data Validation** | Validate incoming data (ranges, formats, completeness) |
| **Data Storage** | Store data in TimescaleDB for historical tracking |
| **Data Caching** | Cache current price in Redis for sub-second access |
| **Event Publishing** | Publish events when new data arrives |
| **Data Quality Monitoring** | Monitor data freshness and completeness |
| **WebSocket Management** | Maintain WebSocket connection for real-time price |

### 2.3 Owned Data

| Data Store | Purpose |
|------------|---------|
| **TimescaleDB** | Historical BTC prices and macro indicators |
| **Redis** | Current BTC price cache |

### 2.4 Events Produced

| Event | Description | Payload |
|-------|-------------|---------|
| **PriceUpdated** | Published when a new BTC price is recorded | `{ symbol, price, volume, marketCap, timestamp, source }` |
| **IndicatorUpdated** | Published when a new macro indicator value is recorded | `{ indicatorType, value, previousValue, changePercent, timestamp, source }` |

### 2.5 Events Consumed

| Event | Description | Consumer Logic |
|-------|-------------|----------------|
| **None** | — | — |

### 2.6 APIs

| API | Type | Purpose |
|-----|------|---------|
| Internal API (gRPC) | Internal | Fetch latest data for AI Service |
| Internal API (gRPC) | Internal | Fetch historical data for training |

### 2.7 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | TimescaleDB |
| Cache | Redis |
| Message Broker | RabbitMQ (Producer) |
| WebSocket | CoinGecko WebSocket / Binance WebSocket |

---

## 3. AI Service

### 3.1 Overview

**Service Name:** `ai-service`

**Purpose:** Responsible for generating BTC price predictions using machine learning models.

**Primary User:** Internal services (API Gateway, Alert Service)

### 3.2 Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Prediction Generation** | Generate 24h and 7d BTC price predictions |
| **Model Training** | Train and retrain Prophet model |
| **Feature Engineering** | Transform raw data into model features |
| **Model Versioning** | Manage model versions using MLflow |
| **Accuracy Tracking** | Track and store prediction accuracy metrics |
| **Prediction Caching** | Cache predictions for performance |
| **Prediction Publishing** | Publish events when new predictions are generated |
| **Model Performance Monitoring** | Monitor model accuracy and drift |

### 3.3 Owned Data

| Data Store | Purpose |
|------------|---------|
| **TimescaleDB** | Predictions (24h and 7d) |
| **MLflow** | Model versioning and metadata |
| **Redis** | Prediction cache |

### 3.4 Events Produced

| Event | Description | Payload |
|-------|-------------|---------|
| **PredictionGenerated** | Published when a new prediction is generated | `{ symbol, horizon, predictedPrice, lowerBound, upperBound, confidenceLevel, generatedAt, modelVersion }` |

### 3.5 Events Consumed

| Event | Description | Consumer Logic |
|-------|-------------|----------------|
| **PriceUpdated** | New BTC price available | Update data for prediction generation |
| **IndicatorUpdated** | New macro indicator available | Update data for prediction generation |

### 3.6 APIs

| API | Type | Purpose |
|-----|------|---------|
| Internal API (gRPC) | Internal | Fetch predictions for API Gateway |
| Internal API (gRPC) | Internal | Trigger model retraining |

### 3.7 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| ML Framework | Prophet |
| Model Registry | MLflow |
| Database | TimescaleDB |
| Cache | Redis |
| Message Broker | RabbitMQ (Consumer/Producer) |

---

## 4. API Gateway

### 4.1 Overview

**Service Name:** `api-gateway`

**Purpose:** Responsible for exposing platform functionality to external users.

**Primary User:** External (BTC Traders, Investment Analysts, Platform Users)

### 4.2 Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **REST API** | Expose 15+ REST endpoints |
| **Authentication** | JWT authentication and authorization |
| **Rate Limiting** | Rate limiting per user type |
| **User Management** | User registration and management |
| **API Documentation** | OpenAPI/Swagger documentation |
| **Request Validation** | Validate incoming requests |
| **Response Caching** | Cache responses for performance |
| **Export Requests** | Handle data export requests |

### 4.3 Owned Data

| Data Store | Purpose |
|------------|---------|
| **PostgreSQL** | Users, API keys, export history |

### 4.4 Events Produced

| Event | Description | Payload |
|-------|-------------|---------|
| **AlertAcknowledged** | Published when a user acknowledges an alert | `{ alertId, userId, acknowledgedAt }` |
| **ExportCompleted** | Published when an export is completed | `{ exportId, userId, dataType, format, fileUrl, completedAt }` |
| **UserRegistered** | Published when a new user registers | `{ userId, email, firstName, lastName, registeredAt }` |
| **UserLoggedIn** | Published when a user logs in | `{ userId, email, loggedInAt, ipAddress }` |

### 4.5 Events Consumed

| Event | Description | Consumer Logic |
|-------|-------------|----------------|
| **PredictionGenerated** | New prediction available | Serve via API |
| **AlertTriggered** | Alert triggered | Notify user |
| **NotificationSent** | Notification sent | Track delivery |

### 4.6 APIs

| API | Type | Purpose |
|-----|------|---------|
| **REST API** | External | All user-facing endpoints |
| **WebSocket** | External | Real-time price updates |

### 4.7 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL |
| Cache | Redis |
| Message Broker | RabbitMQ (Consumer/Producer) |
| Auth | JWT, OAuth2 |

---

## 5. Alert Service

### 5.1 Overview

**Service Name:** `alert-service`

**Purpose:** Responsible for evaluating alert conditions and delivering notifications.

**Primary User:** Internal (API Gateway)

### 5.2 Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Alert Evaluation** | Evaluate alerts against incoming events |
| **Alert Management** | Create, update, delete alerts |
| **Alert Lifecycle** | Manage alert states (Active, Triggered, Dismissed, Disabled, Expired) |
| **Notification Delivery** | Send notifications via email and in-app |
| **Alert History** | Track alert history for audit |
| **Macro Event Alerts** | Send alerts before macro events |

### 5.3 Owned Data

| Data Store | Purpose |
|------------|---------|
| **PostgreSQL** | Alerts, alert history, notifications |

### 5.4 Events Produced

| Event | Description | Payload |
|-------|-------------|---------|
| **AlertTriggered** | Published when an alert condition is met | `{ alertId, userId, alertType, threshold, currentValue, triggeredAt }` |
| **NotificationSent** | Published when a notification is sent | `{ notificationId, userId, type, channel, title, message, sentAt }` |

### 5.5 Events Consumed

| Event | Description | Consumer Logic |
|-------|-------------|----------------|
| **PriceUpdated** | New BTC price available | Evaluate price alerts |
| **PredictionGenerated** | New prediction available | Evaluate prediction change alerts |
| **IndicatorUpdated** | New macro indicator available | Evaluate macro event alerts |
| **AlertAcknowledged** | Alert acknowledged by user | Update alert status |

### 5.6 APIs

| API | Type | Purpose |
|-----|------|---------|
| Internal API (gRPC) | Internal | Alert management for API Gateway |

### 5.7 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL |
| Message Broker | RabbitMQ (Consumer/Producer) |
| Email | SendGrid / AWS SES / SMTP |

---

## 6. Service Dependencies

### 6.1 Dependency Diagram

```
┌───────────────────────────┐
│                           │
│  Data Ingestion Service   │
│                           │
└───────────┬───────────────┘
            │
            │ PriceUpdated, IndicatorUpdated
            │
            ▼
┌───────────────────────────┐          ┌───────────────────────────┐
│                           │          │                           │
│   AI Service              │─────────▶│  Alert Service            │
│                           │          │                           │
└───────────┬───────────────┘          └───────────────────────────┘
            │
            │ PredictionGenerated
            │
            ▼
┌───────────────────────────┐
│                           │
│   API Gateway             │
│                           │
└───────────────────────────┘
```

### 6.2 Dependency Matrix

| Service | Depends On | Dependency Type |
|---------|------------|-----------------|
| Data Ingestion | None | — |
| AI Service | Data Ingestion | Events (PriceUpdated, IndicatorUpdated) |
| Alert Service | Data Ingestion, AI Service | Events (PriceUpdated, IndicatorUpdated, PredictionGenerated) |
| API Gateway | AI Service, Alert Service | Events (PredictionGenerated, AlertTriggered, NotificationSent) |

---

## 7. Service Catalog Summary

| Service | Database | APIs | Events Produced | Events Consumed |
|---------|----------|------|-----------------|-----------------|
| **Data Ingestion** | TimescaleDB, Redis | Internal | PriceUpdated, IndicatorUpdated | None |
| **AI Service** | TimescaleDB, MLflow, Redis | Internal | PredictionGenerated | PriceUpdated, IndicatorUpdated |
| **API Gateway** | PostgreSQL | External | AlertAcknowledged, ExportCompleted, UserRegistered, UserLoggedIn | PredictionGenerated, AlertTriggered, NotificationSent |
| **Alert Service** | PostgreSQL | Internal | AlertTriggered, NotificationSent | PriceUpdated, PredictionGenerated, IndicatorUpdated, AlertAcknowledged |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |