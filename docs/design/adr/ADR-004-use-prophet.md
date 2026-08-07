# ADR-004: Use Prophet for Time-Series Forecasting

## Status

**Accepted**

---

## Context

We need a time-series forecasting model to generate BTC price predictions. We considered multiple options: Prophet, LSTM, XGBoost, ARIMA, and simple moving averages.

---

## Decision

**Use Prophet** (Meta's open-source forecasting library).

---

## Rationale

| Reason | Explanation |
|--------|-------------|
| **Easy to Use** | Simple API, minimal hyperparameter tuning |
| **Seasonality** | Built-in daily, weekly, yearly seasonality |
| **Uncertainty** | Automatic confidence intervals |
| **Handles Missing Data** | Robust to missing values |
| **Interpretable** | Trend, seasonality, and holidays are separate components |

---

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **LSTM/RNN** | Requires large data, complex training, black box |
| **XGBoost** | No native time-series support, no uncertainty |
| **ARIMA** | Manual tuning, no seasonality detection |
| **Moving Averages** | Too simplistic, no confidence intervals |

---

## Consequences

### Positive

- ✅ Fast to train (< 5s)
- ✅ Automatic confidence intervals
- ✅ Good for financial time-series
- ✅ Easy to explain to users

### Negative

- ❌ Less accurate than deep learning (for complex patterns)
- ❌ Not good for high-frequency data (< 1 hour)
- ❌ Assumes additive seasonality

---

## Implementation Details

| Component | Technology |
|-----------|------------|
| Library | prophet 1.1.5+ |
| Seasonality | Daily, weekly, yearly |
| Confidence | 70%, 85%, 95% |
| Features | 10 features (5 macro, 5 BTC) |

---

## Related ADRs

- None

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |