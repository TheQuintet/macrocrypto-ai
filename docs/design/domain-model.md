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

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version — Entities and Value Objects |