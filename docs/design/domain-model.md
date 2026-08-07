# Domain Model — MacroCrypto AI

This document defines the domain model for the MacroCrypto AI platform, including Entities, Value Objects, Aggregates, Domain Events, and Bounded Contexts.

---

## 1. Entities

Entities are objects that have a distinct identity that persists over time. They are defined by their identity, not their attributes.

### 1.1 User

| Attribute | Type | Description |
|-----------|------|-------------|
| **Identity** | UserId (UUID) | Unique identifier |
| email | String | User's email address (unique) |
| passwordHash | String | Hashed password |
| firstName | String | User's first name |
| lastName | String | User's last name |
| userType | Enum (GUEST, REGISTERED, ADMIN) | User's role |
| createdAt | DateTime | Account creation timestamp |
| updatedAt | DateTime | Last update timestamp |
| lastLoginAt | DateTime | Last login timestamp |
| isActive | Boolean | Account active status |

**Behavior:**
- `changePassword(oldPassword, newPassword)`
- `updateProfile(firstName, lastName)`
- `activateAccount()`
- `deactivateAccount()`
- `recordLogin()`

---

### 1.2 Alert

| Attribute | Type | Description |
|-----------|------|-------------|
| **Identity** | AlertId (UUID) | Unique identifier |
| userId | UserId | Owner of the alert |
| alertType | Enum (PRICE, PREDICTION_CHANGE, CONFIDENCE_CHANGE, MACRO_EVENT) | Type of alert |
| threshold | Decimal | Threshold value that triggers the alert |
| condition | Enum (REACHES, CROSSES_ABOVE, CROSSES_BELOW) | Condition for price alerts |
| horizon | Enum (24H, 7D) | Prediction horizon for prediction alerts |
| status | Enum (ACTIVE, TRIGGERED, DISMISSED, DISABLED, EXPIRED) | Current status |
| createdAt | DateTime | Creation timestamp |
| triggeredAt | DateTime | When the alert was triggered |
| updatedAt | DateTime | Last update timestamp |
| expiresAt | DateTime | Expiration timestamp (one-time alerts) |

**Behavior:**
- `trigger()`
- `dismiss()`
- `disable()`
- `enable()`
- `isExpired()`
- `shouldTrigger(currentValue)`

---

### 1.3 BTC Price

| Attribute | Type | Description |
|-----------|------|-------------|
| **Identity** | PriceId (UUID) | Unique identifier |
| price | Decimal | Current BTC price in USD |
| symbol | String | BTC (constant) |
| currency | String | USD (constant) |
| timestamp | DateTime | When the price was recorded |
| source | String | Data source (e.g., CoinGecko) |
| volume | Decimal | 24h trading volume |
| marketCap | Decimal | Current market cap |

**Behavior:**
- `isFresh(maxAgeSeconds)`
- `getChangePercentage(previousPrice)`

---

### 1.4 Prediction

| Attribute | Type | Description |
|-----------|------|-------------|
| **Identity** | PredictionId (UUID) | Unique identifier |
| symbol | String | BTC (constant) |
| horizon | Enum (24H, 7D) | Forecast horizon |
| predictedPrice | Decimal | Predicted price |
| lowerBound | Decimal | Lower bound of confidence interval |
| upperBound | Decimal | Upper bound of confidence interval |
| confidenceLevel | Percentage | Confidence level (70%, 85%, 95%) |
| generatedAt | DateTime | When the prediction was generated |
| modelVersion | String | Version of the model that generated it |
| status | Enum (PENDING, ACTIVE, ARCHIVED) | Current status |

**Behavior:**
- `isValid()`
- `archive()`
- `getRange()`

---

### 1.5 Macro Indicator

| Attribute | Type | Description |
|-----------|------|-------------|
| **Identity** | IndicatorId (UUID) | Unique identifier |
| indicatorType | Enum (CPI, INTEREST_RATE, GDP, UNEMPLOYMENT, M2, DXY, TREASURY_YIELD) | Type of indicator |
| value | Decimal | Current value |
| previousValue | Decimal | Previous value |
| changePercent | Decimal | Percentage change |
| timestamp | DateTime | When the data was recorded |
| source | String | Data source (e.g., FRED) |
| isRevision | Boolean | Whether this is a revision of previous data |

**Behavior:**
- `isFresh(maxAgeHours)`
- `getTrend()`

---

### 1.6 Notification

| Attribute | Type | Description |
|-----------|------|-------------|
| **Identity** | NotificationId (UUID) | Unique identifier |
| userId | UserId | Recipient user |
| type | Enum (ALERT, EVENT, SYSTEM) | Notification type |
| title | String | Notification title |
| message | String | Notification message |
| channel | Enum (IN_APP, EMAIL) | Delivery channel |
| status | Enum (PENDING, SENT, READ, FAILED) | Delivery status |
| createdAt | DateTime | Creation timestamp |
| sentAt | DateTime | When it was sent |
| readAt | DateTime | When it was read |

**Behavior:**
- `markAsRead()`
- `markAsSent()`
- `send()`

---

### 1.7 Export Request

| Attribute | Type | Description |
|-----------|------|-------------|
| **Identity** | ExportId (UUID) | Unique identifier |
| userId | UserId | Requesting user |
| dataType | Enum (PRICES, INDICATORS, CORRELATION, REGIMES) | Type of data to export |
| format | Enum (CSV, PNG, PDF) | Export format |
| timeframe | String | Time range (30d, 90d, 1y, 5y) |
| status | Enum (PENDING, PROCESSING, COMPLETED, FAILED) | Processing status |
| fileUrl | String | URL to download the exported file |
| fileSize | Bytes | Size of the exported file |
| createdAt | DateTime | Request timestamp |
| completedAt | DateTime | Completion timestamp |

**Behavior:**
- `startProcessing()`
- `complete(fileUrl, fileSize)`
- `fail(reason)`

---

## 2. Value Objects

Value Objects are immutable objects that are defined by their attributes, not their identity. Two value objects with the same attributes are considered identical.

### 2.1 UserId

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | UUID | Unique user identifier |

**Validation:**
- Must be a valid UUID

---

### 2.2 AlertId

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | UUID | Unique alert identifier |

**Validation:**
- Must be a valid UUID

---

### 2.3 Price

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | Decimal | Amount in USD |
| **Currency** | String | USD (constant) |

**Validation:**
- Must be > 0
- Must have 2 decimal places

---

### 2.4 Confidence Level

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | Percentage | 70%, 85%, or 95% |

**Validation:**
- Must be one of: 70, 85, 95

---

### 2.5 Price Range

| Attribute | Type | Description |
|-----------|------|-------------|
| lowerBound | Decimal | Minimum value |
| upperBound | Decimal | Maximum value |

**Validation:**
- lowerBound <= upperBound
- Both must be > 0

---

### 2.6 Percentage

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | Decimal | A percentage value |

**Validation:**
- Must be between -100 and 100

---

### 2.7 Email

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | String | User's email address |

**Validation:**
- Must be a valid email format

---

### 2.8 Password Hash

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | String | Hashed password |

**Generation:**
- Generated using bcrypt

---

### 2.9 Timestamp

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | DateTime | UTC timestamp |

**Validation:**
- Must be in UTC

---

### 2.10 Threshold

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | Decimal | Alert threshold value |

**Validation:**
- Must be > 0 (for price alerts)
- Must be between 1-10% (for prediction alerts)

---

### 2.11 Impact Level

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | Enum (HIGH, MEDIUM, LOW) | Impact level of an economic event |

---

### 2.12 Event Type

| Attribute | Type | Description |
|-----------|------|-------------|
| **Value** | Enum (FED, CPI, EMPLOYMENT, GDP) | Type of economic event |

---

## 3. Entities vs Value Objects — Summary

| Entity | Identity Type | Key Attributes |
|--------|---------------|----------------|
| User | UserId (UUID) | email, userType, isActive |
| Alert | AlertId (UUID) | userId, alertType, threshold, status |
| BTC Price | PriceId (UUID) | price, timestamp, volume |
| Prediction | PredictionId (UUID) | predictedPrice, horizon, confidenceLevel |
| Macro Indicator | IndicatorId (UUID) | indicatorType, value, timestamp |
| Notification | NotificationId (UUID) | userId, type, status |
| Export Request | ExportId (UUID) | userId, dataType, format, status |

| Value Object | Validation |
|--------------|------------|
| Price | > 0, 2 decimal places |
| Confidence Level | 70, 85, or 95 |
| Price Range | lowerBound <= upperBound |
| Percentage | -100 to 100 |
| Email | Valid email format |
| Timestamp | UTC format |
| Threshold | > 0 or 1-10% |
| Impact Level | HIGH, MEDIUM, LOW |
| Event Type | FED, CPI, EMPLOYMENT, GDP |

---

## 4. Aggregates

Aggregates are clusters of domain objects that are treated as a single unit. Each aggregate has a root entity (the Aggregate Root) that acts as the entry point for all operations on the aggregate.

---

### 4.1 User Aggregate

**Aggregate Root:** User

**Entities:**
- User (root)
- Alert (child)

**Value Objects:**
- UserId
- Email
- Password Hash
- Timestamp

**Invariants:**
- A user must have a unique email
- A user can be either active or inactive
- Deactivated users cannot create new alerts

**Operations:**
- `User.create(email, password, firstName, lastName)`
- `User.activate()`
- `User.deactivate()`
- `User.addAlert(alertType, threshold, condition)`
- `User.removeAlert(alertId)`
- `User.updateAlert(alertId, alertData)`
- `User.getAlerts()`

**Consistency Boundary:**
- All alerts belonging to a user are updated together when the user's status changes
- Alert creation/update requires user validity

---

### 4.2 Alert Aggregate

**Aggregate Root:** Alert

**Entities:**
- Alert (root)

**Value Objects:**
- AlertId
- Threshold
- Impact Level (for macro events)
- Timestamp

**Invariants:**
- An alert must have a valid threshold value
- An alert must have a valid alert type
- An alert must have a valid status (Active, Triggered, Dismissed, Disabled, Expired)
- A triggered alert cannot be re-triggered without resetting
- An expired alert cannot be re-activated

**Operations:**
- `Alert.create(alertType, threshold, condition, horizon)`
- `Alert.trigger(currentValue)`
- `Alert.dismiss()`
- `Alert.disable()`
- `Alert.enable()`
- `Alert.checkCondition(currentValue)`

**Consistency Boundary:**
- Alert state changes affect the alert's ability to trigger
- Triggering an alert creates a notification
- Alert status changes are recorded for audit

---

### 4.3 Prediction Aggregate

**Aggregate Root:** Prediction

**Entities:**
- Prediction (root)

**Value Objects:**
- PredictionId
- Confidence Level
- Price Range (upper/lower bounds)
- Timestamp

**Invariants:**
- A prediction must have a valid horizon (24h or 7d)
- A prediction must have a valid confidence level (70%, 85%, or 95%)
- lowerBound must be <= predictedPrice <= upperBound
- A prediction cannot be archived if it is still valid

**Operations:**
- `Prediction.generate(predictedPrice, lowerBound, upperBound, confidenceLevel, horizon)`
- `Prediction.archive()`
- `Prediction.getAccuracy()`

**Consistency Boundary:**
- Predictions are generated by the AI Service
- Predictions are immutable once generated (only archived)
- Predictions trigger alerts in the Alert Service

---

### 4.4 BTC Price Aggregate

**Aggregate Root:** BTC Price

**Entities:**
- BTC Price (root)

**Value Objects:**
- Price
- Timestamp

**Invariants:**
- Price must be > 0
- Price must have a valid timestamp
- Price must be from a known source

**Operations:**
- `BTCPrice.record(price, volume, marketCap)`
- `BTCPrice.getChangePercentage(previousPrice)`
- `BTCPrice.isFresh(maxAgeSeconds)`

**Consistency Boundary:**
- Each price is independent and immutable
- Historical prices are stored for accuracy tracking
- Current price is published to the PriceUpdated event

---

### 4.5 Macro Indicator Aggregate

**Aggregate Root:** Macro Indicator

**Entities:**
- Macro Indicator (root)

**Value Objects:**
- Indicator Type
- Percentage
- Timestamp

**Invariants:**
- Each indicator must have a unique combination of type and timestamp
- Value must be within expected range for the indicator type

**Operations:**
- `MacroIndicator.record(indicatorType, value)`
- `MacroIndicator.getTrend()`
- `MacroIndicator.isFresh(maxAgeHours)`

**Consistency Boundary:**
- Each indicator value is independent
- Historical indicators are immutable
- Current indicators are used for regime detection

---

### 4.6 Notification Aggregate

**Aggregate Root:** Notification

**Entities:**
- Notification (root)

**Value Objects:**
- NotificationId
- Timestamp

**Invariants:**
- A notification must have a valid type
- A notification must have a valid channel
- A notification must have a recipient user ID

**Operations:**
- `Notification.send()`
- `Notification.markAsRead()`
- `Notification.markAsSent()`
- `Notification.fail()`

**Consistency Boundary:**
- Notifications are created from alerts or events
- Notifications are independent of their source
- Notifications track delivery and read status

---

### 4.7 Export Request Aggregate

**Aggregate Root:** Export Request

**Entities:**
- Export Request (root)

**Value Objects:**
- ExportId
- Timestamp

**Invariants:**
- dataType must be valid (PRICES, INDICATORS, CORRELATION, REGIMES)
- format must be valid (CSV, PNG, PDF)
- timeframe must be valid (30d, 90d, 1y, 5y)

**Operations:**
- `ExportRequest.startProcessing()`
- `ExportRequest.complete(fileUrl, fileSize)`
- `ExportRequest.fail(reason)`

**Consistency Boundary:**
- Each export request is independent
- Export requests track processing status
- Completed exports are available for download

---

### 4.8 Aggregate Relationships

```
┌─────────────┐     ┌─────────────┐
│    User     │────▶│   Alerts    │
│  (Aggregate │ 1..n │ (Child      │
│    Root)    │     │  Entities)  │
└─────────────┘     └─────────────┘

┌─────────────┐
│  Prediction │
│  (Aggregate │
│    Root)    │
└─────────────┘

┌─────────────┐
│  BTC Price  │
│  (Aggregate │
│    Root)    │
└─────────────┘

┌─────────────┐     ┌─────────────┐
│   Macro     │     │   Regime    │
│  Indicator  │────▶│  Detection  │
│  (Aggregate │ 1..n │  (Process)  │
│    Root)    │     │             │
└─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐
│  Notification│────▶│   Events    │
│  (Aggregate │ 1   │  (Context)  │
│    Root)    │     │             │
└─────────────┘     └─────────────┘

┌─────────────┐
│   Export    │
│   Request   │
│  (Aggregate │
│    Root)    │
└─────────────┘
```

---

### 4.9 Aggregate Summary

| Aggregate | Root Entity | Child Entities | Key Invariants |
|-----------|-------------|----------------|----------------|
| **User** | User | Alert | Unique email, active status |
| **Alert** | Alert | — | Valid threshold, valid status |
| **Prediction** | Prediction | — | Valid horizon, lowerBound <= price <= upperBound |
| **BTC Price** | BTC Price | — | Price > 0, valid timestamp |
| **Macro Indicator** | Macro Indicator | — | Unique type+timestamp, valid range |
| **Notification** | Notification | — | Valid type, valid channel |
| **Export Request** | Export Request | — | Valid dataType, format, timeframe |

---
## 5. Domain Events

Domain Events represent significant changes in the state of the system that are of interest to other parts of the system. They are used to communicate changes between aggregates and services.

---

### 5.1 Event Catalog

| Event Name | Producer | Consumers | Description |
|------------|----------|-----------|-------------|
| **PriceUpdated** | Data Ingestion Service | AI Service, Alert Service | Published when a new BTC price is recorded |
| **PredictionGenerated** | AI Service | API Gateway, Alert Service | Published when a new prediction is generated |
| **IndicatorUpdated** | Data Ingestion Service | AI Service, Alert Service | Published when a new macro indicator value is recorded |
| **AlertTriggered** | Alert Service | API Gateway | Published when an alert condition is met |
| **NotificationSent** | Alert Service | API Gateway | Published when a notification is sent to a user |
| **AlertAcknowledged** | API Gateway | Alert Service | Published when a user acknowledges/dismisses an alert |
| **ExportCompleted** | API Gateway | — | Published when an export request is completed |
| **UserRegistered** | API Gateway | — | Published when a new user registers |
| **UserLoggedIn** | API Gateway | — | Published when a user logs in |

---

### 5.2 Event Details

#### 5.2.1 PriceUpdated

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

#### 5.2.2 PredictionGenerated

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

#### 5.2.3 IndicatorUpdated

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

#### 5.2.4 AlertTriggered

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

#### 5.2.5 NotificationSent

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

#### 5.2.6 AlertAcknowledged

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

#### 5.2.7 ExportCompleted

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

#### 5.2.8 UserRegistered

| Attribute | Type | Description |
|-----------|------|-------------|
| userId | UUID | Unique identifier of the user |
| email | String | User's email address |
| firstName | String | User's first name |
| lastName | String | User's last name |
| registeredAt | DateTime | When the user registered |

**Example:**
```json
{
  "eventType": "UserRegistered",
  "userId": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "registeredAt": "2026-08-07T09:00:00Z"
}
```

---

#### 5.2.9 UserLoggedIn

| Attribute | Type | Description |
|-----------|------|-------------|
| userId | UUID | Unique identifier of the user |
| email | String | User's email address |
| loggedInAt | DateTime | When the user logged in |
| ipAddress | String | IP address of the login request |

**Example:**
```json
{
  "eventType": "UserLoggedIn",
  "userId": "b2c3d4e5-f6g7-8901-bcde-f23456789012",
  "email": "user@example.com",
  "loggedInAt": "2026-08-07T10:00:00Z",
  "ipAddress": "192.168.1.100"
}
```

---

### 5.3 Event Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVENT FLOW DIAGRAM                              │
│                                                                             │
│  ┌──────────────────┐    PriceUpdated    ┌──────────────────┐               │
│  │  Data Ingestion  │──────────────────▶│   AI Service     │               │
│  │     Service      │                    │                  │               │
│  └──────────────────┘                    └────────┬─────────┘               │
│           │                                      │                          │
│           │ IndicatorUpdated                     │ PredictionGenerated     │
│           │                                      │                          │
│           ▼                                      ▼                          │
│  ┌──────────────────┐                    ┌──────────────────┐               │
│  │   Alert Service  │◀──────────────────│   API Gateway    │               │
│  │                  │                    │                  │               │
│  └────────┬─────────┘                    └────────┬─────────┘               │
│           │                                      │                          │
│           │ AlertTriggered                       │ UserRegistered          │
│           │                                      │ UserLoggedIn            │
│           ▼                                      │                          │
│  ┌──────────────────┐                    ┌──────────────────┐               │
│  │  Notification    │                    │   Export Service │               │
│  │     Service      │                    │                  │               │
│  └──────────────────┘                    └────────┬─────────┘               │
│                                                    │                          │
│                                                    │ ExportCompleted         │
│                                                    ▼                          │
│                                           ┌──────────────────┐               │
│                                           │   API Gateway    │               │
│                                           │                  │               │
│                                           └──────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 5.4 Event Summary

| Event | Producer | Primary Consumers | Purpose |
|-------|----------|-------------------|---------|
| PriceUpdated | Data Ingestion | AI Service, Alert Service | Trigger model updates and alert evaluation |
| PredictionGenerated | AI Service | API Gateway, Alert Service | Serve predictions and evaluate alerts |
| IndicatorUpdated | Data Ingestion | AI Service, Alert Service | Update macro context and evaluate alerts |
| AlertTriggered | Alert Service | API Gateway | Notify user via API |
| NotificationSent | Alert Service | API Gateway | Track notification delivery |
| AlertAcknowledged | API Gateway | Alert Service | Update alert status |
| ExportCompleted | Export Service | API Gateway | Notify user of export completion |
| UserRegistered | API Gateway | — | Track user registration |
| UserLoggedIn | API Gateway | — | Track user activity |

---
## 6. Bounded Contexts

Bounded Contexts are logical boundaries that define where a particular domain model applies. Each bounded context has its own ubiquitous language, entities, value objects, and aggregates.

---

### 6.1 Context Map

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌───────────────────────────────┐    ┌───────────────────────────────────┐    │
│  │                               │    │                                   │    │
│  │    Data Context              │    │       AI Context                  │    │
│  │                               │    │                                   │    │
│  │  - BTC Price Collection      │    │  - Prediction Generation          │    │
│  │  - Macro Data Collection     │    │  - Model Training                 │    │
│  │  - Data Validation           │    │  - Accuracy Tracking              │    │
│  │  - Historical Data Storage   │    │  - Feature Engineering            │    │
│  │                               │    │                                   │    │
│  └───────────────┬───────────────┘    └───────────────┬───────────────────┘    │
│                  │                                      │                       │
│                  │ PriceUpdated                         │ PredictionGenerated   │
│                  │ IndicatorUpdated                     │                       │
│                  ▼                                      ▼                       │
│  ┌───────────────────────────────┐    ┌───────────────────────────────────┐    │
│  │                               │    │                                   │    │
│  │    Alerts Context            │    │       API Context                 │    │
│  │                               │    │                                   │    │
│  │  - Alert Evaluation          │    │  - REST API Endpoints             │    │
│  │  - Alert Management          │    │  - Authentication                 │    │
│  │  - Notification Delivery     │    │  - Rate Limiting                  │    │
│  │  - Event Monitoring          │    │  - User Management                │    │
│  │                               │    │  - Export Requests               │    │
│  │                               │    │                                   │    │
│  └───────────────────────────────┘    └───────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### 6.2 Data Context

**Purpose:**
Responsible for collecting, validating, and storing all data used by the platform.

**Core Concepts:**
- BTC Price
- Macro Indicator
- Historical Data
- Data Validation

**Entities:**
- BTC Price
- Macro Indicator

**Value Objects:**
- Price
- Timestamp
- Indicator Type

**Events Produced:**
- PriceUpdated
- IndicatorUpdated

**Events Consumed:**
- None

**Key Responsibilities:**
- Fetch BTC price data from CoinGecko
- Fetch macro indicator data from FRED API
- Validate incoming data
- Store data in TimescaleDB
- Publish events when new data arrives

---

### 6.3 AI Context

**Purpose:**
Responsible for generating BTC price predictions using machine learning models.

**Core Concepts:**
- Prediction
- Model Training
- Feature Engineering
- Accuracy Tracking

**Entities:**
- Prediction
- Model Version

**Value Objects:**
- Confidence Level
- Price Range
- Feature Set

**Events Produced:**
- PredictionGenerated

**Events Consumed:**
- PriceUpdated
- IndicatorUpdated

**Key Responsibilities:**
- Generate 24h and 7d BTC price predictions
- Train and retrain Prophet model
- Track prediction accuracy
- Manage model versions
- Cache predictions for performance

---

### 6.4 Alerts Context

**Purpose:**
Responsible for evaluating alert conditions and delivering notifications.

**Core Concepts:**
- Alert
- Notification
- Event Monitoring
- User Preferences

**Entities:**
- Alert
- Notification

**Value Objects:**
- AlertId
- Threshold
- Impact Level

**Events Produced:**
- AlertTriggered
- NotificationSent

**Events Consumed:**
- PriceUpdated
- PredictionGenerated
- IndicatorUpdated
- AlertAcknowledged

**Key Responsibilities:**
- Evaluate alerts against incoming events
- Manage alert lifecycle (create, trigger, dismiss, disable)
- Deliver notifications via email and in-app
- Track notification delivery status

---

### 6.5 API Context

**Purpose:**
Responsible for exposing platform functionality to external users.

**Core Concepts:**
- User
- API Endpoint
- Authentication
- Export Request

**Entities:**
- User
- Export Request

**Value Objects:**
- UserId
- ExportId
- Email

**Events Produced:**
- AlertAcknowledged
- ExportCompleted
- UserRegistered
- UserLoggedIn

**Events Consumed:**
- PredictionGenerated
- AlertTriggered
- NotificationSent

**Key Responsibilities:**
- Expose REST API endpoints
- Authenticate users (JWT)
- Rate limiting
- Manage user accounts
- Handle export requests

---

### 6.6 Context Summary

| Bounded Context | Primary Entities | Produced Events | Consumed Events | Database |
|-----------------|------------------|-----------------|-----------------|----------|
| **Data Context** | BTC Price, Macro Indicator | PriceUpdated, IndicatorUpdated | None | TimescaleDB |
| **AI Context** | Prediction, Model Version | PredictionGenerated | PriceUpdated, IndicatorUpdated | TimescaleDB, MLflow |
| **Alerts Context** | Alert, Notification | AlertTriggered, NotificationSent | PriceUpdated, PredictionGenerated, IndicatorUpdated, AlertAcknowledged | PostgreSQL |
| **API Context** | User, Export Request | AlertAcknowledged, ExportCompleted, UserRegistered, UserLoggedIn | PredictionGenerated, AlertTriggered, NotificationSent | PostgreSQL |

---

### 6.7 Context Boundaries and Relationships

```
┌─────────────────────────────┐
│       Data Context          │
│                             │
│  BTC Price, Macro Indicator │
│  TimescaleDB                │
└──────────┬──────────────────┘
           │
           │ PriceUpdated, IndicatorUpdated
           │
           ▼
┌─────────────────────────────┐
│       AI Context            │
│                             │
│  Prediction                 │
│  TimescaleDB, MLflow        │
└──────────┬──────────────────┘
           │
           │ PredictionGenerated
           │
           ▼
┌─────────────────────────────┐
│       Alerts Context        │
│                             │
│  Alert, Notification        │
│  PostgreSQL                 │
└──────────┬──────────────────┘
           │
           │ AlertTriggered, NotificationSent
           │
           ▼
┌─────────────────────────────┐
│       API Context           │
│                             │
│  User, Export Request       │
│  PostgreSQL                 │
└─────────────────────────────┘
```

---

### 6.8 Context Dependencies

| Context | Depends On | Dependency Type |
|---------|------------|-----------------|
| Data Context | None | — |
| AI Context | Data Context | Events |
| Alerts Context | Data Context, AI Context | Events |
| API Context | AI Context, Alerts Context | Events, API |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — Entities and Value Objects |
| 1.1 | 2026-08-07 | Sid | Added Aggregates section |
| 1.2 | 2026-08-07 | Sid | Added Domain Events section |
| 1.3 | 2026-08-07 | Sid | Added Bounded Contexts section |