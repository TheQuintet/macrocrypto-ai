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
| **Prediction Generation** | Generate 24h and 7d BTC price predictions using Prophet model |
| **Model Training** | Train and retrain Prophet model with latest data |
| **Feature Engineering** | Transform raw data into model features (10 features: 5 macro, 5 BTC) |
| **Model Versioning** | Manage model versions using MLflow |
| **Accuracy Tracking** | Track and store prediction accuracy metrics (RMSE, MAE, MAPE) |
| **Prediction Caching** | Cache predictions in Redis for performance |
| **Prediction Publishing** | Publish PredictionGenerated event when new predictions are available |
| **Model Performance Monitoring** | Monitor model accuracy and feature drift |
| **Confidence Interval Calculation** | Calculate upper and lower bounds using Prophet's uncertainty intervals |

### 3.3 Owned Data

| Data Store | Purpose |
|------------|---------|
| **TimescaleDB** | Store predictions (24h and 7d with confidence intervals) |
| **MLflow** | Model versioning, parameters, and metadata |
| **Redis** | Cache predictions for sub-second API responses |

### 3.4 Events Produced

| Event | Description | Payload |
|-------|-------------|---------|
| **PredictionGenerated** | Published when a new prediction is generated | `{ symbol, horizon, predictedPrice, lowerBound, upperBound, confidenceLevel, generatedAt, modelVersion }` |

### 3.5 Events Consumed

| Event | Description | Consumer Logic |
|-------|-------------|----------------|
| **PriceUpdated** | New BTC price available | Update feature data for prediction generation |
| **IndicatorUpdated** | New macro indicator available | Update feature data for prediction generation |

### 3.6 APIs

| API | Type | Purpose |
|-----|------|---------|
| Internal API (gRPC) | Internal | Fetch predictions for API Gateway |
| Internal API (gRPC) | Internal | Trigger model retraining |
| Internal API (gRPC) | Internal | Get model performance metrics |

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
| Scheduling | Celery / Cron |

### 3.8 Prediction Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Prediction Flow                           │
│                                                                 │
│  ┌──────────────────┐                                         │
│  │ PriceUpdated /   │                                         │
│  │ IndicatorUpdated │                                         │
│  └────────┬─────────┘                                         │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────┐                                         │
│  │  Feature         │  10 Features:                           │
│  │  Engineering     │  - CPI, Interest Rate, M2, DXY, Yield   │
│  │                  │  - Price, Volume, Volatility, Dominance, │
│  │                  │    Active Addresses                     │
│  └────────┬─────────┘                                         │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────┐                                         │
│  │  Prophet Model   │  Generate 24h (hourly) and 7d (daily)   │
│  │  Prediction      │  with confidence intervals               │
│  └────────┬─────────┘                                         │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────┐                                         │
│  │  Store in        │  Save predictions in TimescaleDB        │
│  │  TimescaleDB     │  Cache in Redis                         │
│  └────────┬─────────┘                                         │
│           │                                                    │
│           ▼                                                    │
│  ┌──────────────────┐                                         │
│  │  Publish Event   │  PredictionGenerated                    │
│  └──────────────────┘                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 3.9 Retraining Strategy

| Schedule | Trigger | Description |
|----------|---------|-------------|
| **Daily** | Scheduled (6:00 AM UTC) | Regular retraining with latest data |
| **On-Demand** | Manual | Triggered by admin via API |
| **Conditional** | Performance degradation | Triggered when accuracy drops below threshold |

### 3.10 Model Performance Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **MAE** | < 5% | Mean Absolute Error |
| **RMSE** | < 7% | Root Mean Square Error |
| **MAPE** | < 5% | Mean Absolute Percentage Error |
| **Directional Accuracy** | > 55% | Percentage of correct direction predictions |
| **Confidence Interval Coverage** | ~95% | Percentage of actual prices within predicted bounds |

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
| **WebSocket Gateway** | Serve real-time price updates |

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

### 4.7 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/predict/btc` | Get BTC predictions |
| GET | `/api/v1/btc/price` | Get current BTC price |
| GET | `/api/v1/indicators` | Get macro indicators |
| GET | `/api/v1/correlation/btc` | Get BTC-macro correlation |
| GET | `/api/v1/regimes/btc` | Get regime data |
| GET | `/api/v1/accuracy/btc` | Get prediction accuracy |
| GET | `/api/v1/recommendations/btc` | Get trade recommendations |
| GET | `/api/v1/events/calendar` | Get economic calendar |
| GET | `/api/v1/methodology` | Get methodology |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/refresh` | Refresh JWT token |
| POST | `/api/v1/alerts/price` | Create price alert |
| POST | `/api/v1/alerts/prediction` | Create prediction alert |
| POST | `/api/v1/alerts/events` | Create macro event alert |
| GET | `/api/v1/export` | Export data |

### 4.8 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL |
| Cache | Redis |
| Message Broker | RabbitMQ (Consumer/Producer) |
| Auth | JWT, OAuth2 |
| Documentation | OpenAPI / Swagger |

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
| **Prediction Change Monitoring** | Monitor prediction changes for alerts |
| **Confidence Change Monitoring** | Monitor confidence changes for alerts |

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

### 5.6 Alert States

```
┌─────────┐
│ Active  │
└────┬────┘
     │
     ├── User disables → Disabled
     │
     ├── Expiry → Expired (one-time)
     │
     └── Condition met → Triggered
                          │
                          ├── User dismisses → Dismissed
                          │
                          └── Auto-archive after 7 days → Archived
```

### 5.7 APIs

| API | Type | Purpose |
|-----|------|---------|
| Internal API (gRPC) | Internal | Alert management for API Gateway |

### 5.8 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Database | PostgreSQL |
| Message Broker | RabbitMQ (Consumer/Producer) |
| Email | SendGrid / AWS SES / SMTP |

---

## 6. Database per Service

### 6.1 Database Ownership

| Service | Database | Purpose | Data Stored |
|---------|----------|---------|-------------|
| **Data Ingestion** | TimescaleDB | Time-series data | BTC prices, macro indicators |
| **Data Ingestion** | Redis | Cache | Current BTC price |
| **AI Service** | TimescaleDB | Predictions | 24h and 7d predictions |
| **AI Service** | Redis | Cache | Cached predictions |
| **AI Service** | MLflow | Model registry | Model versions, metadata |
| **API Gateway** | PostgreSQL | User data | Users, API keys, export history |
| **Alert Service** | PostgreSQL | Alerts | Alerts, history, notifications |

### 6.2 Database Separation Rules

| Rule | Description |
|------|-------------|
| **No Sharing** | Each service has its own database |
| **No Direct Access** | Services cannot directly access other services' databases |
| **Event-Driven** | Communication happens via events |
| **API-Driven** | When events are not appropriate, use internal APIs |

### 6.3 Database Technologies

| Database | Used By | Purpose |
|----------|---------|---------|
| **TimescaleDB** | Data Ingestion, AI Service | Time-series data (prices, predictions, indicators) |
| **PostgreSQL** | API Gateway, Alert Service | Relational data (users, alerts, export history) |
| **Redis** | Data Ingestion, AI Service, API Gateway | Caching (prices, predictions, API responses) |
| **MLflow** | AI Service | Model versioning and metadata |

---

## 7. Service Dependencies

### 7.1 Dependency Diagram

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

### 7.2 Dependency Matrix

| Service | Depends On | Dependency Type |
|---------|------------|-----------------|
| **Data Ingestion** | None | — |
| **AI Service** | Data Ingestion | Events (PriceUpdated, IndicatorUpdated) |
| **Alert Service** | Data Ingestion, AI Service | Events (PriceUpdated, IndicatorUpdated, PredictionGenerated) |
| **API Gateway** | AI Service, Alert Service | Events (PredictionGenerated, AlertTriggered, NotificationSent) |

---

## 8. Service Catalog Summary

| Service | Database | APIs | Events Produced | Events Consumed |
|---------|----------|------|-----------------|-----------------|
| **Data Ingestion** | TimescaleDB, Redis | Internal | PriceUpdated, IndicatorUpdated | None |
| **AI Service** | TimescaleDB, MLflow, Redis | Internal | PredictionGenerated | PriceUpdated, IndicatorUpdated |
| **API Gateway** | PostgreSQL | External | AlertAcknowledged, ExportCompleted, UserRegistered, UserLoggedIn | PredictionGenerated, AlertTriggered, NotificationSent |
| **Alert Service** | PostgreSQL | Internal | AlertTriggered, NotificationSent | PriceUpdated, PredictionGenerated, IndicatorUpdated, AlertAcknowledged |

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Metric | Target |
|--------|--------|
| API Response Time (cached) | < 200ms |
| API Response Time (non-cached) | < 500ms |
| Event Processing Latency | < 100ms |
| Prediction Generation | < 5s |

### 9.2 Availability

| Metric | Target |
|--------|--------|
| System Uptime | 99.5% |
| Data Freshness (BTC) | < 5 seconds |
| Data Freshness (Indicators) | < 24 hours |

### 9.3 Scalability

| Aspect | Strategy |
|--------|----------|
| Horizontal Scaling | All services stateless, can scale horizontally |
| Database Scaling | TimescaleDB hypertables, PostgreSQL read replicas |
| Caching | Redis cluster |
| Load Balancing | API Gateway behind load balancer |

---

## 10. Deployment

### 10.1 Deployment Strategy

| Service | Deployment Strategy |
|---------|---------------------|
| All Services | Docker containers |
| Orchestration | Kubernetes |
| CI/CD | GitHub Actions |
| Environment | Cloud (AWS/GCP/Azure) |

### 10.2 Ports

| Service | Port |
|---------|------|
| Data Ingestion | 8081 |
| AI Service | 8082 |
| API Gateway | 8080 |
| Alert Service | 8083 |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — all services defined |