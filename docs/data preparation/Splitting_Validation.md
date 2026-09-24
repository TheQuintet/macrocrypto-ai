# Train / Validation / Test Splitting, Target Alignment & Walk-Forward Policy — Stage 6

**Status:** Review  
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_features.csv` (3,321 rows × 60 columns)  
**Output Artifacts:** 
* `app/ml/splitting_config.py` (Pydantic Split Parameter Validation)
* `app/ml/walk_forward.py` (Pure NumPy/Pandas Walk-Forward & Purge Splitter)
* `app/ml/target_generator.py` (Next-Day Target Alignment $y_t = \text{Price}_{t+1}$)
* `tests/ml_qa/test_split_validation.py` (Automated Verification Suite)

---

## 1. Executive Summary

This document establishes the official chronological partitioning, walk-forward cross-validation, and target variable alignment framework for the **MacroCrypto AI** machine learning pipeline. To ensure absolute scientific integrity and eliminate look-ahead bias, all data splits, buffer accounting, and feature-target relationships adhere to strict temporal boundaries.

---

## 2. Target Variable Definition & Feature-Target Alignment

Supervised learning models within the pipeline are structured around a precise 1-day ahead forecasting objective:

* **Target Variable ($y_t$):** Next-day Bitcoin closing/observed price ($\text{Price}_{t+1}$). For each trading day $t$, the model forecasts the exact price observed on day $t+1$.
* **Predictor Feature Availability ($X_t$):** All predictor features (including technical indicators and rolling statistics such as `btc_sma_90`) are computed strictly using information available **on or before day $t$**.
* **Trailing NaN Policy:** The absolute final row in the dataset ($t = N$) lacks an observed $t+1$ price because future data is unobserved. This row is isolated via `TargetGenerator` as the live, unlabeled inference frontier.

---

## 3. Partition Sizing & Buffer Accounting

Nominal split ratios are established at **80% Training / 10% Validation / 10% Holdout Test** across a dataset of $N = 3,321$ rows. Purge and embargo buffers carve out dedicated separation zones from the theoretical allocations:

* **Training Region:** Indices $0 \to 2,656$ (**2,656 rows** / 80%)
* **Purge Buffer:** **90 rows** dropped between training and validation partitions (Indices $2,656 \to 2,746$). This completely neutralizes rolling feature overlap (`btc_sma_90`) and target boundary leakage.
* **Validation Region:** Indices $2,746 \to 3,078$ (**332 rows** / 10%)
* **Embargo Buffer:** **7 rows** dropped between validation and test partitions (Indices $3,078 \to 3,085$).
* **Holdout Test Region:** Indices $3,085 \to 3,321$ (**236 rows** / 7.1% effective).

---

## 4. Architectural Specifications & Policies

| Policy Domain | Implementation Details & Technical Rationale |
| :--- | :--- |
| **Purge & Horizon Sizing** | Default `purge_window` is configured to **90 days**, comfortably exceeding the 1-day target horizon and fully covering maximum rolling indicators like `btc_sma_90`. |
| **Walk-Forward Design** | Utilizes an expanding training window combined with rolling validation slices, tracking absolute chronological bounds prior to the holdout test set. |
| **Date Density & Continuity** | Enforces a strict daily calendar grid with zero date gaps ($\Delta = 1$ day) using `observation_date`, verifying that row indices map reliably to calendar intervals. |
| **Target Enforcement** | Programmatically constructed via `TargetGenerator` (`app/ml/target_generator.py`) and verified by automated test suites. |

---

## 5. Automated Verification Suite

The verification suite (`tests/ml_qa/test_split_validation.py`) enforces strict automated invariants:
1. **Date Continuity:** Asserts zero calendar gaps or duplicates ($\Delta = 1$ day) across `observation_date`.
2. **Exact Partition Sizes:** Asserts exact row allocations (`train=2656`, `val=332`, `test=236`) and buffer widths (`purge=90`, `embargo=7`).
3. **Disjoint Partition Boundaries:** Verifies zero index intersection between Training, Validation, and Test partitions.
4. **Walk-Forward Invariants:** Confirms strictly expanding training set sizes, rigorous purge buffer enforcement ($\ge 90$ days), and complete test set isolation.

---

## 6. Next Steps
Once Stage 6 got approval, the pipeline proceeds to **Stage 7 (Feature Scaling and Normalization)**.