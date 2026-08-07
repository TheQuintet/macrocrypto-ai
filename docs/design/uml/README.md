# UML Diagrams — MacroCrypto AI

This document contains all UML diagrams for the MacroCrypto AI platform using Mermaid syntax.

---

## 1. Domain Class Diagram [8.1]

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String passwordHash
        +String firstName
        +String lastName
        +Enum userType
        +DateTime createdAt
        +DateTime updatedAt
        +DateTime lastLoginAt
        +Boolean isActive
        +changePassword()
        +updateProfile()
        +activateAccount()
        +deactivateAccount()
        +recordLogin()
    }

    class Alert {
        +UUID id
        +UUID userId
        +Enum alertType
        +Decimal threshold
        +Enum condition
        +Enum horizon
        +Enum status
        +DateTime createdAt
        +DateTime triggeredAt
        +DateTime updatedAt
        +DateTime expiresAt
        +trigger()
        +dismiss()
        +disable()
        +enable()
        +isExpired()
        +shouldTrigger()
    }

    class BTCPrice {
        +UUID id
        +Decimal price
        +String symbol
        +String currency
        +DateTime timestamp
        +String source
        +Decimal volume
        +Decimal marketCap
        +isFresh()
        +getChangePercentage()
    }

    class Prediction {
        +UUID id
        +String symbol
        +Enum horizon
        +Decimal predictedPrice
        +Decimal lowerBound
        +Decimal upperBound
        +Integer confidenceLevel
        +DateTime generatedAt
        +String modelVersion
        +Enum status
        +isValid()
        +archive()
        +getRange()
    }

    class MacroIndicator {
        +UUID id
        +Enum indicatorType
        +Decimal value
        +Decimal previousValue
        +Decimal changePercent
        +DateTime timestamp
        +String source
        +Boolean isRevision
        +isFresh()
        +getTrend()
    }

    class Notification {
        +UUID id
        +UUID userId
        +Enum type
        +String title
        +String message
        +Enum channel
        +Enum status
        +DateTime createdAt
        +DateTime sentAt
        +DateTime readAt
        +markAsRead()
        +markAsSent()
        +send()
    }

    class ExportRequest {
        +UUID id
        +UUID userId
        +Enum dataType
        +Enum format
        +String timeframe
        +Enum status
        +String fileUrl
        +Long fileSize
        +DateTime createdAt
        +DateTime completedAt
        +startProcessing()
        +complete()
        +fail()
    }

    User "1" --> "0..*" Alert : owns
    User "1" --> "0..*" Notification : receives
    User "1" --> "0..*" ExportRequest : requests
```

---

## 2. Sequence Diagram: BTC Prediction Flow [8.2]

```mermaid
sequenceDiagram
    actor User
    participant APIGateway as API Gateway
    participant Redis as Redis Cache
    participant AIService as AI Service
    participant TimescaleDB as TimescaleDB

    User->>APIGateway: GET /api/v1/predict/btc?horizon=24h
    APIGateway->>APIGateway: Validate JWT Token
    APIGateway->>Redis: Check cache for predictions
    alt Cache Hit
        Redis-->>APIGateway: Return cached predictions
    else Cache Miss
        APIGateway->>AIService: Request predictions
        AIService->>TimescaleDB: Fetch latest predictions
        TimescaleDB-->>AIService: Return predictions
        AIService-->>APIGateway: Return predictions
        APIGateway->>Redis: Store in cache (TTL: 5 min)
    end
    APIGateway-->>User: Return predictions (JSON)
```

---

## 3. Sequence Diagram: Alert Trigger Flow [8.3]

```mermaid
sequenceDiagram
    participant DataIngestion as Data Ingestion Service
    participant RabbitMQ as RabbitMQ
    participant AlertService as Alert Service
    participant APIGateway as API Gateway
    participant User
    participant EmailService as Email Service

    DataIngestion->>RabbitMQ: Publish PriceUpdated
    RabbitMQ->>AlertService: Deliver PriceUpdated
    AlertService->>AlertService: Evaluate active alerts
    alt Alert Condition Met
        AlertService->>AlertService: Trigger alert
        AlertService->>APIGateway: Publish AlertTriggered
        APIGateway->>User: Send in-app notification
        APIGateway->>EmailService: Send email notification
        EmailService-->>User: Deliver email
        User->>APIGateway: Acknowledge alert
        APIGateway->>AlertService: Publish AlertAcknowledged
    end
```

---

## 4. Sequence Diagram: Data Ingestion Flow [8.4]

```mermaid
sequenceDiagram
    participant Scheduler as Scheduler
    participant DataIngestion as Data Ingestion Service
    participant CoinGecko as CoinGecko API
    participant FRED as FRED API
    participant TimescaleDB as TimescaleDB
    participant Redis as Redis
    participant RabbitMQ as RabbitMQ

    Scheduler->>DataIngestion: Trigger data fetch (hourly/daily)
    
    par BTC Price Fetch
        DataIngestion->>CoinGecko: GET /api/v3/simple/price?ids=bitcoin
        CoinGecko-->>DataIngestion: Return price data
        DataIngestion->>DataIngestion: Validate data
        DataIngestion->>TimescaleDB: Store price with timestamp
        DataIngestion->>Redis: Update current price cache
        DataIngestion->>RabbitMQ: Publish PriceUpdated
    and Macro Data Fetch
        DataIngestion->>FRED: GET /series/observations?series_id=CPIAUCSL
        FRED-->>DataIngestion: Return indicator data
        DataIngestion->>DataIngestion: Validate data
        DataIngestion->>TimescaleDB: Store indicator with timestamp
        DataIngestion->>RabbitMQ: Publish IndicatorUpdated
    end
```

---

## 5. Component Diagram [8.5]

```mermaid
graph TB
    subgraph "MacroCrypto AI Platform"
        subgraph "API Gateway"
            REST[REST Controllers]
            Auth[Authentication Middleware]
            RateLimit[Rate Limiting Middleware]
            UserService[User Service]
            ExportService[Export Service]
            EventProducer[Event Producer]
            EventConsumer[Event Consumer]
        end

        subgraph "AI Service"
            FeatureEng[Feature Engineering]
            ModelTraining[Model Training]
            PredictionGen[Prediction Generator]
            ModelRegistry[Model Registry]
            CacheManager[Cache Manager]
            AIEventConsumer[Event Consumer]
            AIEventProducer[Event Producer]
        end

        subgraph "Data Ingestion Service"
            CoinGeckoClient[CoinGecko Client]
            FREDClient[FRED Client]
            DataValidator[Data Validator]
            DataStorage[Data Storage]
            DataCacheManager[Cache Manager]
            DIEventProducer[Event Producer]
            Scheduler[Scheduler]
        end

        subgraph "Alert Service"
            AlertEngine[Alert Engine]
            AlertManager[Alert Manager]
            NotificationService[Notification Service]
            AlertEventConsumer[Event Consumer]
            AlertEventProducer[Event Producer]
        end
    end

    subgraph "External Systems"
        CoinGecko[CoinGecko API]
        FRED[FRED API]
        Email[SendGrid/AWS SES]
        MLflow[MLflow]
    end

    subgraph "Infrastructure"
        RabbitMQ[RabbitMQ]
        TimescaleDB[TimescaleDB]
        PostgreSQL[PostgreSQL]
        Redis[Redis]
    end

    %% Connections
    REST --> Auth --> RateLimit
    RateLimit --> UserService
    RateLimit --> ExportService
    
    CoinGeckoClient --> CoinGecko
    FREDClient --> FRED
    DataStorage --> TimescaleDB
    DataCacheManager --> Redis
    DIEventProducer --> RabbitMQ
    DIEventConsumer --> RabbitMQ
    
    PredictionGen --> ModelRegistry
    CacheManager --> Redis
    AIEventProducer --> RabbitMQ
    AIEventConsumer --> RabbitMQ
    
    NotificationService --> Email
    AlertManager --> PostgreSQL
    AlertEventProducer --> RabbitMQ
    AlertEventConsumer --> RabbitMQ
    
    UserService --> PostgreSQL
    ExportService --> EventProducer
    EventProducer --> RabbitMQ
    EventConsumer --> RabbitMQ
```

---

## 6. State Machine Diagram: Alerts [8.6]

```mermaid
stateDiagram-v2
    [*] --> Active: Alert Created
    
    Active --> Triggered: Condition Met
    Active --> Disabled: User Disables
    Active --> Expired: Timer Expires (One-Time)
    
    Triggered --> Dismissed: User Dismisses
    Triggered --> Archived: Auto-Archive (7 days)
    
    Disabled --> Active: User Enables
    
    Dismissed --> [*]
    Expired --> [*]
    Archived --> [*]
    
    note right of Active
        Alert is monitoring
        for trigger conditions
    end note
    
    note right of Triggered
        Alert condition has been met
        Notification sent to user
    end note
    
    note right of Disabled
        User has manually
        disabled the alert
    end note
    
    note right of Dismissed
        User has acknowledged
        and dismissed the alert
    end note
    
    note right of Expired
        One-time alert has
        expired without triggering
    end note
```

---

## 7. State Machine Diagram: Predictions [8.7]

```mermaid
stateDiagram-v2
    [*] --> Generated: Model generates prediction
    Generated --> Active: Prediction available for API
    Generated --> Archived: Prediction expired (beyond horizon)
    
    Active --> Updated: New prediction generated (same horizon)
    Active --> Archived: Prediction expired (beyond horizon)
    
    Updated --> Active: New prediction available
    Updated --> Archived: Prediction expired
    
    note right of Generated
        Prediction just created
        Not yet available to users
    end note
    
    note right of Active
        Prediction is available
        via API and dashboard
    end note
    
    note right of Updated
        New prediction replaces
        previous one
    end note
    
    note right of Archived
        Prediction no longer
        available (expired)
    end note
```

---

## 8. Deployment Diagram [8.8]

```mermaid
graph TB
    subgraph "Internet"
        User[User Browser/API Client]
    end

    subgraph "Kubernetes Cluster"
        subgraph "Ingress"
            LB[Load Balancer]
        end

        subgraph "API Gateway Pod"
            APIGateway[API Gateway]
        end

        subgraph "AI Service Pod"
            AIService[AI Service]
        end

        subgraph "Data Ingestion Pod"
            DataIngestion[Data Ingestion]
        end

        subgraph "Alert Service Pod"
            AlertService[Alert Service]
        end

        subgraph "RabbitMQ StatefulSet"
            RabbitMQ[RabbitMQ]
        end

        subgraph "TimescaleDB StatefulSet"
            TimescaleDB[TimescaleDB]
        end

        subgraph "PostgreSQL StatefulSet"
            PostgreSQL[PostgreSQL]
        end

        subgraph "Redis StatefulSet"
            Redis[Redis]
        end

        subgraph "MLflow Deployment"
            MLflow[MLflow]
        end
    end

    subgraph "External Services"
        CoinGecko[CoinGecko API]
        FRED[FRED API]
        Email[SendGrid/AWS SES]
        Prometheus[Prometheus]
        Grafana[Grafana]
    end

    User --> LB
    LB --> APIGateway
    
    APIGateway --> AIService
    APIGateway --> AlertService
    APIGateway --> PostgreSQL
    APIGateway --> Redis
    APIGateway --> RabbitMQ
    
    AIService --> TimescaleDB
    AIService --> Redis
    AIService --> MLflow
    AIService --> RabbitMQ
    
    DataIngestion --> TimescaleDB
    DataIngestion --> Redis
    DataIngestion --> RabbitMQ
    DataIngestion --> CoinGecko
    DataIngestion --> FRED
    
    AlertService --> PostgreSQL
    AlertService --> RabbitMQ
    AlertService --> Email
    
    Prometheus --> APIGateway
    Prometheus --> AIService
    Prometheus --> DataIngestion
    Prometheus --> AlertService
    
    Grafana --> Prometheus
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — all UML diagrams complete |