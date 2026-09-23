# Project Milestone Completion Report: Data Aggregation Stage

**Project:** MacroCrypto AI

**Status:** Finalized & Operational

**Date:** September 2026

## 1. Executive Summary

The **Data Aggregation Stage** for the MacroCrypto AI pipeline is now officially complete. All required historical market, macroeconomic, and on-chain datasets have been successfully backfilled, ingested, and compiled into a unified base dataset.

This stage strictly focused on data collection and structural traceability without applying premature transformations, ensuring raw source integrity is preserved for downstream point-in-time (PIT) alignment.

## 2. Key Implementation Highlights

### A. Timestamp & Date Management

* **`observation_date` Integration:** Derived directly from original UTC `time`/`timestamp` fields.

* **Point-in-Time Traceability:** Original source timestamps are strictly retained to support subsequent PIT alignment.

* **Standardization:** Daily aggregation is systematically indexed based on the UTC calendar date.

### B. Aggregation Engine (`aggregate_ml_data.py`)

* Deployed the core aggregation script, operating on the assumption that underlying historical data has been backfilled.

* Built-in validation checks raw source counts prior to applying the hard start-date filter (`2017-08-17`).

* The hard start date of August 17, 2017, was chosen because it marks the earliest available free API data for Binance's daily pricing and volume records, which serve as the primary daily foundation required to construct and align the remaining dataset features.

* Maintained strict pipeline boundaries: **No imputation, interpolation, forward-filling, feature engineering, target creation, or scaling** is performed at this layer.

### C. Comprehensive Data Source Catalog & Endpoints

The aggregation pipeline successfully integrates and standardizes inputs from the following official sources and endpoints:

* **BTC Prices (`btc_prices`):** 
  * *Endpoint:* `https://api.binance.com/api/v3` (Current and historical)
  * *Sources:* `binance_backfill` and `binance_ws+coingecko`.
* **BTC Dominance (`btc_dominance`):** 
  * *Current Endpoint:* `https://api.coingecko.com/api/v3` (CoinGecko)
  * *Historical Endpoint:* `https://bitcoin-data.com/v1/bitcoin-dominance/csv` (BGeometrics)
* **Gold Spot (`gold_spot`):** 
  * *Current Endpoint:* `https://query1.finance.yahoo.com/v8/finance/chart` (Yahoo Finance)
  * *Historical Endpoint:* `perthmint.com/globalassets/assets/metal-prices---csvs/historical-metals-page/csvs-archived-data-2016-2021/daily-gold-prices-01-01-2016-to-31-12-2021.csv` (Perth Mint archived data)
* **Macroeconomic Indicators (`macro_indicators` - FRED):** 
    * **Current Endpoint:** `https://api.stlouisfed.org/fred` (Handles CPI, DXY, Federal Funds Rate, GDP, M2 Money Supply, Nasdaq Composite, 10-Year Treasury, Unemployment, VIX, and High-Yield Spread).
    * **Historical Endpoint for High-Yield Spread:** `https://raw.githubusercontent.com/csaladenes/eco-archive/main/BAMLH0A0HYM2.csv` (An archive spanning December 1996 through March 2021, utilized because the FRED API restricts backfill history to the past 3 years).
* **On-Chain Metrics (`active_addresses`):** 
  * *Endpoint (Current & Historical):* `https://api.blockchain.info/charts` (Blockchain.com API)
* **Derived Metrics:** Equity correlation (`equity_corr`, computed from BTC/Nasdaq data).

---

## 3. Data Coverage Metrics

The database schema and coverage metrics across tables, features, and sources reflect the backfilled historical state:

### Table & Feature Coverage Matrix

| table_name | feature_name | rows | first_seen | last_seen | distinct_days | sort_order |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `btc_prices` | `btc_price` | 3,489 | 2017-08-17 00:00:00+00 | 2026-09-19 13:52:18+00 | 3,321 | 1 |
| `btc_prices` | `btc_volume` | 3,489 | 2017-08-17 00:00:00+00 | 2026-09-19 13:52:18+00 | 3,321 | 2 |
| `btc_dominance` | `btc_dominance` | 4,710 | 2013-04-29 02:00:00+00 | 2026-09-19 00:00:00+00 | 4,710 | 3 |
| `macro_indicators` | `gdp` | 318 | 1947-01-01 00:00:00+00 | 2026-04-01 00:00:00+00 | 318 | 4 |
| `macro_indicators` | `cpi` | 955 | 1947-01-01 00:00:00+00 | 2026-08-01 00:00:00+00 | 955 | 4 |
| `macro_indicators` | `unemployment` | 943 | 1948-01-01 00:00:00+00 | 2026-08-01 00:00:00+00 | 943 | 4 |
| `macro_indicators` | `federal_funds_rate` | 866 | 1954-07-01 00:00:00+00 | 2026-08-01 00:00:00+00 | 866 | 4 |
| `macro_indicators` | `m2_money_supply` | 811 | 1959-01-01 00:00:00+00 | 2026-07-01 00:00:00+00 | 811 | 4 |
| `macro_indicators` | `ten_year_treasury` | 16,163 | 1962-01-02 00:00:00+00 | 2026-09-17 00:00:00+00 | 16,163 | 4 |
| `macro_indicators` | `nasdaq_composite` | 14,023 | 1971-02-05 00:00:00+00 | 2026-09-18 00:00:00+00 | 14,023 | 4 |
| `macro_indicators` | `vix` | 9,276 | 1990-01-02 00:00:00+00 | 2026-09-17 00:00:00+00 | 9,276 | 4 |
| `macro_indicators` | `high_yield_spread` | 7,109 | 1996-12-31 00:00:00+00 | 2026-09-17 00:00:00+00 | 7,109 | 4 |
| `macro_indicators` | `dxy` | 5,188 | 2006-01-02 00:00:00+00 | 2026-09-11 00:00:00+00 | 5,188 | 4 |
| `macro_indicators` | `active_addresses` | 6,432 | 2009-01-03 00:00:00+00 | 2026-09-18 00:00:00+00 | 6,432 | 4 |
| `macro_indicators` | `gold_spot` | 2,524 | 2017-08-17 00:00:00+00 | 2026-09-18 04:00:00+00 | 2,524 | 4 |
| `macro_indicators` | `equity_corr` | 2,254 | 2017-10-02 00:00:00+00 | 2026-09-18 00:00:00+00 | 2,254 | 4 |

### Granular Source Breakdown

* **`btc_price` Sources:**
  * `binance_backfill`: 3,321 rows (2017-08-17 to 2026-09-19)
  * `binance_ws+coingecko`: 168 rows (2026-09-19 to 2026-09-19)

* **`btc_dominance` Sources:**
  * `bgeometrics_backfill`: 4,710 rows (2013-04-29 to 2026-09-19)

* **`macro_indicators` Sources:**
  * `active_addresses` (`blockchain.com`): 6,432 rows (2009-01-03 to 2026-09-18)
  * `cpi` (`fred`): 955 rows (1947-01-01 to 2026-08-01)
  * `dxy` (`fred`): 5,188 rows (2006-01-02 to 2026-09-11)
  * `equity_corr` (`derived`): 2,254 rows (2017-10-02 to 2026-09-18)
  * `federal_funds_rate` (`fred`): 866 rows (1954-07-01 to 2026-08-01)
  * `gdp` (`fred`): 318 rows (1947-01-01 to 2026-04-01)
  * `gold_spot` (`perth_mint_backfill`): 1,266 rows (2017-08-17 to 2021-09-13)
  * `gold_spot` (`yahoo_finance`): 1,258 rows (2021-09-20 to 2026-09-18)
  * `high_yield_spread` (`fred_archive_backfill`): 6,322 rows (1996-12-31 to 2021-03-19)
  * `high_yield_spread` (`fred`): 787 rows (2023-09-19 to 2026-09-17)
  * `m2_money_supply` (`fred`): 811 rows (1959-01-01 to 2026-07-01)
  * `nasdaq_composite` (`fred`): 14,023 rows (1971-02-05 to 2026-09-18)
  * `ten_year_treasury` (`fred`): 16,163 rows (1962-01-02 to 2026-09-17)
  * `unemployment` (`fred`): 943 rows (1948-01-01 to 2026-08-01)
  * `vix` (`fred`): 9,276 rows (1990-01-02 to 2026-09-17)

---

## 4. Data Limitations & Governance

To maintain total data transparency, known source discrepancies have been isolated and documented rather than artificially patched:

* **High-Yield Spread Gap:** The FRED series contains a historical data gap between March 2021 and September 2023.  Only official FRED data has been persisted to the primary database under `high_yield_spread`.
* **Proxy Dataset Quarantine:** To mitigate this a secondary proxy dataset (`high_yield_spread_proxy.csv`) has been prepared using the HYG/SHY methodology. It remains isolated from the main database pending **formal team approval** before addressing remaining historical gaps.

---

## 5. Final Dataset Specifications

* **Total Rows:** 3,321
* **Total Columns:** 32
* **Schema Scope:** Comprehensive coverage spanning BTC pricing, on-chain fundamentals, market liquidity indices, and macroeconomic indicators.
* **Traceability Fields:** Includes explicit `observation_date` and source timestamp mappings for auditability.

---
## 6. Canonical Aggregated Dataset Artifact

The aggregation stage produces a canonical CSV representing the exact output of `aggregate_ml_data.py` after the defined aggregation and hard-start-date filtering steps.

- **Artifact:** `app/data/ml_btc_daily_raw.csv`
- **Rows:** 3,321
- **Columns:** 32
- **Date range:** 2017-08-17 through 2026-09-16
- **Granularity:** One row per UTC calendar day
- **Purpose:** Immutable handoff artifact between the Data Aggregation and Data Validation/Cleaning stages.
- **Transformation status:** No imputation, interpolation, forward-filling, feature engineering, target construction, or scaling has been applied.
- **Traceability:** The dataset retains `observation_date` and source timestamp information required for downstream point-in-time alignment.
- **Reproducibility:** The CSV is generated directly from the aggregation pipeline and should be treated as the canonical output for validation and downstream processing.




## 7. Next Steps & Transition Plan

With data aggregation successfully concluded, the project is officially **transitioning to the Data Validation and Cleaning stage**. 

Immediate upcoming tasks include:
1. Formal evaluation of source gaps and missing observations.
2. Verification of timestamp alignment and structural coverage.
3. Review and approval gating for the high-yield spread proxy dataset prior to ML feature preprocessing.