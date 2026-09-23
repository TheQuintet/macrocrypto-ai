# Feature Engineering Policy & Execution Report — Stage 4

**Status:** Finalized & Operational  
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_cleaned.csv` (3,321 rows × 49 columns)  
**Output Artifact:** `app/data/ml_btc_daily_features.csv` (3,321 rows × 60 columns, inclusive of technical indicators, momentum returns, annualized rolling volatilities, cross-asset ratios, and warmup governance flags)  

---

## 1. Purpose & Scope

This document defines the definitive feature engineering policies, transformations, and consumption frameworks applied to the cleaned daily Bitcoin dataset produced in Stage 3 (Data Cleaning) for the **MacroCrypto AI** pipeline. 

Feature engineering marks the stage where raw values and cleaned metrics are mathematically transformed into predictive signals. To maintain rigorous scientific and engineering integrity, every transformation is:
1. **Explicit** — stated in clear, unambiguous mathematical terms.
2. **Deterministic** — identical inputs consistently yield identical feature outputs.
3. **Traceable** — backed by domain standards, market periodicity, and crypto trading behaviors.
4. **Testable** — verified via automated pipeline assertions and the `tests/ml_qa/test_engineered_features_quality.py` test suite.

**Out of Scope for This Stage:**
* Raw data ingestion and aggregation (Stage 2)
* Imputation, structural gap governance, and cleaning policies (Stage 3)
* Train/test splitting, cross-validation boundaries, and model training (Stages 5–6)

---

## 2. Core Guiding Principles

| # | Principle | Operational Implication |
| :--- | :--- | :--- |
| 1 | **Single Source of Truth (SSOT).** | Generate one comprehensive feature store artifact; avoid fragmenting datasets into model-specific files to eliminate data drift. |
| 2 | **Preserve temporal sorting.** | All time-series transformations must be computed on strictly chronological data (`observation_date`) to prevent look-ahead bias. |
| 3 | **Match windows to market cycles.** | Feature horizons must reflect real-world behaviors (e.g., 7-day windows for 24/7 crypto trading weeks, 30-day windows for monthly macro alignment). |
| 4 | **Enable dynamic model selection.** | Model-specific feature selection (lean subsets for Prophet vs. full feature sets for tree boosters) occurs dynamically at training time. |
| 5 | **Retain raw lineage.** | All 49 original cleaned columns, staleness counters, and governance flags are safely carried over into the 60-column output store. |

---

## 3. Implemented Transformations & Feature Catalog

Features are computed using deterministic rolling and lagged mathematical operations over the cleaned dataset.

### 3.1 Feature Transformation Matrix

| Feature Category | Target Columns | Transformation / Formula | Operational Rationale |
| :--- | :--- | :--- | :--- |
| **Multi-Horizon Log Returns** | `btc_price` | $\ln(P_t / P_{t-k})$ for $k \in \{1, 7, 30\}$ | Captures immediate tactical shocks ($1d$), 7-day crypto weekly cycle effects ($7d$), and monthly trend velocity ($30d$). |
| **Moving Average Trends** | `btc_price` | Rolling Mean ($\text{window} \in \{7, 30, 90\}$, `min_periods=N`) | Smooths out high-frequency noise to establish baseline short, medium, and long-term moving trend paths. |
| **Annualized Rolling Volatility** | `btc_log_return_1d` | $\text{Std}(\text{ddof}=1) \times \sqrt{365}$ ($\text{window} \in \{7d, 30d\}$) | Quantifies changing market risk profiles and immediate volatility regime shifts tailored for 24/7 crypto markets. |
| **Cross-Asset Ratios** | `btc_price`, `gold_spot`, `nasdaq_composite` | $\text{Ratio} = P_{\text{btc}} / P_{\text{asset}}$ | Measures relative purchasing power, safe-haven dynamics, and intermarket correlation shifts. |
| **Macro Pass-Through** | All 14 Core Macro & Market columns | Unmodified raw values + staleness counters | Preserves slow-moving macro velocity without inducing zero-variance daily noise via forced short-term rolling windows. |

### 3.2 Schema Layout & Metadata Architecture (60 Columns Total)
The output Feature Store artifact (`ml_btc_daily_features.csv`) preserves complete lineage across 60 distinct columns:

* **Original Cleaned Schema (49 columns):** Retains all primary identifiers, raw timestamps, core financial/macro levels, staleness counters (`_days_since_release`, `_days_since_last_observation`), and imputation/governance flags from Stage 3.
* **Engineered Technical Indicators, Ratios & Flags (11 columns):** 
  * *Log Returns:* `btc_log_return_1d`, `btc_log_return_7d`, `btc_log_return_30d`
  * *Moving Averages:* `btc_sma_7`, `btc_sma_30`, `btc_sma_90`
  * *Volatility Metrics:* `btc_volatility_7d`, `btc_volatility_30d`
  * *Cross-Asset Ratios:* `btc_gold_ratio`, `btc_nasdaq_ratio`
  * *Governance Flag:* `warmup_complete`

---

## 4. NaN Warmup Governance & Handling

Because rolling calculations apply strict window requirements (`min_periods=N`), initial observations generate natural warm-up gaps:
* **Warmup Window:** Rows 1 through 89 contain `NaN` values in high-window features (e.g., `btc_sma_90`, `btc_volatility_30d`) due to insufficient prior history.
* **Governance Flag (`warmup_complete`):** A binary companion column is generated (`1` when 90-day moving averages are fully available, `0` during initial warmup rows) to allow downstream training scripts to filter out incomplete windows effortlessly.
* **Model-Specific Handling:** Tree-based boosters (XGBoost, LightGBM) natively handle missing values during splits, whereas linear models or Prophet training scripts should explicitly truncate rows where `warmup_complete == 0`.

---

## 5. Model-Specific Feature Consumption Strategy

Different model families possess distinct mathematical constraints regarding feature dimensionality and collinearity. The SSOT feature store accommodates these via dynamic selection at training time:

### A. Tree-Based Boosters (XGBoost & LightGBM)
* **Dataset Consumption:** Full Feature Store (All 60 columns).
* **Rationale:** Gradient boosters thrive on high-dimensional feature spaces, automatically discovering non-linear interaction terms across technical indicators, rolling volatilities, moving averages, and macro staleness trackers.

### B. Additive Time Series (Prophet)
* **Dataset Consumption:** Lean subset (`ds`, `y`, plus core macro regressors like `dxy`, `m2_money_supply`, `nasdaq_composite`).
* **Rationale:** Prophet treats external regressors as additive linear components. Excluding high-frequency noise (such as 1-day log returns and short-term rolling volatilities) prevents multicollinearity and overfitting, allowing Prophet to focus cleanly on structural macro trends.

---

## 6. Post-Engineering Integrity Assertions & Test Suite

The feature engineering script (`app/scripts/engineer_features.py`) and pytest suite (`tests/ml_qa/test_engineered_features_quality.py`) enforce strict validation rules:
1. **Chronological Integrity:** Asserts that input data is strictly sorted by `observation_date` ($\text{monotonic increasing}$) prior to rolling window calculations.
2. **Zero Row-Loss:** Verifies that row count remains identically aligned at 3,321 daily observations.
3. **Dimensional Expansion:** Confirms successful column growth from 49 input features to 60 output features.
4. **Encoding & Format Compliance:** Ensures outputs are cleanly serialized to CSV in UTF-8 encoding without Byte Order Marks (BOM).
5. **Domain Boundaries:** Validates that daily log returns remain within realistic bounds, SMAs/ratios are strictly positive, and volatilities are non-negative.

---

## 7. Deliverables & Execution Summary

| Artifact Name | File Path | Description |
| :--- | :--- | :--- |
| **Feature Engineering Report** | `macrocrypto-ai/docs/feature_engineering.md` | Comprehensive documentation of transformation policies and 60-column layout. |
| **Feature Engineering Script** | `app/scripts/engineer_features.py` | Deterministic pipeline executing returns, annualized volatility, SMAs, ratios, and assertions. |
| **Final Feature Store** | `app/data/ml_btc_daily_features.csv` | Final unified output artifact (3,321 rows × 60 columns) ready for leakage validation. |
| **QA Test Suite** | `tests/ml_qa/test_engineered_features_quality.py` | Automated test suite enforcing strict numerical, chronological, and structural integrity. |