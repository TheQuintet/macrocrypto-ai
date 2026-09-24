# Train / Validation / Test Splitting, Target Alignment & Walk-Forward Policy — Stage 6

**Status:** Finalized & Operational  
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_features.csv` (Raw: 3,321 rows $\to$ Filtered Clean Baseline: 3,230 rows × 60 columns)  
**Output Artifacts:** 
* `app/ml/splitting_config.py` (Pydantic Split Parameter Validation)
* `app/ml/walk_forward.py` (Pure NumPy/Pandas Walk-Forward & Purge Splitter)
* `app/ml/target_generator.py` (Next-Day Target Alignment $y_t = \text{Price}_{t+1}$)
* `app/ml/split_processor.py` (Stage 6 Pipeline Orchestrator & Governance Manager)
* `tests/ml_qa/test_split_processor.py` (Automated Verification Suite)

---

## 1. Executive Summary

This document establishes the official chronological partitioning, walk-forward cross-validation, and target variable alignment framework for the **MacroCrypto AI** machine learning pipeline. Managed centrally via `SplitProcessor`, all data governance filters, splits, buffer accounting, and feature-target relationships adhere to strict temporal boundaries to ensure absolute scientific integrity and eliminate look-ahead bias.

---

## 2. Target Variable Definition & Feature-Target Alignment

Supervised learning models within the pipeline are structured around a precise 1-day ahead forecasting objective:

* **Target Variable ($y_t$):** Next-day Bitcoin closing/observed price ($\text{Price}_{t+1}$). For each trading day $t$, the model forecasts the exact price observed on day $t+1$.
* **Predictor Feature Availability ($X_t$):** All predictor features (including technical indicators and rolling statistics such as `btc_sma_90`) are computed strictly using information available **on or before day $t$**.
* **Trailing NaN Policy:** The absolute final row in the dataset ($t = N$) lacks an observed $t+1$ price because future data is unobserved. This row is isolated via `TargetGenerator` as the live, unlabeled inference frontier.

---

## 3. Data Governance & Row Filtering Strategy

Before splitting, Stage 6 applies explicit data governance rules via `SplitProcessor` to transition the raw feature store into a pristine modeling baseline:
* **Warmup Drop:** Excludes 89 records where `warmup_complete == 0` to purge rolling indicator initialization artifacts (reducing rows from 3,321 to 3,232).
* **Missing Value Cleanup:** Drops 2 records missing critical `active_addresses` metrics, establishing the final clean baseline of exactly **3,230 rows**.
* **Feature Imputation:** Minor downstream gaps (such as `unemployment`) are forward-filled strictly on NaN values to maintain zero missing values across numerical features prior to scaling and partitioning.

---

## 4. Partition Sizing & Buffer Accounting

Nominal split ratios are established at **80% Training / 10% Validation / 10% Holdout Test** across the supervised timeline ($N = 3,229$ rows after isolating the live frontier). Purge and embargo buffers carve out dedicated separation zones from chronological allocations to prevent look-ahead leakage from rolling window features:

* **Training Partition:** **2,583 rows**
* **Validation Partition:** **322 rows**
* **Holdout Test Partition:** **227 rows**
* **Total Supervised Split Rows:** **3,132 rows**
* **Purge/Embargo Buffer Dropped:** **97 boundary rows** (neutralizing rolling feature overlap like `btc_sma_90` and target boundary leakage between partitions).

---

## 5. Architectural Specifications & Policies

| Policy Domain | Implementation Details & Technical Rationale |
| :--- | :--- |
| **Purge & Horizon Sizing** | Default `purge_window` is configured to **90 days**, comfortably exceeding the 1-day target horizon and fully covering maximum rolling indicators like `btc_sma_90`. |
| **Walk-Forward Design** | Utilizes an expanding training window combined with rolling validation slices, tracking absolute chronological bounds prior to the holdout test set. |
| **Date Density & Continuity** | Enforces a strict daily calendar grid with zero date gaps ($\Delta = 1$ day) using `observation_date` on the raw sequence prior to row filtering. |
| **Target Enforcement** | Programmatically orchestrated via `SplitProcessor` and verified by automated test suites. |

---

## 6. Automated Verification Suite

The verification suite (`tests/ml_qa/test_split_processor.py`) enforces strict automated invariants:
1. **Row Count Governance:** Asserts exact record transitions (3,321 raw $\to$ 3,232 post-warmup $\to$ 3,230 final clean baseline).
2. **Supervised Split Validation:** Validates exact partition sums (Train: 2,583, Val: 322, Test: 227 = 3,132 total supervised rows).
3. **Live Frontier Isolation:** Verifies that exactly 1 row is isolated as the live inference frontier.
4. **Zero Missingness:** Confirms zero NaN values across unemployment and feature partitions after targeted imputation rules.

---

## 7. Next Steps

With Stage 6 fully validated and operational, the pipeline proceeds to **Stage 7 (Feature Scaling and Transformation)**.