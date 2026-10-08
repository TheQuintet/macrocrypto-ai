# Data Service — The Four Paths

## 1. Overview

The data-service has **four paths**, distinguished by trigger and output. All four share the raw tables; they differ in what they read, what they write, and how they're invoked.

| Path | Trigger | Reads | Writes | Status |
|---|---|---|---|---|
| Live | Scheduled, continuous | External providers | Raw tables + hourly tables | Active |
| Manual ML | Manual (CLI) | Raw tables | Daily parquet (`processed/`) | **Frozen** (D13, D21) |
| Backfill | Scheduled + CLI | External providers | Raw tables | Active |
| Option A/B validation | Manual (CLI) | Raw + hourly tables | Hourly parquet (`processed_v2_scripts/`, `processed_v2_builder/`) + `features_db` | **Time-boxed** (D23) |

## 2. Live path (scheduled, continuous)

The live path keeps raw tables and hourly tables fresh. It runs inside the service (scheduler tasks in `app/services/scheduler.py`).

**Components:**
- WebSocket client (`BTCWebSocketClient`) — continuous BTC ticks.
- Periodic collectors — dominance (900s), marketcap (900s), periodic price (60s).
- Daily macro task (01:00 UTC) — FRED series, release dates, active_addresses, gold spot.
- Daily HY proxy task (03:00 UTC) — new `HighYieldCreditStressService`.
- Daily vintages task (03:30 UTC) — new `MacroVintageService`.
- Hourly writers — `:01` `btc_prices_hourly`, `:02` `macro_indicators_hourly`, `:05` `features_db`.

**Idempotency:** all writes use `ON CONFLICT DO NOTHING` or pre-check. Re-running an hour is safe.

## 3. Manual ML path (frozen)

The daily parquet pipeline. Produces `app/data/processed/` for the AI Service's current production training path.

**Status: FROZEN** (D13, D21). No new writes. Kept as a reference baseline and escape hatch.

**Files:** the "four scripts" referenced in D19 (modified versions become Option A).

## 4. Backfill path (scheduled + CLI)

Populates raw tables from external sources.

**New service:** `hourly_backfill_service.py` (D8):
- BTC: Binance klines `interval="1h"`, `source="binance_backfill_hourly"`.
- Gold: Yahoo `interval="1h"` for last ~730 days, `source="yahoo_hourly"`.

`run_backfills.py` is **UNCHANGED** (D8).

**Idempotency:** `save_historical_prices`, `create_many`, and existing repository methods are already idempotent. Re-running a backfill is safe.

**Trigger:** scheduled (weekly for Binance hourly, per §3 of architecture doc) + CLI (ad-hoc recovery).

## 5. Option A / Option B validation path (time-boxed)

Two parallel implementations of the hourly parquet pipeline, so they can be diffed before committing to one.

**Option A (D19):** modified versions of the four existing scripts.
- Output: `processed_v2_scripts/`.
- Time-boxed (D23).

**Option B (D19):** new unified feature builder.
- Output: `processed_v2_builder/`.
- Also writes `features_db` (D22).
- Target for the AI Service (per flag, §8 of design doc).

**Frozen baseline (D21):** `processed/` stays as-is.

**Retirement (D23):** Option A is retired once Option B is trusted.

**Diffing strategy:** column-by-column comparison between the two outputs at matching `ds` values. Price-derived columns must be bit-identical (D12); window-based columns must match within float tolerance after normalizing for the window definition. Any structural difference is a bug in one of the two.

## 6. How the paths interact

```
                    ┌─────────────────────────┐
                    │   Raw tables (frozen)   │
                    │  btc_prices             │
                    │  macro_indicators       │
                    │  btc_dominance          │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
   Live path              Backfill path           Manual ML path
   (scheduled)            (sched + CLI)           (CLI, frozen)
        │                       │                       │
        ▼                       │                       ▼
   Hourly tables ◄──────────────┘                processed/
        │                                          (daily, frozen)
        ▼
   features_db
        │
        ├─► AI Service
        │
        └─► Option A/B validation
              ├─ processed_v2_scripts/ (A)
              └─ processed_v2_builder/ (B)
```

**Shared:** all paths read the raw tables. Nothing writes to raw tables except the live and backfill paths.

**Independent:** hourly tables, `features_db`, and the three parquet dirs are separate. A failure in one doesn't corrupt another.

**Ordering:** live writes raw → hourly writers materialize → features writer writes `features_db`. Backfill can run any time; idempotency makes overlap safe.

## 7. Disaster Recovery and Backup Strategy

### What to back up

1. **Postgres data volume** — the single source of truth. Back up daily.
   - `docker exec macro-postgres pg_dump -U macro macrocrypto > backup_$(date +%Y%m%d).sql`
   - Or use `pg_basebackup` for physical backups.
   - Or use TimescaleDB's `timescaledb-backup` toolkit.

2. **`feature_scaler.pkl`** — the fitted scaler for each output directory. If lost, retraining produces a different scaler, and old model artifacts become incompatible.
   - Back up from: `app/data/processed/`, `app/data/processed_v2_scripts/`, `app/data/processed_v2_builder/`.

3. **AI Service model artifacts** — trained model files (`models/*.pkl`, `models/*.json`). Backed up by the AI Service team.

4. **`.env` files** — configuration.

### What NOT to back up

- Redis cache — regenerable.
- RabbitMQ messages — transient.
- Intermediate CSVs (`ml_btc_*_raw.csv`, etc.) — regenerable from raw tables.
- `macro_raw_with_vintages.csv` — regenerable from FRED (slow but idempotent).

### Backup frequency

- Raw tables (`btc_prices`, `macro_indicators`, `btc_dominance`) — daily.
- Derived tables (`btc_prices_hourly`, `macro_indicators_hourly`, `features_db`) — daily; regenerable from raw so backup is optional.
- Regime tables — daily; regenerable from raw `macro_indicators`.
- `feature_scaler.pkl` — on every retrain.

### Restore procedure

1. Stop the data-service and AI-service.
2. Restore the Postgres volume from the last backup.
3. Restore `feature_scaler.pkl` files from backup.
4. Run: `python -m app.database.migrate` (idempotent).
5. Run: `python -m app.scripts.run_live_path --backfill --all` to fill any gap since the backup.
6. Restart the services.
7. Verify freshness via `/health`.

### Disaster scenarios and responses

| Scenario | Response |
|---|---|
| Postgres volume lost | Restore from last daily backup + gap backfill |
| Migration failed mid-run | Fix migration, re-run (idempotent) |
| Backfill partially failed | Re-run backfill (idempotent) |
| `features_db` corrupt | Drop table, re-run migrations, backfill |
| Raw table corrupt | Restore from backup + gap backfill |
| Scaler lost | Retrain; old models become incompatible |
| AI Service artifacts lost | AI Service team's concern |

### Testing the recovery

- Every 3 months: restore the latest backup to a test database, verify row counts, run the gap-fill backfill.
- Annually: full disaster recovery drill.

### What is NOT covered

- Cross-region replication.
- Point-in-time recovery (PITR) — Postgres supports it via WAL archiving, but it's not configured today.
- Automated failover.

These are the responsibility of the deployment environment. The data-service assumes the DB is highly available; if it's not, the recovery strategy above is the fallback.

## 8. Open items — adjustable in later chats

- The exact weekly schedule for the Binance hourly backfill (weekly is proposed, not locked).
- The `--backfill --all` CLI shape in the restore procedure is illustrative — actual CLI flags finalized in a later chat.