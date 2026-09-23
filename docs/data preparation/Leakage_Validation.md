# Leakage & Point-in-Time Validation Policy & Report — Stage 5

**Status:** Review 
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_features.csv` (3,321 rows × 60 columns)  
**Output Artifact:** Automated Pytest Leakage Validation Suite (`tests/ml_qa/test_leakage_validation.py`)  

---

## 1. Purpose & Scope

This document defines the definitive leakage and point-in-time validation framework applied to the 60-column SSOT Feature Store produced in Stage 4 for the **MacroCrypto AI** pipeline. 

Preventing information leakage is the most critical safeguard in quantitative machine learning. Without rigorous point-in-time alignment, models can inadvertently "peek" into the future, yielding inflated backtest metrics that catastrophically fail in live deployment. To maintain absolute scientific integrity, our leakage prevention policy enforces that:
1. **No future information pollutes the past.** Every observation row represents a frozen, immutable snapshot of what was known at timestamp $T$.
2. **Macro publication lags are strictly respected.** Official macroeconomic releases (CPI, GDP, unemployment, etc.) are joined based strictly on their official release dates, tracking exact publication lag counters ($\ge 0$).
3. **Temporal ordering is immutable.** Chronological sorting and UTC timestamp normalization are enforced across all transformation boundaries.

**Out of Scope for This Stage:**
* Raw data cleaning and imputation (Stage 3)
* Feature transformation, rolling standard deviations, and ratio creation (Stage 4)
* Train/validation/test splitting strategies and model weight optimization (Stage 6)

---

## 2. Core Guiding Principles

| # | Principle | Operational Implication |
| :--- | :--- | :--- |
| 1 | **Strict As-Of Alignment.** | Macroeconomic series must use official release dates, never observation dates, preventing look-ahead bias. |
| 2 | **Zero-Lag Tolerance for Leakage.** | Any feature that references future indices (`shift(-k)` where $k > 0$) is strictly prohibited. |
| 3 | **Staleness Tracking as a Shield.** | Staleness and release-lag counters (`_days_since_release`, `_days_since_last_observation`) must remain non-negative at all times ($\ge 0$). |
| 4 | **Automated Pytest Gatekeeping.** | Leakage checks are fully automated via `tests/ml_qa/test_leakage_validation.py`, blocking promotion to Stage 6 if any anomaly is detected. |

---

## 3. Validation Vectors & Audit Framework

Our automated test suite audits four primary vectors of potential information leakage:

### A. Temporal Boundary Audits
* **Chronological Sorting:** Asserts via `test_temporal_monotonicity` that `observation_date` is strictly monotonic increasing (`is_monotonic_increasing == True`).
* **Future Date Verification:** Asserts via `test_no_future_timestamps` that no row contains an `observation_date` exceeding current execution time ($\le \text{UTC Now}$).

### B. Macroeconomic Release Lag Audits
* **Publication Lags:** Asserts via `test_macro_publication_lags_non_negative` that all macro series companion columns (`cpi_days_since_release`, `federal_funds_rate_days_since_release`, etc.) are strictly $\ge 0$. A negative value would indicate that a model is consuming a macro print before public release.

### C. Shift & Rolling Window Directionality Audit
* **Backward-Looking Computations:** Verifies that all log returns and moving averages are computed strictly backward using past and present values (`shift(1)`, rolling windows with `min_periods=N`), avoiding any forward-looking data leakage.

### D. Warmup Governance & Feature Independence
* **Warmup Flag Verification:** Asserts via `test_warmup_governance_flag` that the `warmup_complete` column exists and is strictly binary (`0` or `1`), ensuring downstream models can cleanly isolate fully warmed-up records.

---

## 4. Deliverables & Execution Summary

| Artifact Name | File Path | Description |
| :--- | :--- | :--- |
| **Leakage Policy Report** | `macrocrypto-ai/docs/data preparation/leakage_validation.md` | Formal documentation of point-in-time constraints and audit vectors. |
| **Leakage Validation Test Suite** | `tests/ml_qa/test_leakage_validation.py` | Automated Pytest suite enforcing strict temporal, macro lag, and non-leakage invariants. |

---

## 5. Next Steps
With Stage 5 leakage validation formalized and covered by our test suite, we are ready to proceed to **Stage 6 (Train / Validation / Test Splitting and Walk-Forward Boundaries)**.