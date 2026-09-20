# Project Milestone Completion Report: Data Quality Assurance and Validation

**Project:** MacroCrypto AI
**Status:** Completed & Ready for Review
**Date:** September 2026

---

## 1. Executive Summary

The **Data Quality Assurance and Validation Stage** has been completed for the MacroCrypto AI data-preparation pipeline.

Validation covered the raw source datasets, aggregated data, schema integrity, UTC observation dates, duplicate observations, chronological ordering, source timestamp consistency, feature completeness, and known historical coverage gaps.

All configured QA test suites passed successfully. The identified historical gaps were confirmed as source-coverage gaps rather than database or aggregation failures.

The historical gap in the canonical `BAMLH0A0HYM2` high-yield spread was also investigated using daily HYG and SHY market data. The HYG/SHY data was analyzed as a separate market-derived signal and was **not used to replace, reconstruct, or rescale the canonical BAML spread**.

---

## 2. Key Validation Highlights

### A. Collector & Source Validation

Each configured collector was executed against its intended upstream source and returned actual source observations successfully.

The validation followed the complete data provenance chain:

```text
Configured collector
        ↓
Actual upstream source
        ↓
Collector response
        ↓
Raw database data
        ↓
Aggregation
        ↓
QA validation
```

The validation confirmed that the aggregated data is based on collected source observations and that no fabricated observations were introduced during aggregation.

### B. Aggregated Dataset Validation

The aggregated ML dataset was validated for:

* Expected schema and feature structure
* UTC `observation_date`
* One observation per UTC day
* Chronological ordering
* No future observation dates
* BTC price and volume completeness
* Numeric feature validity
* Source timestamp consistency
* Feature-level missingness
* Duplicate observation dates

Historical missing values were reported rather than filled during this stage because source availability differs across indicators.

### C. QA Test Results

| Test Suite                        |           Result |
| --------------------------------- | ---------------: |
| BTC prices data quality           |     16/16 passed |
| BTC dominance data quality        |     13/13 passed |
| Macro indicators data quality     |     15/15 passed |
| Aggregated ML raw dataset quality |     20/20 passed |
| **Total**                         | **64/64 passed** |

---

## 3. Gap & Duplication Analysis

The QA process uses frequency-aware gap validation so that expected publication frequencies are considered when checking historical coverage.

### A. Known Historical Gaps

| **Feature**         | **Gap Start** | **Gap End** | **Gap Length** | **Finding**                    |
| ------------------- | ------------- | ----------- | -------------- | ------------------------------ |
| `btc_dominance`     | 2023-07-23    | 2023-07-26  | 4 days         | Upstream source coverage gap   |
| `gold_spot`         | 2021-09-14    | 2021-09-19  | 6 calendar days| Upstream source coverage gap   |
| `active_addresses`  | 2026-08-17    | 2026-08-23  | 7 days         | Upstream source coverage gap   |
| `cpi`               | 2025-09-02    | 2025-10-31  | 60 days        | Upstream source coverage gap   |
| `dxy`               | 2020-11-26    | 2020-11-29  | 4 days         | Upstream source coverage gap   |
| `dxy`               | 2020-12-24    | 2020-12-27  | 4 days         | Upstream source coverage gap   |
| `unemployment`      | 2025-09-02    | 2025-10-31  | 60 days        | Upstream source coverage gap   |
| `high_yield_spread` | 2021-03-20    | 2023-09-18  | 913 days       | Historical source coverage gap |

These gaps were confirmed during validation and are not treated as database collection or aggregation failures.

### B. Duplication Validation

Duplicate observations were checked at both the raw-source and aggregated-data levels.

The validation confirmed:

* Unexpected duplicate dates were checked in the raw observations.
* Aggregation produces one observation per UTC `observation_date`.
* The aggregated ML dataset contains no duplicate observation dates.
* The HYG/SHY daily dataset contains no duplicate dates.

---

## 4. High-Yield Spread Gap Investigation

The canonical high-yield spread feature is:

`high_yield_spread = BAMLH0A0HYM2`

This represents the ICE BofA US High Yield Index Option-Adjusted Spread.

The available historical sources cover:

* Historical archive: `1996-12-31` → `2021-03-19`
* FRED: `2023-09-19` → present
* Confirmed gap: `2021-03-20` → `2023-09-18`

The gap was therefore confirmed as a source-coverage issue rather than a failure in the aggregation process.

### A. HYG/SHY Daily Data Acquisition

Daily HYG and SHY market data was collected separately to investigate whether the available market-price information could provide a useful additional signal around the BAML coverage gap.

The raw dataset is:

`app/scripts/hyg_shy_raw.csv`

It contains:

* 2,284 overlapping daily observations
* Date range: `2017-08-17` → `2026-09-18`
* No missing HYG observations
* No missing SHY observations
* No duplicate dates

The raw dataset contains the daily `HYG` and `SHY` closing prices and is maintained as a separate source artifact.

It is not a replacement dataset for `BAMLH0A0HYM2`.

### B. Daily HYG/SHY Derived Signal

The daily HYG/SHY data was used to calculate the following derived signal:

```text
(HYG / SHY).pct_change()
```

The resulting feature is stored separately as:

`app/scripts/high_yield_credit_stress_proxy.csv`

This represents a **daily market-derived signal** based on the relative movement of HYG and SHY.

It is not the BAML high-yield spread and is not treated as a reconstructed version of `BAMLH0A0HYM2`.

### C. Daily Analysis Performed

The analysis focused on the daily signal and its relationship with daily BTC returns.

The daily HYG/SHY signal was examined for:

* Daily observations and coverage
* Missing values
* Duplicate dates
* Daily percentage changes
* Large daily movements
* Selected historical dates
* Relationship with same-day BTC returns
* Relationship with next-day BTC returns for point-in-time validation

The daily signal showed an observable relationship with same-day BTC movement:

* Correlation with same-day BTC return: approximately **0.216**
* Correlation with same-day absolute BTC return: approximately **0.168**

For the point-in-time check using the following day's BTC return:

* Correlation with next-day BTC return: approximately **-0.050**
* Correlation with next-day absolute BTC return: approximately **0.070**

These results indicate that the daily HYG/SHY signal contains some observable relationship with BTC market movement on the same day, while the next-day relationship observed in this analysis was weak.

The results do **not** establish that the HYG/SHY signal is equivalent to the BAML spread or that it provides proven predictive performance. Formal predictive evaluation belongs to the downstream ML validation stage.

### D. Interpretation for Team Decision

The analysis supports keeping the HYG/SHY signal separate from the canonical BAML feature.

The two datasets represent different measurements:

```text
BAMLH0A0HYM2
    ↓
Canonical high-yield credit spread
    ↓
high_yield_spread


HYG + SHY daily prices
    ↓
(HYG / SHY).pct_change()
    ↓
high_yield_credit_stress_proxy
```

The HYG/SHY signal should therefore **not** be used to fill the historical BAML gap by pretending that it represents the missing BAML observations.

The daily analysis provides enough evidence to preserve the HYG/SHY signal as a **separate candidate feature** for downstream evaluation. Its usefulness should be determined independently through the later feature-engineering and ML-validation stages.

---

## 5. Proxy Dataset Governance

The initial exploratory artifact:

`app/scripts/high_yield_spread_proxy.csv`

used a transformation intended to place the HYG/SHY signal into a BAML-like numerical range.

That approach is not used for the final dataset because numerical rescaling does not establish equivalence with the BAML spread.

The validated representation is therefore:

```text
BAMLH0A0HYM2
        ↓
canonical high_yield_spread


HYG / SHY daily market data
        ↓
daily percentage change
        ↓
high_yield_credit_stress_proxy
```

The HYG/SHY feature remains independently named, independently sourced, and independently evaluated.

No BAML observations were fabricated or reconstructed from HYG/SHY.

---

## 6. Validation Results

The completed validation stage confirms that:

* Configured collectors returned actual source observations.
* Raw source data passed the applicable quality checks.
* Aggregated data has the expected structure.
* UTC observation dates are used for daily aggregation.
* The aggregated dataset contains one observation per UTC day.
* Unexpected duplicate dates were checked.
* Known historical source gaps were identified and documented.
* No imputation, interpolation, or forward-filling was performed during aggregation.
* The canonical BAML high-yield spread was not replaced by the HYG/SHY signal.
* HYG/SHY daily data was separately collected and validated.
* The daily HYG/SHY-derived signal was analyzed against daily BTC returns.
* The HYG/SHY signal remains a separate candidate feature for downstream evaluation.

---

## 7. Canonical Dataset Status

The canonical aggregated dataset:

`app/data/ml_btc_daily_raw.csv`

has completed the Data Quality Assurance and Validation Stage.

The dataset remains a raw/aggregated ML-preparation artifact.

At this stage:

* No imputation has been applied.
* No interpolation has been applied.
* No forward-fill has been applied.
* No target engineering has been applied.
* No scaling has been applied.
* No HYG/SHY proxy has been substituted for `high_yield_spread`.
* No predictive feature selection has been performed.

The HYG/SHY candidate remains outside the canonical aggregated dataset pending downstream evaluation and implementation decisions.

---

## 8. Validation-to-Implementation Boundary

The following items are intentionally carried forward to the subsequent data-preparation stages:

* Treatment of the historical `BAMLH0A0HYM2` coverage gap
* Whether the HYG/SHY-derived signal should be included as an independent feature
* Daily alignment of additional derived features
* Point-in-time alignment
* Feature engineering
* Final ML suitability evaluation

These decisions are not implemented by modifying the canonical BAML series during the aggregation or QA stages.

---

## 9. Known Limitations for Downstream Stages
Macro release-lag alignment: Macro features (cpi, federal_funds_rate, m2_money_supply, ...etc.) are currently aligned on observation date rather than actual release date. Training directly on observation-date alignment introduces look-ahead bias and requires proper release-date shifting as a planned step in the preprocessing stage prior to model training.

---

## 10. Final Outcome & Approval Request

The **Data Quality Assurance and Validation Stage is complete**.

The stage delivered:

* **64/64 QA tests passed**
* Raw-source and aggregated-data validation completed
* Duplicate-date validation completed
* Historical source gaps identified and documented
* Canonical BAML high-yield spread gap investigated
* HYG/SHY daily data independently collected and validated
* Daily HYG/SHY-derived signal analyzed against daily BTC returns
* HYG/SHY maintained as a separate candidate feature
* No fabricated BAML observations introduced
* Canonical aggregated dataset preserved without proxy substitution

The canonical `high_yield_spread` feature remains based on `BAMLH0A0HYM2`.

The HYG/SHY-derived `high_yield_credit_stress_proxy` is carried forward as a separate candidate feature for evaluation in the subsequent data-preparation and ML stages.
