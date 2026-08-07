# C4 Model — MacroCrypto AI

This document defines the C4 Model (Context, Container, Component diagrams) for the MacroCrypto AI platform.

---

## 1. C4 Context Diagram

The Context Diagram shows the system boundaries, external actors, and external systems.

### 1.1 Actors

| Actor | Description |
|-------|-------------|
| **BTC Trader** | User who trades BTC using predictions and alerts |
| **Investment Analyst** | User who researches BTC and macro data |
| **Platform User** | General user of the platform |

### 1.2 External Systems

| System | Description |
|--------|-------------|
| **CoinGecko API** | Provides BTC price data |
| **FRED API** | Provides macroeconomic indicator data |
| **SendGrid / AWS SES** | Email delivery service |
| **MLflow** | Model versioning and tracking |

### 1.3 Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                          ┌─────────────────────┐                           │
│                          │                     │                           │
│                          │   BTC Trader        │                           │
│                          │                     │                           │
│                          └──────────┬──────────┘                           │
│                                     │                                      │
│                          ┌──────────┼──────────┐                           │
│                          │          │          │                           │
│                          ▼          ▼          ▼                           │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                                                                   │    │
│  │                    MacroCrypto AI Platform                        │    │
│  │                                                                   │    │
│  │  - BTC Price Predictions (24h/7d)                                │    │
│  │  - Macroeconomic Indicators                                      │    │
│  │  - Correlation Analysis                                          │    │
│  │  - Alerts & Notifications                                        │    │
│  │  - Data Exports                                                  │    │
│  │                                                                   │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                          │            │            │                      │
│                          ▼            ▼            ▼                      │
│                    ┌─────────────────────────────────────┐               │
│                    │   Investment Analyst  Platform User │               │
│                    └─────────────────────────────────────┘               │
│                                                                             │
│  External Systems:                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ CoinGecko   │  │   FRED      │  │  SendGrid/  │  │   MLflow    │    │
│  │    API      │  │    API      │  │  AWS SES    │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. C4 Container Diagram

The Container Diagram shows the 4 microservices and their dependencies.

### 2.1 Containers

| Container | Type | Description |
|-----------|------|-------------|
| **Data Ingestion Service** | Microservice | Collects and stores BTC and macro data |
| **AI Service** | Microservice | Generates BTC price predictions |
| **API Gateway** | Microservice | REST API and WebSocket endpoints |
| **Alert Service** | Microservice | Alert evaluation and notifications |

### 2.2 Container Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        MacroCrypto AI                               │   │
│  │                                                                     │   │
│  │  ┌─────────────────────┐    ┌──────────────────────────────────┐   │   │
│  │  │                     │    │                                  │   │   │
│  │  │  Data Ingestion     │───▶│          RabbitMQ               │   │   │
│  │  │     Service         │    │          (Broker)                │   │   │
│  │  │                     │    │                                  │   │   │
│  │  │  - CoinGecko API    │    └──────────────────────────────────┘   │   │
│  │  │  - FRED API         │                     │                     │   │
│  │  └─────────────────────┘                     │                     │   │
│  │                                               ▼                     │   │
│  │  ┌─────────────────────┐    ┌──────────────────────────────────┐   │   │
│  │  │                     │    │                                  │   │   │
│  │  │   TimescaleDB       │◀───│       AI Service                │   │   │
│  │  │   (Data Storage)    │    │                                  │   │   │
│  │  │                     │    │  - Prophet Model                │   │   │
│  │  └─────────────────────┘    │  - MLflow                       │   │   │
│  │                             │                                  │   │   │
│  │  ┌─────────────────────┐    └──────────────────────────────────┘   │   │
│  │  │                     │                     │                     │   │
│  │  │   Redis             │◀────────────────────┘                     │   │
│  │  │   (Cache)           │                     │                     │   │
│  │  │                     │                     │                     │   │
│  │  └─────────────────────┘                     ▼                     │   │
│  │                                       ┌──────────────────────┐    │   │
│  │  ┌─────────────────────┐             │                      │    │   │
│  │  │                     │             │   API Gateway        │    │   │
│  │  │   PostgreSQL        │◀────────────│   (REST + WebSocket) │    │   │
│  │  │   (Alerts, Users)   │             │                      │    │   │
│  │  │                     │             └──────────────────────┘    │   │
│  │  └─────────────────────┘                     │                     │   │
│  │                                               │                     │   │
│  │                                       ┌───────┼───────┐            │   │
│  │                                       │       │       │            │   │
│  │                                       ▼       ▼       ▼            │   │
│  │                                 ┌─────────┐ ┌─────────┐ ┌───────┐ │   │
│  │                                 │ Traders │ │Analysts │ │Users  │ │   │
│  │                                 └─────────┘ └─────────┘ └───────┘ │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  External APIs:                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ CoinGecko   │  │   FRED      │  │  SendGrid/  │  │   MLflow    │    │
│  │    API      │  │    API      │  │  AWS SES    │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. C4 Component Diagram

The Component Diagram shows the internal components of each service.

### 3.1 API Gateway Components

| Component | Responsibility |
|-----------|----------------|
| **REST Controllers** | Handle HTTP requests for each endpoint |
| **Authentication Middleware** | Validate JWT tokens |
| **Rate Limiting Middleware** | Enforce rate limits |
| **Validation Service** | Validate request data |
| **User Service** | Manage user accounts |
| **Export Service** | Handle data exports |
| **Event Producer** | Publish events to RabbitMQ |
| **Event Consumer** | Consume events from RabbitMQ |

### 3.2 AI Service Components

| Component | Responsibility |
|-----------|----------------|
| **Feature Engineering** | Transform raw data into model features |
| **Model Training** | Train Prophet model |
| **Prediction Generator** | Generate 24h and 7d predictions |
| **Model Registry** | Manage model versions (MLflow) |
| **Cache Manager** | Cache predictions in Redis |
| **Event Consumer** | Consume PriceUpdated, IndicatorUpdated |
| **Event Producer** | Publish PredictionGenerated |

### 3.3 Data Ingestion Components

| Component | Responsibility |
|-----------|----------------|
| **CoinGecko Client** | Fetch BTC price data |
| **FRED Client** | Fetch macro indicator data |
| **Data Validator** | Validate incoming data |
| **Data Storage** | Store data in TimescaleDB |
| **Cache Manager** | Cache current price in Redis |
| **Event Producer** | Publish PriceUpdated, IndicatorUpdated |
| **Scheduler** | Schedule periodic data fetches |

### 3.4 Alert Service Components

| Component | Responsibility |
|-----------|----------------|
| **Alert Engine** | Evaluate alert conditions |
| **Alert Manager** | CRUD operations for alerts |
| **Notification Service** | Send email and in-app notifications |
| **Event Consumer** | Consume PriceUpdated, PredictionGenerated, IndicatorUpdated |
| **Event Producer** | Publish AlertTriggered, NotificationSent |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — all diagrams complete |