# Data Service — Live Path Design

This document records the locked design decisions (D1–D23) with rationale, the narrow-table justification, the alignment guarantee, the aggregation-options catalog, the "when to widen a table" rule, the four paths, the regime-subsystem scope note, the hourly-OHLC future-work note, and the AI Service handoff flag.

## 1. Decisions D1–D23

### Paths

**D1 — Three paths (now four, see §2): manual ML, live, backfill. Each has both a scheduled and a CLI trigger.**
Rationale: scheduled runs keep the system fresh without human intervention; CLI triggers allow ad-hoc recovery and development without duplicating logic. The fourth path (Option A/B validation) is a temporary addition for D18–D23.

**D2 — CLI calls the same service methods the scheduler calls.**
Rationale: one implementation, two triggers. Prevents drift between "what the scheduler does" and "what a human does when fixing something."

**D3 — Manual ML path preserved.**
Rationale: it's the current production path for the AI Service. Changing it during migration risks breaking training. Preserve it until Option B is trusted (D23).

**D13 — Old daily parquet stays at `app/data/processed/` — FROZEN.**
Rationale: reference baseline. Also serves as an escape hatch if the hourly migration has issues. Never written to again.

### Schema ownership

**D4 — Raw tables untouched: `btc_prices`, `macro_indicators`, `btc_dominance`.**
Rationale: the AI Service, regime subsystem, and existing jobs read these. Changing them is a cross-service breaking change with no upside — the new work materializes *new* tables instead.

**D5 — Migrations own schema. Add `schema_migrations` table. Remove `Base.metadata.create_all()` from `init_db()`.**
Rationale: `create_all()` cannot express changes (only creation), can't be ordered, and hides schema drift. Migrations make every change explicit, ordered, and idempotent.

**D14 — `btc_dominance` raw table untouched; its value flows into `btc_prices_hourly.dominance`.**
Rationale: dominance is a market feature, not a revision-prone macro series. The hourly writer reads the raw table and writes the current value.

**D15 — New table `macro_indicator_vintages` for PIT macro data.**
Rationale: FRED series like CPI, UNRATE, GDP get revised. Training on final values leaks future information. Vintages preserve release dates so the features writer can merge point-in-time.

**D17 — `high_yield_credit_stress_proxy` → raw `macro_indicators` via a new service.**
Rationale: this is a market feature, not revision-prone. It belongs in the raw layer alongside VIX, gold, etc. A dedicated service keeps the computation testable and its cadence independent.

### New tables

**D5 — Three new materialized hourly tables: `btc_prices_hourly`, `macro_indicators_hourly`, `features_db`.**
Rationale: hourly is the AI Service's new resolution (see §5 alignment guarantee). Materializing hourly tables makes the features writer cheap and the AI Service's config change trivial.

**D6 — `btc_prices_hourly`: 8 cols (`time`, `close`, `volume`, `volatility`, `dominance`, `active_addresses`, `price_lag_7d`, `created_at`).**
See §3 for the narrow-table justification.

**D7 — `macro_indicators_hourly`: 7 cols including `created_at` (`time`, `cpi`, `interest_rate`, `m2_growth`, `dxy`, `treasury_yield`, `created_at`).**
See §3 for the narrow-table justification.

**D8 — `features_db`: 53 cols per contract v2. Flags typed INTEGER (not BOOLEAN).**
Rationale for INTEGER flags: the AI Service's loader expects numeric; booleans become 0/1 anyway but with type ambiguity across drivers. Integer is explicit.

### Semantics

**D8 — Recency trackers stored in HOURS; column names keep `_days_since_*` suffix.**
Rationale: the names are part of the AI Service contract and cannot change. The values change to hours because the resolution is hourly. This is a documented quirk, not a bug.

**D9 — `y` = price at `ds + 1h`. Writer lags 1 hour.**
Rationale: hourly prediction means the next hour's price. The writer lagging 1 hour means the current hour's feature row is written after `ds + 1h` exists, so `y` is always populated (never NaN at the frontier).

**D11 — Windows × 24 (7d = 168h, 30d = 720h, 90d = 2160h). Annualization factor becomes √(365 × 24).**
Rationale: semantic preservation. A "7-day SMA" means the same *thing* at hourly resolution; it's computed over 168 hours.

**D12 — Alignment guarantee: hourly features mean the same as daily; price-derived features are bit-identical at day boundaries; window-based features differ numerically but are semantically equivalent.**
See §5.

### AI Service integration

**D9 — AI Service config defaults → `btc_prices_hourly`, `macro_indicators_hourly`.**
Rationale: the AI Service reads hourly tables directly where it can. Only the two permitted changes (config defaults + `fetch_training_frame_from_features_db`).

**D12 — Analytics jobs read the hourly tables.**
Rationale: correlation and event-impact jobs operate on the highest available resolution.

**D8 — No AI Service job changes except config defaults and implementing `fetch_training_frame_from_features_db`.**
Rationale: minimize cross-service risk.

### Backfill

**D8 — New `hourly_backfill_service.py`:**
- BTC: Binance klines `interval="1h"`, `source="binance_backfill_hourly"`
- Gold: Yahoo `interval="1h"` for last ~730 days, `source="yahoo_hourly"`

`run_backfills.py` UNCHANGED.

**D17 — Frontend readiness first (Phase A), then AI integration (Phase B).**

### Parallel validation

**D18 — Parquet path becomes hourly.**
**D19 — Two implementations run in parallel: Option A (modified four scripts) and Option B (unified feature builder).**
**D20 — Outputs to separate dirs: `processed_v2_scripts/` (A), `processed_v2_builder/` (B).**
**D21 — Old daily parquet at `processed/` stays FROZEN.**
**D22 — Option B writes both parquet (`processed_v2_builder/`) AND `features_db`.**
**D23 — Option A is time-boxed; retired once Option B is trusted.**

Rationale for the whole D18–D23 block: validation by parallel implementation. Two independent pipelines producing hourly parquet lets us diff them column-by-column before committing to one. Option B is the target (it's unified and writes `features_db`); Option A is the safety net.

## 2. The four paths (summary; full in `data-service-paths.md`)

1. **Live** — scheduled continuous ingestion + hourly writers.
2. **Manual ML** — daily parquet pipeline, frozen.
3. **Backfill** — populating raw tables from external sources, scheduled + CLI.
4. **Option A/B validation** — dual hourly parquet, time-boxed.

The handoff calls these "three paths" (D1). The addendum re-frames as four. The three-path framing is preserved in D1; the fourth is a temporary validation path. Both framings are correct at different scopes.

## 3. Narrow-table justification

### Why `btc_prices_hourly` has 8 columns

The hourly table is **not** a mirror of raw `btc_prices`. It's a *materialized, ML-ready, hourly-resolution* projection containing exactly the BTC-side features `features_db` needs from the BTC path:

- `time`, `close`, `volume` — base OHLC-like data
- `volatility` — precomputed because it's expensive and reused
- `dominance` — from `btc_dominance` (D14)
- `active_addresses` — on-chain, hourly-aligned
- `price_lag_7d` — precomputed lag
- `created_at` — operational

Anything else the features writer needs (VIX, gold, etc.) comes from other tables. Widening `btc_prices_hourly` would duplicate storage for no benefit.

### Why `macro_indicators_hourly` has 7 columns

Same logic: it holds the macro features that are (a) not revision-prone and (b) needed at hourly resolution. The 5 revision-prone series live in `macro_indicator_vintages` and are merged by the features writer (addendum A2). Market features that don't need hourly materialization (VIX, gold, HY, NASDAQ, equity_corr, HY proxy, active_addresses) stay in raw `macro_indicators` and are ffilled by the features writer.

The result: `macro_indicators_hourly` holds only what the *analytics jobs* (D12) need at hourly resolution plus the two market features (`dxy`, `treasury_yield`) that `features_db` reads directly.

### The "when to widen a table" rule

**Widen only when a new consumer needs a new feature at the table's native resolution AND that feature cannot be derived cheaply at read time.**

Corollaries:
- New *derived* feature (e.g., a new SMA)? Don't widen. Compute in the features writer.
- New *raw* feature that the analytics jobs need hourly? Widen `macro_indicators_hourly` (or add a new hourly table, not widen the existing one, if the new feature is a different domain).
- New *revision-prone* series? Never widen an hourly table. Add to `macro_indicator_vintages` and merge in the features writer.

## 4. Aggregation options catalog

When materializing hourly tables from raw, each source column needs an explicit rule. The catalog:

| Rule | When to use | Example |
|---|---|---|
| `last` | Value is a level that updates; take the latest within the hour | `close`, `dominance` |
| `sum` | Value is a flow that accumulates; sum within the hour | `volume` |
| `mean` | Value is noisy; averaging within the hour reduces noise | `volatility` (already computed upstream, then mean) |
| `ffill` | Value updates infrequently; carry forward | macro indicators |
| `rolling(N)` | Feature is defined over a window | SMAs, volatility |
| `shift(N)` | Feature is a lag | `price_lag_7d`, engineered lags |

**Rule:** every source → hourly column mapping in the schemas doc must pick exactly one of these (or a documented composition). No implicit defaults.

## 5. Alignment guarantee explained

The guarantee (D12) is about **semantics**, not numbers.

- **Price-derived features** (e.g., `btc_price`, `btc_log_return_1d`) are **bit-identical at day boundaries**. If you take the hourly row whose `ds` is exactly midnight UTC and compare its `btc_log_return_1d` to the daily pipeline's `btc_log_return_1d` for that day, they are the same float.
- **Window-based features** (e.g., `btc_sma_7`) **differ numerically** because the window is computed over 168 hours, not 7 days. But they mean the same thing: "the average close over the last 7 days."
- **Recency trackers** are stored in hours but keep their `_days_since_*` names. A value of `24` in `cpi_days_since_release` means "24 hours since release," i.e., 1 day. The AI Service contract is unchanged (same column names, same relative semantics), but the unit is hours.

**Same meaning vs. same number:** same meaning is required; same number is required only for price-derived features.

## 6. Why the regime subsystem is out of scope

The regime subsystem:

1. **Serves the frontend, not the AI Service.** It produces regime classifications for display. Its consumers don't read `features_db`, the hourly tables, or the vintages.
2. **Reads raw `macro_indicators`** — which this work does not touch (D4). The regime subsystem's read path is unaffected by the new tables.
3. **Doesn't touch raw tables in ways our changes affect.** The hourly writers *read* raw tables; they don't modify them. The regime subsystem's view of raw data is identical before and after this work.
4. **Has its own schema** (`001_create_regime_tables.sql`), which is untouched.

Therefore: no changes to the regime subsystem, and no coordination needed between this work and whoever owns it.

## 7. Future work: hourly OHLC from our own DB

**This is a note, not a decision.**

Today the frontend's chart endpoint (`GET /api/v1/btc/price/history`) proxies Binance REST klines directly. This is correct — Binance is authoritative.

Once `btc_prices_hourly` exists, it becomes possible to serve historical OHLC from our own DB (`SELECT` from `btc_prices_hourly`). This would enable:

- faster responses (no round-trip to Binance)
- auditing (prove what price we saw at what time)
- offline operation
- single source of truth for live and historical

**Not in this plan.** A future chat can add a DB-backed history endpoint if needed.

## 8. Flag to the AI Service team

**This is an explicit handoff item.**

> **Subject: Parquet resolution changes from daily to hourly**
>
> The data-service is changing the parquet feature output from daily to hourly. This affects the AI Service's training and backtesting paths.
>
> **What changes:**
> - The parquet files (`train_scaled.parquet`, `val_scaled.parquet`, `test_scaled.parquet`, `live_frontier_scaled.parquet`) will contain hourly rows, not daily.
> - Row count goes from ~3,300 rows to ~70,000+ rows (about 24×).
> - The scaler (`feature_scaler.pkl`) is fit on hourly data.
> - Feature windows change semantics: `btc_sma_7` becomes a 168-hour (7-day) moving average instead of a 7-day average. Same semantic, hourly resolution.
> - Volatility annualization changes from `sqrt(365)` to `sqrt(365*24)`.
> - The target `y` (was `target_next_price`) now means the next hour's price, not the next day's price.
>
> **What the AI Service team may need to review:**
> - Training time: 24× more rows. Consider `history_hours` settings (2160, 2880), backtest windows.
> - Split configs: `purge_window: int = 90` and `embargo_window: int = 7` were days; in hourly terms they should be 2160 and 168 hours.
> - Backtest configs: `backtest_history_hours: int = 2880` was really 8 years when read from daily rows. Now 2880 = 120 days. This is the fix for the MAE == RMSE horizon bug — but it also means the backtest now operates on genuinely hourly data, so results will differ.
> - Champion selection windows: `champion_primary_lookback_days` and `champion_secondary_lookback_days` operate on `forecast_date`. With hourly predictions, those are still days — no change needed — but verify sample sizes remain meaningful (`champion_min_sample_size: int = 100`).
> - Model performance: tree models benefit from more data; Prophet may need `changepoint_prior_scale` tuning.
>
> **What does NOT change:**
> - Read path — `FeatureLoader` and `fetch_training_frame_from_files` are resolution-agnostic.
> - Column names — same 60 columns (`ds`, `y`, 45 base features, 6 engineered).
> - Column types.
>
> **How the AI Service reaches the new output:**
> - Option B (`processed_v2_builder/`) is the target.
> - Option A (`processed_v2_scripts/`) is available during a validation window.
> - Old daily parquet at `processed/` stays frozen as reference.
> - Switch by changing the `SHARED_DATA_DIR` env var.
>
> **What we need from the AI Service team:**
> - Review whether any training/backtest configs assume daily rows.
> - Confirm `fetch_training_frame_from_features_db` is implemented when `features_db` lands.
> - Consider whether the champion promotion job's stability gate (`champion_stability_days: int = 3`) still makes sense with hourly predictions.

## 9. Open items — adjustable in later chats

- Stagger minutes (`:01`/`:02`/`:05`).
- `004_create_raw_tables_idempotent.sql` is newly proposed.