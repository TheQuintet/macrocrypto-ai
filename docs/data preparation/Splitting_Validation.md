# Train / Validation / Test Splitting & Walk-Forward Policy & Report — Stage 6

**Status:** Review  
**Date:** September 2026  
**Input Artifact:** `app/data/ml_btc_daily_features.csv` (3,321 rows × 60 columns)  
**Output Artifacts:** 
* `app/ml/splitting_config.py` (Pydantic Split Parameter Validation)
* `app/ml/walk_forward.py` (Pure NumPy/Pandas Walk-Forward & Purge Splitter)
* `tests/ml_qa/test_split_validation.py` (Automated Pytest Suite)

---

## 1. Purpose & Scope

This document defines the definitive chronological partitioning and cross-validation framework applied to the 60-column SSOT Feature Store for the **MacroCrypto AI** pipeline. 

In quantitative time-series forecasting, standard random K-fold cross-validation introduces severe look-ahead bias due to serial correlation. To maintain absolute scientific integrity, our splitting policy enforces:
1. **Strict Chronological Separation:** Data is partitioned strictly along a time axis into an 80% Train set, 10% Validation set, and 10% Holdout Test set.
2. **Purge & Embargo Buffers:** Eliminates target and feature overlap leakage around split boundaries caused by rolling windows and lagging features.
3. **Walk-Forward Expanding Windows:** Simulates real-world deployment via expanding training folds and sequential validation slices.

**Out of Scope for This Stage:**
* Raw data cleaning and imputation (Stage 3)
* Feature engineering and rolling calculations (Stage 4)
* Point-in-time leakage verification (Stage 5)
* Model training, hyperparameter tuning, and final evaluation (Stage 7+)

---

## 2. Core Guiding Principles

| # | Principle | Operational Implication |
| :--- | :--- | :--- |
| 1 | **Chronological Order Preservation.** | Past data trains the model; future data validates and tests it. No shuffling of time-series indices is permitted. |
| 2 | **Pydantic Configuration Integrity.** | Split ratios (80/10/10), purge windows (7 days), and embargo windows (7 days) are centrally governed and validated via `SplitConfig`. |
| 3 | **Purge & Embargo Buffers.** | Training sets are trimmed by the purge window to prevent rolling feature leakage (e.g., 90-day SMAs) from bleeding into validation. |
| 4 | **Automated Pytest Gatekeeping.** | Partition overlap and fold expansion invariants are enforced via `tests/ml_qa/test_split_validation.py`. |

---

## 3. Validation Vectors & Audit Framework

Our automated test suite (`tests/ml_qa/test_split_validation.py`) enforces strict mathematical and temporal invariants across the following vectors:

### A. Partition Boundary & Zero-Overlap Audit (`test_partition_boundaries_no_overlap`)
* **Exact Ratio Mapping:** Asserts that the 80% training cutoff aligns precisely with dataset dimensions ($3,321 \times 0.80 = 2,656$ rows).
* **Chronological Sequence:** Verifies strict ordering: $\text{Train End} \le \text{Validation Start}$ and $\text{Validation End} \le \text{Test Start}$.
* **Zero Index Intersection:** Proves mathematically that index sets for Train, Validation, and Test partitions are mutually exclusive ($\vert{}A \cap B\vert{} = 0$).

### B. Walk-Forward Expanding Folds Audit (`test_walk_forward_generator`)
* **Expanding Training Windows:** Verifies that walk-forward folds dynamically expand while respecting purge buffers at fold boundaries.
* **Non-Empty Slices:** Asserts that every training and validation fold contains valid sample lengths and maintains correct temporal precedence ($\text{Train Index Max} < \text{Val Index Min}$).

---

## 4. Deliverables & Execution Summary

| Artifact Name | File Path | Description |
| :--- | :--- | :--- |
| **Split Configuration** | `app/ml/splitting_config.py` | Pydantic model enforcing 80/10/10 ratios, purge, and embargo settings. |
| **Walk-Forward Splitter** | `app/ml/walk_forward.py` | Native NumPy/Pandas splitting engine with built-in buffer management. |
| **Split Validation Suite** | `tests/ml_qa/test_split_validation.py` | Automated Pytest suite verifying boundary non-overlap and fold integrity. |

---

## 5. Next Steps
With Stage 6 splitting configuration and walk-forward cross-validation fully implemented and tested, we are ready to proceed to **Stage 7 (Feature Scaling and Normalization)**.