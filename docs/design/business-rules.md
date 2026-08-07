# Business Rules — MacroCrypto AI

This document defines the business rules that govern the MacroCrypto AI platform.

---

## 1. Alert Threshold Rules

### 1.1 Price Alerts

| Rule | Description |
|------|-------------|
| **Threshold** | User configurable (any positive price in USD) |
| **Alert Types** | Price reaches, crosses above, crosses below |
| **Default** | No default — user must set their own threshold |
| **Validation** | Must be > $0 |
| **Active Limit** | No limit on number of active alerts per user |

**Example:**
```
User sets alert: "Alert me when BTC reaches $85,000"
Alert type: "Price reaches"
```

---

### 1.2 Prediction Change Alerts

| Rule | Description |
|------|-------------|
| **Threshold** | User configurable (1%, 2%, 5%, 10%) |
| **Default** | 2% |
| **What's Monitored** | Change in predicted price (24h and 7d horizons) |
| **Trigger** | New prediction differs from previous by >= threshold |
| **Check Frequency** | Hourly |

**Example:**
```
Previous prediction: $82,450
New prediction: $84,500
Change: 2.5%
Alert triggers (threshold = 2%)
```

---

### 1.3 Confidence Change Alerts

| Rule | Description |
|------|-------------|
| **Threshold** | User configurable (default ±5%) |
| **What's Monitored** | Change in confidence level percentage |
| **Trigger** | Confidence level changes by >= threshold |

**Example:**
```
Previous confidence: 85%
New confidence: 78%
Change: -7%
Alert triggers (threshold = 5%)
```

---

### 1.4 Macro Event Alerts

| Rule | Description |
|------|-------------|
| **Timing Options** | 1 day before, 12 hours before, 1 hour before |
| **Default** | 1 day before |
| **Event Types** | Fed meetings, CPI releases, Employment reports, GDP releases |
| **Impact Levels** | High (CPI, Fed), Medium (GDP, Employment) |

---

## 2. Trading Recommendation Logic

### 2.1 Recommendation Types

| Recommendation | Condition |
|----------------|-----------|
| **BUY** | Prediction trend is bullish AND macro context supports it |
| **SELL** | Prediction trend is bearish AND macro context supports it |
| **HOLD** | Predictions are neutral or conflicting signals |

### 2.2 Entry Price Calculation

| Rule | Description |
|------|-------------|
| **For BUY** | Entry price = current price (or slight premium if trend is strong) |
| **For SELL** | Entry price = current price (or slight discount if trend is strong) |
| **For HOLD** | No entry price displayed |

### 2.3 Stop-Loss and Take-Profit

| Rule | Description |
|------|-------------|
| **Stop-Loss** | Derived from confidence interval lower bound (e.g., -2% from entry) |
| **Take-Profit 1** | Conservative target (e.g., +3% from entry) |
| **Take-Profit 2** | Moderate target (e.g., +5% from entry) |
| **Take-Profit 3** | Aggressive target (e.g., +8% from entry) |

### 2.4 Risk Level

| Risk Level | Conditions |
|------------|------------|
| **Low** | Volatility < 2% AND confidence > 85% |
| **Medium** | Volatility 2-5% OR confidence 70-85% |
| **High** | Volatility > 5% OR confidence < 70% |

### 2.5 Risk-Reward Ratio

| Rule | Description |
|------|-------------|
| **Formula** | (Take Profit - Entry) / (Entry - Stop Loss) |
| **Minimum** | Must be > 1:1 to recommend a trade |
| **Display** | e.g., "1:2.5" |

---

## 3. Correlation Strength Rules

### 3.1 Correlation Strength

| Strength | Range | Color | Meaning |
|----------|-------|-------|---------|
| **Strong** | > 0.7 | 🟢 Green | Strong relationship |
| **Medium** | 0.3 - 0.7 | 🟡 Yellow | Moderate relationship |
| **Weak** | < 0.3 | 🔴 Red | Weak relationship |

### 3.2 Correlation Direction

| Direction | Value | Arrow | Meaning |
|-----------|-------|-------|---------|
| **Positive** | > 0 | ↑ | BTC moves in same direction as indicator |
| **Negative** | < 0 | ↓ | BTC moves in opposite direction to indicator |

### 3.3 Statistical Significance

| Rule | Description |
|------|-------------|
| **Significant** | p-value < 0.05 |
| **Not Significant** | p-value >= 0.05 |

### 3.4 Interpretation Guidelines

| Correlation Pattern | Market Implication |
|---------------------|-------------------|
| **Strong positive** | BTC moves with macro indicator (e.g., inflation rising = BTC rising) |
| **Strong negative** | BTC moves opposite to macro indicator (e.g., rates rising = BTC falling) |
| **Weak correlation** | BTC is decoupled from that macro factor |
| **Changing correlation** | Market regime shift — monitor closely |

---

## 4. Regime Classification Rules

### 4.1 Regime Types

| Regime | Classification Criteria |
|--------|-------------------------|
| **High Inflation** | CPI > 3% |
| **Low Inflation** | CPI < 2% |
| **Rising Rates** | Interest rates increasing over 3 months |
| **Falling Rates** | Interest rates decreasing over 3 months |
| **Recession** | GDP negative growth for 2 consecutive quarters |
| **Growth** | GDP positive growth > 2% |

### 4.2 Regime Performance Metrics

| Metric | Description |
|--------|-------------|
| **Average Return** | Mean BTC return during regime |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Volatility** | Standard deviation of returns |
| **Sharpe Ratio** | Risk-adjusted return |

### 4.3 Regime Transition Rules

| Transition | Condition |
|------------|-----------|
| **High Inflation → Low Inflation** | CPI drops below 2% |
| **Rising Rates → Falling Rates** | Rates peak and start decreasing |
| **Growth → Recession** | GDP negative for 2 consecutive quarters |
| **Recession → Growth** | GDP positive for 2 consecutive quarters |

### 4.4 Interpretation Guidelines

| Regime | Typical BTC Behavior |
|--------|---------------------|
| **High Inflation** | Historically bullish (hedge narrative) |
| **Low Inflation** | Neutral to bearish |
| **Rising Rates** | Bearish pressure (risk-off) |
| **Falling Rates** | Bullish (risk-on) |
| **Recession** | Bearish (risk-off, liquidity crunch) |
| **Growth** | Bullish (risk-on) |

---

## 5. Data Quality Rules

### 5.1 BTC Price Data

| Rule | Description |
|------|-------------|
| **Minimum Data** | 90 days of historical data for model training |
| **Data Freshness** | Price updates < 5 seconds |
| **Missing Values** | Interpolate or remove |
| **Duplicate Prevention** | Unique timestamps enforced |
| **Source** | CoinGecko API |
| **Outlier Handling** | Winsorize values beyond 3 standard deviations |

### 5.2 Macro Indicator Data

| Rule | Description |
|------|-------------|
| **Data Freshness** | Updated within 24 hours |
| **Missing Values** | Forward-fill until new data arrives |
| **Source** | FRED API |
| **Outlier Handling** | Flag for manual review |
| **Data Revision Handling** | Replace historical values when revisions occur |

### 5.3 Data Quality Monitoring

| Metric | Alert Threshold |
|--------|-----------------|
| **Completeness** | Missing > 5% of expected data points |
| **Accuracy** | Values outside expected ranges |
| **Timeliness** | No new data in > 48 hours |
| **Consistency** | Significant revisions (> 10% change) |

---

## 6. User Permission Rules

### 6.1 User Types

| User Type | Permissions |
|-----------|-------------|
| **Guest** | View public data only |
| **Registered User** | View all data, create alerts, export data |
| **Admin** | All permissions + user management |

### 6.2 Feature Access by User Type

| Feature | Guest | Registered User | Admin |
|---------|-------|-----------------|-------|
| View BTC price | ✅ | ✅ | ✅ |
| View macro indicators | ✅ | ✅ | ✅ |
| View predictions | ❌ | ✅ | ✅ |
| Create alerts | ❌ | ✅ | ✅ |
| Export data | ❌ | ✅ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

### 6.3 Rate Limits by User Type

| User Type | API Rate Limit |
|-----------|----------------|
| **Guest** | 10 requests/minute |
| **Registered User** | 100 requests/minute |
| **Admin** | 1000 requests/minute |

---

## 7. Alert Lifecycle Rules

### 7.1 Alert States

| State | Description |
|-------|-------------|
| **Active** | Alert is monitoring for trigger conditions |
| **Triggered** | Alert condition has been met |
| **Dismissed** | User has acknowledged/ dismissed the alert |
| **Disabled** | User has manually disabled the alert |
| **Expired** | Alert has expired (one-time alerts only) |

### 7.2 Alert Lifecycle

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

### 7.3 Alert Retention

| Alert Type | Retention Period |
|------------|------------------|
| **Active Alerts** | Indefinitely (until triggered/disabled) |
| **Triggered Alerts** | 7 days after triggering |
| **Dismissed Alerts** | 30 days after dismissal |
| **Expired Alerts** | 30 days after expiry |

---

## 8. Performance Requirements

### 8.1 Response Time Targets

| Operation | Target | Acceptable | Unacceptable |
|-----------|--------|------------|--------------|
| BTC price display | < 1s | < 2s | > 3s |
| Predictions generation | < 5s | < 10s | > 15s |
| Alert evaluation | < 1s | < 2s | > 5s |
| API response (cached) | < 200ms | < 500ms | > 1s |

### 8.2 System Targets

| Metric | Target |
|--------|--------|
| **System Uptime** | 99.5% (monthly) |
| **Data Latency** | < 5 seconds for BTC price |
| **Event Processing** | < 100ms |
| **Model Retraining** | < 1 hour |

---

## 9. Security Rules

### 9.1 Authentication

| Rule | Description |
|------|-------------|
| **Password Requirements** | Minimum 8 characters, 1 uppercase, 1 number, 1 special character |
| **Token Expiry** | Access token: 15 minutes, Refresh token: 7 days |
| **Rate Limiting** | 5 failed login attempts = 15 minute lockout |

### 9.2 Data Protection

| Rule | Description |
|------|-------------|
| **Data Encryption** | TLS for all communications, AES-256 for stored data |
| **Data Retention** | User data retained only as long as account is active |
| **Data Deletion** | GDPR-compliant deletion within 30 days of request |

### 9.3 API Security

| Rule | Description |
|------|-------------|
| **HTTPS** | Required for all API requests |
| **Rate Limiting** | Configurable per endpoint |
| **CORS** | Configured for allowed origins only |

---

## 10. Version History

| Version | Date | Author | Changes | Sub-Issue |
|---------|------|--------|---------|-----------|
| 1.0 | 2026-08-07 | Sid | Initial version with alert threshold rules | 1.1 |
| 1.1 | 2026-08-07 | Sid | Added trading recommendation logic | 1.2 |
| 1.2 | 2026-08-07 | Sid | Added correlation strength rules | 1.3 |
| 1.3 | 2026-08-07 | Sid | Added regime classification rules | 1.4 |
| 1.4 | 2026-08-07 | Sid | Added data quality rules | 1.5 |
| 1.5 | 2026-08-07 | Sid | Added user permission, alert lifecycle, performance, and security rules | 1.6 |