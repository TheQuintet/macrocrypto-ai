# Data Cleaning Policy & Execution Report — Stage 3

**Status:** Initial Draft for Team Review  
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_raw.csv` (3,321 rows × 32 columns)  
**Output Artifact:** `app/data/ml_btc_daily_cleaned.csv`  

---

## 1. Purpose & Scope

This document defines the definitive cleaning policies and execution framework applied to the aggregated ML dataset produced in Stage 2 (Data Aggregation) and validated in the QA stage for the **MacroCrypto AI** pipeline. 

Cleaning marks the critical transition where values are modified in the pipeline. Everything before this stage preserved raw source integrity; everything after will perform feature engineering, target construction, and scaling. To maintain rigorous traceability, every policy is:
1. **Explicit** — stated in clear, unambiguous language.
2. **Deterministic** — identical inputs consistently yield identical outputs.
3. **Traceable** — backed by source limitations, domain standards, or literature.
4. **Testable** — verified via automated assertions in `tests/ml_qa/test_cleaned_data_quality.py`.

**Out of Scope for This Stage:**
* Feature engineering and transformations
* Target variable construction
* Scaling, normalization, and standardization
* Train/test splitting and model training

---

## 2. Core Guiding Principles

| # | Principle | Operational Implication |
| :--- | :--- | :--- |
| 1 | **Match treatment to cadence.** | Heterogeneous series (daily, monthly, sparse) require tailored handling. |
| 2 | **Preserve observability.** | Imputed or carried values must be explicitly distinguishable from real observations. |
| 3 | **Never paper over structural gaps.** | Multi-year gaps represent fundamental regime changes, not missing data to be blindly smoothed. |
| 4 | **Avoid look-ahead bias.** | Features must strictly reflect information knowable at each specific `observation_date`. |
| 5 | **Prefer additive flags.** | Additive `_is_missing` and staleness columns preserve baseline data that destructive transforms erase. |

---

## 3. Missing-Value Treatment — Per-Cadence Policies

Features are processed according to their source release cadence to prevent data corruption.

### 3.1 Cadence Policy Matrix

| Cadence | Target Features | Treatment Strategy | Operational Rationale |
| :--- | :--- | :--- | :--- |
| **Continuous Daily** | `btc_price`, `btc_volume` | Assert completeness (Zero missing expected). | Gaps indicate underlying ingestion bugs rather than fill opportunities. |
| **Business-Day Markets** | `btc_dominance`, `gold_spot`, `dxy`, `ten_year_treasury`, `vix`, `nasdaq_composite`, `equity_corr`, `high_yield_credit_stress_proxy` | Forward-fill to calendar days; add staleness counters. | Traditional markets close on weekends and holidays; the last known close provides the valid state for a daily ML row. |
| **Structural Gap Series** | `high_yield_spread` | Left untouched as NaN; add `high_yield_spread_is_missing` flag. | Multi-year structural gap (913 days); forward-filling would fabricate false economic stability across major credit shifts. |
| **Sparse On-Chain** | `active_addresses` | Forward-fill up to 5 days; mask (NaN) beyond 5 days. | Source is inherently irregular; fill within tolerance, mask extended gaps. |
| **Monthly / Quarterly Macro** | `cpi`, `federal_funds_rate`, `m2_money_supply`, `unemployment`, `gdp` | As-of join on official release dates; add release lag counters. | Prevents look-ahead bias by respecting publication lags. |

### 3.2 Staleness Indicators & Imputation Flags
For forward-filled and imputed features, companion columns are generated to provide explicit data-freshness metrics for downstream tree-based models (XGBoost, LightGBM):
* **`{feature}_days_since_last_observation`**: Counts integer calendar days since the last fresh market observation (`0` for fresh updates, incrementing upwards during holidays/weekends).
* **`{feature}_is_imputed`**: Binary flag (`0`/`1`) marking interpolated or carried values.

---

## 4. Historical-Gap Treatment & NaN Governance

Certain segments contain structural gaps requiring specialized handling rather than automated filling.

### 4.1 The 913-Day Structural Gap (`high_yield_spread`)
* **Context:** The ICE BofA US High Yield Index OAS (`BAMLH0A0HYM2`) contains a **913-day structural coverage gap** spanning from **March 20, 2021, to September 18, 2023**, bridging the archived historical feed and the live FRED API. This interval covers the 2022 rate-hike cycle and the March 2023 regional banking stress.
* **Governance & NaN Application:** 
  * Per team policy, **forward-filling this 913-day gap is strictly prohibited**, as it would fabricate flat credit spreads across critical macroeconomic shifts.
  * The canonical `high_yield_spread` is left entirely as **`NaN`** throughout this multi-year interval.
  * Companion column **`high_yield_spread_is_missing`** is set to `1` during the gap (and `0` elsewhere) to inform models of the coverage absence natively.

### 4.2 Other Structural & Handoff Gaps
* **`active_addresses` (Sparse Gaps):** Irregular gaps (such as a 7-day gap in August 2026) are forward-filled up to a maximum limit of 5 days and masked as `NaN` beyond that threshold.
* **Handoff Gaps (`gold_spot`, `btc_dominance`):** Source transition gaps (5–6 days during API/archive migrations) are forward-filled under controlled tolerance, backed by staleness indicators.

---

## 5. Macroeconomic Vintage & Point-in-Time Alignment Status

* **Status:** Raw vintage release dataset successfully acquired and stored.
* **Dataset Location:** `app/data/macro_raw_with_vintages.csv`
* **Details:** Official publication and revision dates (`realtime_start`) are tracked for all macroeconomic features (`cpi`, `unemployment`, `federal_funds_rate`, `m2_money_supply`, `gdp`). Redundant no-op re-releases have been filtered out to optimize storage and clarity.
* **Next Steps:** The release-date `pd.merge_asof` point-in-time join logic will be fully integrated. 
---

## 6. Standalone Proxy Integration (`high_yield_credit_stress_proxy`)

To retain credit-stress signals during the 913-day BAML gap without corrupting the canonical series:
* **Standalone Structure:** Loaded via `Date, high_yield_credit_stress_proxy` structure and merged via left join.
* **Cadence Treatment:** Treated as a business-day market asset, applying standard calendar-day forward-filling and staleness tracking (`high_yield_credit_stress_proxy_days_since_last_observation`).
* **Governance Rule:** Kept strictly distinct on its native return scale. Automated integrity assertions confirm that proxy values never directly overwrite or equal canonical `high_yield_spread` values.

---

## 7. Post-Cleaning Integrity Assertions

The cleaning script (`app/scripts/clean_ml_data.py`) and associated pytest suite (`tests/ml_qa/test_cleaned_data_quality.py`) enforce strict validation rules:
1. **Uniqueness:** No duplicate `observation_date` entries exist.
2. **Temporal Bounds:** `MAX(observation_date) <= current_date`.
3. **Structural Preservation:** The 913-day `high_yield_spread` gap is verified as `NaN` paired with correct missing flags.
4. **Proxy Distinctness:** Asserts zero direct equality matches between `high_yield_spread` and `high_yield_credit_stress_proxy`.
5. **Schema Stability:** Column names, encodings (UTF-8 without BOM), and value ranges (`vix >= 0`, `dxy > 0`) remain consistent.

---

## 8. Deliverables & Execution Summary

| Artifact Name | File Path | Description |
| :--- | :--- | :--- |
| **Cleaning Policy & Report** | `app/docs/data_cleaning_report.md` | Comprehensive documentation of all governance rules. |
| **Cleaning Script** | `app/scripts/clean_ml_data.py` | Deterministic pipeline executing cadence rules and proxy integration. |
| **Cleaned Dataset** | `app/data/ml_btc_daily_cleaned.csv` | Output artifact ready for feature engineering. |
| **QA Test Suite** | `tests/ml_qa/test_cleaned_data_quality.py` | Automated test suite enforcing structural assertions. |