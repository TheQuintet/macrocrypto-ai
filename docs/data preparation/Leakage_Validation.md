# Leakage & Point-in-Time Validation Policy & Report — Stage 5

**Status:** Finalized & Operational  
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_features.csv` (3,321 rows × 60 columns)  
**Output Artifact:** Automated Pytest Leakage Validation Suite (`tests/ml_qa/test_leakage_validation.py`)  

---

## 1. Purpose & Scope

This document defines the definitive leakage and point-in-time validation framework applied to the 60-column SSOT Feature Store produced in Stage 4 for the **MacroCrypto AI** pipeline. 

Preventing information leakage is the most critical safeguard in quantitative machine learning. Without rigorous point-in-time alignment, models can inadvertently "peek" into the future, yielding inflated backtest metrics that catastrophically fail in live deployment. To maintain absolute scientific integrity, our leakage prevention policy enforces that:
1. **No future information pollutes the past.** Every observation row represents a frozen, immutable snapshot of what was known at timestamp $T$.
2. **Macro publication lags are strictly respected.** Official macroeconomic releases (CPI, GDP, unemployment, etc.) are joined based strictly on their official release dates, tracking exact publication lag counters ($\ge 0$) bounded by realistic upper limits.
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
| 2 | **Zero-Lag Tolerance for Leakage.** | Any feature that references future indices (`shift(-k)` where $k > 0$) is strictly prohibited and verified via shift directionality tests. |
| 3 | **Staleness Tracking & Resets.** | Release-lag and staleness counters (`_days_since_release`, `_days_since_last_observation`) must remain non-negative ($\ge 0$), respect upper bounds, and programmatically reset to `0` on rows where fresh observations arrive. |
| 4 | **Automated Pytest Gatekeeping.** | Leakage checks are fully automated via `tests/ml_qa/test_leakage_validation.py`, blocking promotion to Stage 6 if any anomaly is detected. |

---

## 3. Validation Vectors & Audit Framework

Our automated test suite (`tests/ml_qa/test_leakage_validation.py`) enforces strict mathematical and temporal invariants across the following vectors:

### A. Temporal Boundary & Dimension Audits (`test_feature_store_dimensions`, `test_temporal_monotonicity`, `test_no_future_timestamps`)
* **Exact Dimensions:** Asserts the feature store maintains the exact contract size (3,321 rows × 60 columns).
* **Chronological Sorting:** Asserts that `observation_date` is strictly monotonic increasing (`is_monotonic_increasing == True`).
* **Future Date Verification:** Asserts that no row contains an `observation_date` exceeding current UTC execution time ($\le \text{UTC Now}$).

### B. Macroeconomic Release Lag & Staleness Audits (`test_macro_publication_lags_non_negative_and_bounded`, `test_staleness_counter_semantics`)
* **Non-Negative Lags:** Asserts that all macro series companion columns (`cpi_days_since_release`, etc.) are strictly $\ge 0$.
* **Lag Upper Bounds:** Enforces strict upper limits (e.g., CPI $\le 90$ days, GDP $\le 150$ days, Federal Funds $\le 60$ days) to prevent runaway stale joins.
* **Staleness Resets:** Cross-references source data (`df_cleaned`) to verify that staleness counters correctly reset to `0` on observation rows where underlying series are freshly updated ($\ge 95\%$ compliance threshold).

### C. Shift Directionality & Multi-Index Formula Audit (`test_shift_directionality_and_formulas`)
* **Backward-Looking Computations:** Confirms that log returns and moving averages utilize past indices (`shift(1)`).
* **Multi-Index Mathematical Verification:** Programmatically validates engineered features against exact formulas across multiple randomly sampled, spread-out indices (rows 100, 500, 1200, 2000, 2800):
  * Log return: $\ln(P_t / P_{t-1})$
  * Moving Average (7-day SMA): $\text{mean}(P_{t-6 : t})$
  * Annualized Volatility (7-day): $\text{std}(r, \text{ddof}=1) \times \sqrt{365}$

### D. Warmup Governance & Invariance Audits (`test_warmup_governance_flag`, `test_warmup_nan_pattern`, `test_future_data_does_not_change_past_features`)
* **Binary Flag Integrity:** Validates that the `warmup_complete` governance flag exists and is strictly binary (`0` or `1`).
* **Exact NaN Boundary Assertions:** Confirms that initial rolling window warmup periods align with `min_periods` specifications (e.g., first 89 rows of `btc_sma_90` are strictly `NaN`, and row 89 onward is fully valid).
* **Future-Append Invariance:** Proves mathematically that truncating or appending future data leaves historical feature values completely drift-free (zero look-ahead leakage).

---

## 4. Deliverables & Execution Summary

| Artifact Name | File Path | Description |
| :--- | :--- | :--- |
| **Leakage Policy Report** | `macrocrypto-ai/docs/data preparation/Leakage_Validation.md` | Formal documentation of point-in-time constraints and audit vectors. |
| **Leakage Validation Test Suite** | `tests/ml_qa/test_leakage_validation.py` | Automated Pytest suite enforcing strict temporal, macro lag, formula, and invariant checks. |

---

## 5. Next Steps
With Stage 5 leakage validation fully implemented, tested, and passing all 9 automated assertions, we are ready to proceed to **Stage 6 (Train / Validation / Test Splitting and Walk-Forward Boundaries)**.