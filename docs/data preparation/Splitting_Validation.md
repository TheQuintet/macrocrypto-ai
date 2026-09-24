# Train / Validation / Test Splitting, Target Alignment & Walk-Forward Policy — Stage 6

**Status:** Ready for Review  
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_features.csv` (3,321 rows × 60 columns)  
**Output Artifacts:** 
* `app/ml/splitting_config.py` (Pydantic Split Parameter Validation)
* `app/ml/walk_forward.py` (Pure NumPy/Pandas Walk-Forward & Purge Splitter)
* `tests/ml_qa/test_split_validation.py` (Automated Verification Suite)

---

## 1. Executive Summary

This document establishes the official chronological partitioning, walk-forward cross-validation, and target variable alignment framework for the **MacroCrypto AI** machine learning pipeline. To ensure absolute scientific integrity and eliminate look-ahead bias, all data splits, buffer accounting, and feature-target relationships adhere to strict temporal boundaries.

---

## 2. Target Variable Definition & Feature-Target Alignment

Supervised learning models within the pipeline are structured around a precise 1-day ahead forecasting objective:

* **Target Variable ($y_t$):** Next-day Bitcoin closing/observed price ($\text{Price}_{t+1}$). For each trading day $t$, the model forecasts the exact price observed on day $t+1$.
* **Predictor Feature Availability ($X_t$):** All predictor features (including technical indicators and rolling statistics such as `btc_sma_90`) are computed strictly using information available **on or before day $t$**.
* **Trailing NaN Policy:** The absolute final row in the dataset ($t = N$) lacks an observed $t+1$ price because future data is unobserved. This row is excluded from supervised training and validation splits, serving exclusively as the live, unlabeled inference frontier.

---

## 3. Partition Sizing & Buffer Accounting

Nominal split ratios are established at **80% Training / 10% Validation / 10% Holdout Test**. To prevent information leakage across temporal boundaries, purge and embargo buffers carve out dedicated separation zones from the theoretical allocations across a dataset of $N = 3,321$ rows:

* **Training Region:** Rows $0 \to 2,656$ (80%)
* **Purge Buffer:** 90 rows dropped between training and validation partitions. Because the maximum rolling feature window is 90 days (`btc_sma_90`) and the target horizon is 1 day ($k=1$), the 90-day purge window completely neutralizes both feature overlap and target boundary leakage.
* **Validation Region:** Rows $2,747 \to 3,002$ (~8%)
* **Embargo Buffer:** 7 rows dropped between validation and test partitions.
* **Holdout Test Region:** Rows $3,010 \to 3,321$ (~9% effective).

---

## 4. Architectural Specifications & Policies

| Policy Domain | Implementation Details & Technical Rationale |
| :--- | :--- |
| **Purge & Horizon Sizing** | Default `purge_window` is configured to **90 days**, comfortably exceeding the 1-day target horizon and fully covering maximum rolling indicators like `btc_sma_90`. |
| **Walk-Forward Design** | Utilizes an expanding training window combined with rolling validation slices, tracking absolute chronological bounds prior to the holdout test set. |
| **Date Density & Continuity** | Enforces a strict daily calendar grid with zero date gaps ($\Delta \le 1$ day), verifying that row indices map reliably to calendar intervals. |
| **Warmup Handling** | Rows where `warmup_complete == 0` reside exclusively at the inception of the training set. Tree-based algorithms process these initial indicators natively, while linear estimators require appropriate dropping or imputation. |

---

## 5. Automated Verification Suite

The verification suite (`tests/ml_qa/test_split_validation.py`) enforces strict automated invariants:
1. **Date Continuity:** Asserts zero calendar gaps ($\Delta \le 1$ day) across the feature store.
2. **Disjoint Partition Boundaries:** Verifies zero index intersection between Training, Validation, and Test partitions.
3. **Walk-Forward Invariants:** Confirms strictly expanding training set sizes, rigorous purge buffer enforcement ($\text{val\_index}[0] - \text{train\_index}[-1] \ge 90$), and complete test set isolation ($\text{val\_index}[-1] < \text{test\_start}$).

---

## 6. Next Steps
Following successful validation and review of Stage 6, the pipeline proceeds to **Stage 7 (Feature Scaling and Transformation)**.