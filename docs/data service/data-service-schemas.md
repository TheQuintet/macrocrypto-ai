# Data Service — Schemas

## 1. DDL — `btc_prices_hourly` (D6)

```sql
CREATE TABLE btc_prices_hourly (
    time                TIMESTAMPTZ      NOT NULL,
    close               DOUBLE PRECISION,
    volume              DOUBLE PRECISION,
    volatility          DOUBLE PRECISION,
    dominance           DOUBLE PRECISION,
    active_addresses    DOUBLE PRECISION,
    price_lag_7d        DOUBLE PRECISION,
    created_at          TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (time)
);

CREATE INDEX idx_btc_prices_hourly_time_desc
    ON btc_prices_hourly (time DESC);
```

## 2. DDL — `macro_indicators_hourly` (D7)

```sql
CREATE TABLE macro_indicators_hourly (
    time             TIMESTAMPTZ      NOT NULL,
    cpi              DOUBLE PRECISION,
    interest_rate    DOUBLE PRECISION,
    m2_growth        DOUBLE PRECISION,
    dxy              DOUBLE PRECISION,
    treasury_yield   DOUBLE PRECISION,
    created_at       TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (time)
);

CREATE INDEX idx_macro_indicators_hourly_time_desc
    ON macro_indicators_hourly (time DESC);
```

## 3. DDL — `features_db` (D8, contract v2)

> **Feature contract: 47 columns.** The frozen parquet files (`train_scaled.parquet` and siblings) are the source of truth: `ds` + `y` + 45 features. The 53-column contract v2 is abandoned. The table below still carries 6 `eng_*` columns from migration 009; they are **deprecated**, are not part of the contract, and no consumer reads them. Lag/return features derived from `y` leak the target (`y` is the next price), so any lag features must come from `btc_price`.

```sql
CREATE TABLE features_db (
    -- Timestamp and target (2)
    ds                                TIMESTAMPTZ      NOT NULL,
    y                                 DOUBLE PRECISION NOT NULL,

    -- Raw market & on-chain (4)
    btc_price                         DOUBLE PRECISION,
    btc_volume                        DOUBLE PRECISION,
    btc_dominance                     DOUBLE PRECISION,
    active_addresses                  DOUBLE PRECISION,

    -- Macro & external assets (13)
    gold_spot                         DOUBLE PRECISION,
    dxy                               DOUBLE PRECISION,
    ten_year_treasury                 DOUBLE PRECISION,
    vix                               DOUBLE PRECISION,
    high_yield_spread                 DOUBLE PRECISION,
    nasdaq_composite                  DOUBLE PRECISION,
    equity_corr                       DOUBLE PRECISION,
    high_yield_credit_stress_proxy    DOUBLE PRECISION,
    cpi                               DOUBLE PRECISION,
    federal_funds_rate                DOUBLE PRECISION,
    gdp                               DOUBLE PRECISION,
    m2_money_supply                   DOUBLE PRECISION,
    unemployment                      DOUBLE PRECISION,

    -- Technical indicators & ratios (10)
    btc_log_return_1d                 DOUBLE PRECISION,
    btc_log_return_7d                 DOUBLE PRECISION,
    btc_log_return_30d                DOUBLE PRECISION,
    btc_sma_7                         DOUBLE PRECISION,
    btc_sma_30                        DOUBLE PRECISION,
    btc_sma_90                        DOUBLE PRECISION,
    btc_volatility_7d                 DOUBLE PRECISION,
    btc_volatility_30d                DOUBLE PRECISION,
    btc_gold_ratio                    DOUBLE PRECISION,
    btc_nasdaq_ratio                  DOUBLE PRECISION,

    -- Data-quality flags (4) — INTEGER, not BOOLEAN
    high_yield_spread_is_missing      INTEGER,
    active_addresses_is_imputed       INTEGER,
    unemployment_is_imputed           INTEGER,
    warmup_complete                   INTEGER,

    -- Observation recency trackers (14) — INTEGER, stored in HOURS,
    -- names keep the _days_since_* suffix (D8)
    btc_dominance_days_since_last_observation                INTEGER,
    gold_spot_days_since_last_observation                    INTEGER,
    dxy_days_since_last_observation                          INTEGER,
    ten_year_treasury_days_since_last_observation            INTEGER,
    vix_days_since_last_observation                          INTEGER,
    nasdaq_composite_days_since_last_observation             INTEGER,
    equity_corr_days_since_last_observation                  INTEGER,
    high_yield_credit_stress_proxy_days_since_last_observation INTEGER,
    active_addresses_days_since_last_observation             INTEGER,
    cpi_days_since_release                                   INTEGER,
    federal_funds_rate_days_since_release                    INTEGER,
    gdp_days_since_release                                   INTEGER,
    m2_money_supply_days_since_release                       INTEGER,
    unemployment_days_since_release                          INTEGER,

    -- Deprecated engineered features (6) — outside the 47-column contract
    eng_price_lag_1d                  DOUBLE PRECISION,
    eng_price_lag_7d                  DOUBLE PRECISION,
    eng_price_lag_30d                 DOUBLE PRECISION,
    eng_returns_1d                    DOUBLE PRECISION,
    eng_returns_7d                    DOUBLE PRECISION,
    eng_returns_30d                   DOUBLE PRECISION,

    PRIMARY KEY (ds)
);

CREATE INDEX idx_features_db_ds_desc ON features_db (ds DESC);
```

**Contract: 2 + 4 + 13 + 10 + 4 + 14 = 47** (matches the frozen parquet). The physical table has 53 columns including the 6 deprecated `eng_*` columns.

## 4. DDL — `macro_indicator_vintages` (D15)

```sql
CREATE TABLE macro_indicator_vintages (
    id                SERIAL PRIMARY KEY,
    series_id         VARCHAR(50)      NOT NULL,
    indicator_name    VARCHAR(100)     NOT NULL,
    observation_date  DATE             NOT NULL,
    release_date      DATE             NOT NULL,
    value             DOUBLE PRECISION NOT NULL,
    created_at        TIMESTAMPTZ      NOT NULL DEFAULT now(),

    CONSTRAINT uq_macro_vintage_series_obs_release
        UNIQUE (series_id, observation_date, release_date)
);

CREATE INDEX idx_macro_vintages_series_obs
    ON macro_indicator_vintages (series_id, observation_date);
CREATE INDEX idx_macro_vintages_release
    ON macro_indicator_vintages (release_date);
```

The `UNIQUE` constraint is **named** (`uq_macro_vintage_series_obs_release`) so the repository's `ON CONFLICT DO NOTHING` can target it by name, matching the pattern of `uq_macro_indicator_time_name` on the raw `macro_indicators` table.

Populated for **5 series only**:

| `series_id` | `indicator_name` |
|---|---|
| `CPIAUCSL` | `cpi` |
| `UNRATE` | `unemployment` |
| `FEDFUNDS` | `federal_funds_rate` |
| `M2SL` | `m2_money_supply` |
| `GDP` | `gdp` |

**Retention:** unlimited (a few thousand rows per year after the no-op vintage filter).

**No-op vintage policy:** the schema permits multiple vintages for the same `(series_id, observation_date)` regardless of whether the value changed. The service (`MacroVintageService`) filters out consecutive same-value vintages before writing. This halves the row count without changing PIT-merge results: "latest `release_date <= H`" still yields the value in force at `H`. See `migrations/008_create_macro_indicator_vintages.sql` for the full policy note.

## 5. Column-by-column source mapping for `features_db`

**All 5 PIT-prone series are merged in the features writer from `macro_indicator_vintages`.** The three-source macro rule:

- **Source 1 — `macro_indicator_vintages`** (5 series, PIT merge in features writer)
- **Source 2 — `macro_indicators_hourly`** (2 series, direct)
- **Source 3 — raw `macro_indicators`** (7 market features, ffill)

| # | Column | Source | Daily rule | Hourly rule |
|---|---|---|---|---|
| 1 | `ds` | — | the day (UTC) | the hour (UTC) |
| 2 | `y` | `btc_prices_hourly.close` | next day's close | value at `ds + 1h` (writer lags 1h) |
| 3 | `btc_price` | `btc_prices_hourly.close` | direct | direct |
| 4 | `btc_volume` | `btc_prices_hourly.volume` | direct | direct |
| 5 | `btc_dominance` | `btc_prices_hourly.dominance` | direct | direct |
| 6 | `active_addresses` | raw `macro_indicators` (`indicator_name='active_addresses'`) | ffill | ffill, limit = 120h |
| 7 | `gold_spot` | raw `macro_indicators` (`indicator_name='gold_spot'`) | ffill | ffill unlimited |
| 8 | `dxy` | `macro_indicators_hourly.dxy` | direct | direct |
| 9 | `ten_year_treasury` | `macro_indicators_hourly.treasury_yield` | **rename** | **rename** |
| 10 | `vix` | raw `macro_indicators` (`indicator_name='vix'`) | ffill | ffill unlimited |
| 11 | `high_yield_spread` | raw `macro_indicators` (`indicator_name='high_yield_spread'`) | ffill; flag if NaN | ffill unlimited; flag if NaN |
| 12 | `nasdaq_composite` | raw `macro_indicators` (`indicator_name='nasdaq_composite'`) | ffill | ffill unlimited |
| 13 | `equity_corr` | raw `macro_indicators` (`indicator_name='equity_corr'`) | ffill | ffill unlimited |
| 14 | `high_yield_credit_stress_proxy` | raw `macro_indicators` (`indicator_name='high_yield_credit_stress_proxy'`) | ffill | ffill unlimited |
| 15 | `cpi` | `macro_indicator_vintages` (`indicator_name='cpi'`) | PIT merge | PIT merge in features writer |
| 16 | `federal_funds_rate` | `macro_indicator_vintages` (`indicator_name='federal_funds_rate'`) | PIT merge | PIT merge in features writer |
| 17 | `gdp` | `macro_indicator_vintages` (`indicator_name='gdp'`) | PIT merge | PIT merge in features writer |
| 18 | `m2_money_supply` | `macro_indicator_vintages` (`indicator_name='m2_money_supply'`) | PIT merge | PIT merge in features writer |
| 19 | `unemployment` | `macro_indicator_vintages` (`indicator_name='unemployment'`) | PIT merge; ffill; flag if imputed | PIT merge in features writer; ffill; flag if imputed |
| 20 | `btc_log_return_1d` | `btc_prices_hourly.close` | `log(p / p.shift(1))` | `log(p / p.shift(24))` |
| 21 | `btc_log_return_7d` | `btc_prices_hourly.close` | `log(p / p.shift(7))` | `log(p / p.shift(168))` |
| 22 | `btc_log_return_30d` | `btc_prices_hourly.close` | `log(p / p.shift(30))` | `log(p / p.shift(720))` |
| 23 | `btc_sma_7` | `btc_prices_hourly.close` | `rolling(7, min_periods=7).mean()` | `rolling(168, min_periods=168).mean()` |
| 24 | `btc_sma_30` | `btc_prices_hourly.close` | `rolling(30, min_periods=30).mean()` | `rolling(720, min_periods=720).mean()` |
| 25 | `btc_sma_90` | `btc_prices_hourly.close` | `rolling(90, min_periods=90).mean()` | `rolling(2160, min_periods=2160).mean()` |
| 26 | `btc_volatility_7d` | `btc_log_return_1d` | `rolling(7).std(ddof=1) * sqrt(365)` | `rolling(168).std(ddof=1) * sqrt(365*24)` |
| 27 | `btc_volatility_30d` | `btc_log_return_1d` | `rolling(30).std(ddof=1) * sqrt(365)` | `rolling(720).std(ddof=1) * sqrt(365*24)` |
| 28 | `btc_gold_ratio` | `btc_price / gold_spot` | direct | direct |
| 29 | `btc_nasdaq_ratio` | `btc_price / nasdaq_composite` | direct | direct |
| 30 | `high_yield_spread_is_missing` | flag | 1 if NaN after ffill | 1 if NaN after ffill |
| 31 | `active_addresses_is_imputed` | flag | 1 if ffilled | 1 if ffilled |
| 32 | `unemployment_is_imputed` | flag | 1 if ffilled | 1 if ffilled |
| 33 | `warmup_complete` | flag | 1 if `btc_sma_90` not NaN | 1 if `btc_sma_90` not NaN |
| 34 | `btc_dominance_days_since_last_observation` | `btc_dominance` | days since last real observation | hours since last real observation |
| 35 | `gold_spot_days_since_last_observation` | raw `macro_indicators` | days since last real observation | hours since last real observation |
| 36 | `dxy_days_since_last_observation` | `macro_indicators_hourly` | days since last real observation | hours since last real observation |
| 37 | `ten_year_treasury_days_since_last_observation` | `macro_indicators_hourly` | days since last real observation | hours since last real observation |
| 38 | `vix_days_since_last_observation` | raw `macro_indicators` | days | hours |
| 39 | `nasdaq_composite_days_since_last_observation` | raw `macro_indicators` | days | hours |
| 40 | `equity_corr_days_since_last_observation` | raw `macro_indicators` | days | hours |
| 41 | `high_yield_credit_stress_proxy_days_since_last_observation` | raw `macro_indicators` | days | hours |
| 42 | `active_addresses_days_since_last_observation` | raw `macro_indicators` | days | hours |
| 43 | `cpi_days_since_release` | `macro_indicator_vintages` | days since `release_date` | hours since `release_date` |
| 44 | `federal_funds_rate_days_since_release` | `macro_indicator_vintages` | days | hours |
| 45 | `gdp_days_since_release` | `macro_indicator_vintages` | days | hours |
| 46 | `m2_money_supply_days_since_release` | `macro_indicator_vintages` | days | hours |
| 47 | `unemployment_days_since_release` | `macro_indicator_vintages` | days | hours |
| 48 | `eng_price_lag_1d` (deprecated) | `btc_prices_hourly.close` | `shift(1)` | `shift(24)` |
| 49 | `eng_price_lag_7d` (deprecated) | `btc_prices_hourly.close` | `shift(7)` | `shift(168)` |
| 50 | `eng_price_lag_30d` (deprecated) | `btc_prices_hourly.close` | `shift(30)` | `shift(720)` |
| 51 | `eng_returns_1d` (deprecated) | `btc_prices_hourly.close` | alias of `btc_log_return_1d` | alias of `btc_log_return_1d` |
| 52 | `eng_returns_7d` (deprecated) | `btc_prices_hourly.close` | alias of `btc_log_return_7d` | alias of `btc_log_return_7d` |
| 53 | `eng_returns_30d` (deprecated) | `btc_prices_hourly.close` | alias of `btc_log_return_30d` | alias of `btc_log_return_30d` |

**Rows 48–53 are deprecated** and outside the 47-column contract; they remain only because migration 009 created them.

**Note on rows 34–47:** the "Daily rule" column records what the *daily* pipeline did (values in **days**); the "Hourly rule" column records what the *hourly* pipeline does (values in **hours**). Column names keep the `_days_` suffix at both resolutions (D8). For rows 43–47, the `release_date` comes from `macro_indicator_vintages`, which is exactly why these are PIT-merged.

## 6. Rename map

### 6.1 FRED → raw → hourly → `features_db`

```
FRED series   →  raw indicator_name    →  hourly column    →  features_db column
──────────       ────────────────────      ──────────────      ───────────────────
FEDFUNDS      →  federal_funds_rate   →  interest_rate    →  federal_funds_rate
M2SL          →  m2_money_supply      →  m2_growth        →  m2_money_supply
DGS10         →  ten_year_treasury    →  treasury_yield   →  ten_year_treasury
CPIAUCSL      →  cpi                  →  cpi              →  cpi
DTWEXBGS      →  dxy                  →  dxy              →  dxy
```

### 6.2 Raw → hourly (used by the `macro_indicators_hourly` writer)

| Raw `macro_indicators.indicator_name` | `macro_indicators_hourly` column |
|---|---|
| `cpi` | `cpi` |
| `federal_funds_rate` | `interest_rate` |
| `m2_money_supply` | `m2_growth` |
| `dxy` | `dxy` |
| `ten_year_treasury` | `treasury_yield` |

### 6.3 Hourly → `features_db`

| Source (hourly) | `features_db` column |
|---|---|
| `btc_prices_hourly.close` | `btc_price` |
| `btc_prices_hourly.volume` | `btc_volume` |
| `btc_prices_hourly.dominance` | `btc_dominance` |
| `macro_indicators_hourly.cpi` | `cpi` (not used — vintages win) |
| `macro_indicators_hourly.interest_rate` | `federal_funds_rate` (not used — vintages win) |
| `macro_indicators_hourly.m2_growth` | `m2_money_supply` (not used — vintages win) |
| `macro_indicators_hourly.treasury_yield` | `ten_year_treasury` |
| `macro_indicators_hourly.dxy` | `dxy` |

**Note:** rows 4–6 in 6.3 are listed for completeness but are **not** the source for `features_db`. The features writer uses vintages for `cpi`, `federal_funds_rate`, and `m2_money_supply`. Listing them here documents the hourly table's own contents without implying they feed `features_db`.

## 7. Migration order and numbering

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
```
008_create_macro_indicator_vintages.sql    (Chat 5, B6)
009_create_features_db.sql                 (Chat 5, B4 — sibling branch)
```

**Notes:**
- There is no "drop `create_all`" migration. That's a code change to `session.py`.
- `004` uses `CREATE TABLE IF NOT EXISTS` for the three raw tables. It was newly proposed in Chat 2 because removing `create_all()` means a fresh DB needs raw tables created by a migration.
- **Migration numbers do not match landing order.** `007_promote_hourly_to_hypertables.sql` was created in Chat 3 for a concern unrelated to `features_db`. It occupies the `007` slot, so `features_db` moves to `009`. The sequence is monotonic by filename only: `007` → `008` → `009`.
- `008` (vintages, B6) and `009` (features_db, B4) are independent at the DDL level. The dependency between them is at the data level: B4's features writer reads vintages to do PIT merges. Filename order (`008` before `009`) reflects the logical dependency, but either migration can land in either order at runtime — the migration runner sorts by filename, so `008` always runs first.
- Migration `009` lives on the sibling branch `feat/data-service-features-db`. It is not part of this branch.

## 8. Open items — adjustable in later chats

- `004` is newly proposed.
- `high_yield_spread_is_missing` semantics: "1 if still NaN after ffill." Left as-is pending a later chat.