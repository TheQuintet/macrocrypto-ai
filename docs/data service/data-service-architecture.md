# Data Service — Architecture

## 1. What the data-service owns

The data-service is the **single source of truth for market and macro data** in the macrocrypto-ai monorepo. It owns:

- **Raw ingestion** — pulling prices, dominance, macro indicators, and on-chain data from external providers (Binance, CoinGecko, FRED, Yahoo, Blockchain.com) into raw Postgres tables.
- **Aggregation** — materializing hourly wide tables (`btc_prices_hourly`, `macro_indicators_hourly`) from the raw tables.
- **Feature engineering** — producing the ML feature table (`features_db`) and (via Option A/B validation) hourly parquet outputs.
- **Schema** — migrations own all table definitions; `Base.metadata.create_all()` is removed from `init_db()`.
- **PIT correctness** — `macro_indicator_vintages` preserves release dates so the features writer can merge macro data point-in-time.

The data-service **does not** own:

- Model training, backtesting, or champion selection (AI Service).
- The frontend chart endpoints (those proxy Binance today; see `data-service-live-path-design.md` "Future work").
- The regime subsystem's schema (see §7 — it's in scope to *describe*, not to change).

## 2. Tables

### 2.1 Raw tables (untouched — D4, D14)

| Table | Purpose | Notes |
|---|---|---|
| `btc_prices` | Tick + daily + hourly BTC prices | Long-lived; `source` column distinguishes feeds (`binance_backfill`, `binance_backfill_hourly`, live WS, etc.) |
| `macro_indicators` | Long-format macro series | `indicator_name` + `observation_date`; final values only, no release dates |
| `btc_dominance` | BTC dominance observations | Untouched per D14; its value flows into `btc_prices_hourly.dominance` |

Raw schemas are frozen. Migration `004_create_raw_tables_idempotent.sql` makes their creation idempotent so a fresh DB works without `create_all()`.

### 2.2 New materialized hourly tables (D5–D7)

**`btc_prices_hourly` — 8 columns (D6)**

| Column | Type | Notes |
|---|---|---|
| `time` | TIMESTAMPTZ | Primary key; hour (UTC) |
| `close` | DOUBLE PRECISION | |
| `volume` | DOUBLE PRECISION | |
| `volatility` | DOUBLE PRECISION | |
| `dominance` | DOUBLE PRECISION | Fed from `btc_dominance` (D14) |
| `active_addresses` | DOUBLE PRECISION | |
| `price_lag_7d` | DOUBLE PRECISION | |
| `created_at` | TIMESTAMPTZ | Default `now()` |

**`macro_indicators_hourly` — 7 columns (D7)**

| Column | Type | Notes |
|---|---|---|
| `time` | TIMESTAMPTZ | Primary key |
| `cpi` | DOUBLE PRECISION | Note: features writer uses vintages, not this, for ML (A2) |
| `interest_rate` | DOUBLE PRECISION | Renamed to `federal_funds_rate` in `features_db` |
| `m2_growth` | DOUBLE PRECISION | Renamed to `m2_money_supply` in `features_db` |
| `dxy` | DOUBLE PRECISION | Direct into `features_db` |
| `treasury_yield` | DOUBLE PRECISION | Renamed to `ten_year_treasury` in `features_db` |
| `created_at` | TIMESTAMPTZ | Default `now()` |

### 2.3 `features_db` (D8)

53 columns per contract v2. Full DDL in `data-service-schemas.md`. Type story: **45 base + 6 engineered = DOUBLE PRECISION; 4 flags + 14 trackers = INTEGER** (never BOOLEAN — D8). Recency trackers stored in **HOURS** but keep the `_days_since_*` suffix (D8).

### 2.4 `macro_indicator_vintages` (D15)

Point-in-time store for revision-prone macro series. Full DDL in `data-service-schemas.md`.

Populated for **5 series only**: `CPIAUCSL`, `UNRATE`, `FEDFUNDS`, `M2SL`, `GDP`. Market features (DXY, VIX, 10Y, NASDAQ, HY spread) are not revision-prone and don't get vintages.

The `UNIQUE` constraint is **named** (`uq_macro_vintage_series_obs_release`) so the repository's `ON CONFLICT DO NOTHING` can target it by name — same pattern as `uq_macro_indicator_time_name` on raw `macro_indicators`.

**No-op vintage policy:** the schema permits consecutive same-value vintages; the service filters them before writing. Halves the row count without changing PIT-merge results. Applied in the service, not the table. See `migrations/008_create_macro_indicator_vintages.sql`.

## 3. Sources and cadences

| Source | Native frequency | Collector / writer | Cadence | Writes to |
|---|---|---|---|---|
| Binance WebSocket (`btcusdt@ticker`) | sub-second | `BTCWebSocketClient` | continuous | `btc_prices` (ticks) |
| Binance REST klines `1d` | daily | `run_backfills.py::backfill_btc_prices` | manual | `btc_prices` (`source="binance_backfill"`) |
| Binance REST klines `1h` | hourly | `hourly_backfill_service.py` | on-demand + weekly scheduled | `btc_prices` (`source="binance_backfill_hourly"`) |
| Binance REST 24hr ticker | every 60s | `periodic_price_collection` (main.py) | continuous | in-memory only |
| CoinGecko `/global` (dominance) | 15-min | `BTCDominanceService` | every 900s | `btc_dominance` |
| CoinGecko `/simple/price` | 15-min | `MarketCapService` | every 900s | Redis only |
| BGeometrics dominance CSV | daily | `run_backfills.py::backfill_btc_dominance` | manual | `btc_dominance` |
| FRED (10 series) | daily/monthly/quarterly | `IndicatorService` | daily 01:00 UTC | `macro_indicators` |
| FRED release dates | event-based | `EconomicCalendarService` | daily 01:00 UTC | `economic_events` |
| Blockchain.com active_addresses | daily | `ActiveAddressesService` | daily (macro task) | `macro_indicators` |
| Yahoo gold spot `XAUUSD=X` | daily | `GoldSpotService` | daily (macro task) | `macro_indicators` |
| Yahoo gold spot `1h` | hourly | `hourly_backfill_service.py` | on-demand | `macro_indicators` (`source="yahoo_hourly"`) |
| Yahoo HYG/SHY | daily | `HighYieldCreditStressService` | daily 03:00 UTC | `macro_indicators` (`indicator_name='high_yield_credit_stress_proxy'`, `source='derived'`) |
| FRED vintages | event-based | `MacroVintageService` | daily 03:30 UTC | `macro_indicator_vintages` |
| `btc_prices` → `btc_prices_hourly` | hourly | `HourlyBTCPricesService` | hourly at :01 | `btc_prices_hourly` |
| `macro_indicators` → `macro_indicators_hourly` | hourly | `HourlyMacroIndicatorsService` | hourly at :02 | `macro_indicators_hourly` |
| hourly + vintages → `features_db` | hourly | `FeaturesDBWriter` | hourly at :05 | `features_db` |

**Status (as of Chat 5):** the daily macro/FRED, economic calendar, current regime, hourly BTC, hourly macro, hourly gap scan, HY credit stress proxy (B5), and macro vintage (B6) tasks are all wired. `features_db` (B4) is the remaining scheduled writer.

**Schedule staggering (all UTC):**

| Time | Task |
|---|---|
| 01:00 | Macro/FRED + economic calendar (existing) |
| 01:00 | Current regime (existing) |
| 03:00 | HY credit stress proxy (B5) |
| 03:30 | Macro vintage (B6) |
| :01 (hourly) | BTC hourly materialization |
| :02 (hourly) | Macro hourly materialization |
| :05 (hourly) | Features DB writer (B4, pending) |
| every 6h | Hourly gap scan |
| every 900s | Dominance + market cap |

## 4. Data flow

```
External providers
  ├─ Binance (WS, REST klines)
  ├─ CoinGecko (dominance, marketcap)
  ├─ FRED (macro series, release dates, vintages)
  ├─ Yahoo (gold spot, HYG/SHY)
  └─ Blockchain.com (active_addresses)
        │
        ▼
Raw tables (frozen schemas)
  ├─ btc_prices
  ├─ macro_indicators
  └─ btc_dominance
        │
        ├──────────────────────────┐
        ▼                          ▼
Hourly materialization       (regime subsystem reads
  ├─ btc_prices_hourly         raw macro_indicators —
  └─ macro_indicators_hourly   see §7)
        │
        ▼
macro_indicator_vintages
(PIT, 5 series only)
        │
        ▼
features_db (53 cols)
  ├─ market/on-chain from btc_prices_hourly + raw
  ├─ non-PIT macro from macro_indicators_hourly
  └─ PIT macro from macro_indicator_vintages
        │
        ├─► AI Service (config defaults point here;
        │   fetch_training_frame_from_features_db)
        │
        └─► Option A/B hourly parquet
              ├─ processed_v2_scripts/ (A)
              └─ processed_v2_builder/ (B)

FROZEN (D13, D21): app/data/processed/  — daily parquet, reference only
```

## 5. Migrations

Existing:
```
001_create_regime_tables.sql
002_create_economic_calendar_tables.sql
003_add_schema_migrations.sql
004_create_raw_tables_idempotent.sql
005_create_btc_prices_hourly.sql
006_create_macro_indicators_hourly.sql
007_promote_hourly_to_hypertables.sql
```

New (Phase B, continuing the sequence):

| File | Purpose | Origin |
|---|---|---|
| `008_create_macro_indicator_vintages.sql` | D15 table | Chat 5, B6 |
| `009_create_features_db.sql` | D8 table | Chat 5, B4 — sibling branch |

**Numbering note:** migration numbers do **not** match landing order. `007_promote_hourly_to_hypertables.sql` (Chat 3) occupied the `007` slot for a concern unrelated to `features_db`, so `features_db` moved to `009`. The sequence is monotonic by filename only: `007` → `008` → `009`. `008` and `009` are independent at the DDL level; the dependency between them is at the data level (B4's features writer reads vintages for PIT merges), and the runner sorts by filename so `008` always runs first at runtime.

The removal of `create_all()` is a **code change to `session.py`**, not a migration.

## 6. Paths (summary)

Four paths, documented in full in `data-service-paths.md`:

1. **Live** — continuous scheduled ingestion + hourly writers.
2. **Manual ML** — daily parquet pipeline. Frozen.
3. **Backfill** — populating raw tables from external sources. Scheduled + CLI.
4. **Option A/B validation** — dual hourly parquet generation. Time-boxed.

All four share the raw tables; they differ in trigger and output.

## 7. Regime subsystem (brief — untouched)

The regime subsystem serves the **frontend**, not the AI Service. It reads raw `macro_indicators` and produces regime classifications. It does **not** write to any raw table in a way this work affects, and it does not consume `features_db`, the hourly tables, or the vintages. Its schema (`001_create_regime_tables.sql`) is untouched.

Reason it's out of scope for this work: see `data-service-live-path-design.md` §"Why the regime subsystem is out of scope".

## 8. Open items — adjustable in later chats

- Stagger minutes for scheduled writers (`:01`/`:02`/`:05`) — currently `:01` BTC, `:02` macro, `:05` features_db (pending B4).
- Exact minute for the weekly scheduled Binance hourly backfill — Chat 3.