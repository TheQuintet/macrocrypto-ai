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
| **Take-Profit 1** | Conservative target (upper bound, e.g., +3% from entry) |
| **Take-Profit 2** | Moderate target (upper bound, e.g., +5% from entry) |
| **Take-Profit 3** | Aggressive target (upper bound, e.g., +8% from entry) |

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

| Strength | Range | Color | Meaning |
|----------|-------|-------|---------|
| **Strong** | > 0.7 | 🟢 Green | Strong relationship |
| **Medium** | 0.3 - 0.7 | 🟡 Yellow | Moderate relationship |
| **Weak** | < 0.3 | 🔴 Red | Weak relationship |

### 3.1 Correlation Direction

| Direction | Value | Arrow | Meaning |
|-----------|-------|-------|---------|
| **Positive** | > 0 | ↑ | BTC moves in same direction as indicator |
| **Negative** | < 0 | ↓ | BTC moves in opposite direction to indicator |

### 3.2 Statistical Significance

| Rule | Description |
|------|-------------|
| **Significant** | p-value < 0.05 |
| **Not Significant** | p-value >= 0.05 |

---

## 4. Regime Classification Rules

| Regime | Classification Criteria |
|--------|-------------------------|
| **High Inflation** | CPI > 3% |
| **Low Inflation** | CPI < 2% |
| **Rising Rates** | Interest rates increasing over 3 months |
| **Falling Rates** | Interest rates decreasing over 3 months |
| **Recession** | GDP negative growth for 2 consecutive quarters |
| **Growth** | GDP positive growth > 2% |

### 4.1 Regime Performance Metrics

| Metric | Description |
|--------|-------------|
| **Average Return** | Mean BTC return during regime |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Volatility** | Standard deviation of returns |
| **Sharpe Ratio** | Risk-adjusted return |

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

### 5.2 Macro Indicator Data

| Rule | Description |
|------|-------------|
| **Data Freshness** | Updated within 24 hours |
| **Missing Values** | Interpolate or remove |
| **Source** | FRED API |

---

## 6. User Permission Rules

| User Type | Permissions |
|-----------|-------------|
| **Guest** | View public data only |
| **Registered User** | View all data, create alerts, export data |
| **Admin** | All permissions + user management |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |