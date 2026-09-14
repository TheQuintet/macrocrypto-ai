# AI Service Migrations

SQL migrations for tables owned by the AI Service.

## Ownership Rule

Only tables **owned by the AI Service** are defined here. Per the
platform's shared-database, per-service-ownership model:

- **AI Service owns and migrates:**
  `btc_predictions`, `schema_migrations`, and (in later branches)
  `model_performance`, `prediction_accuracy`, `btc_macro_correlation`,
  `historical_event_impacts`, `export_history`.

- **AI Service reads but does NOT own (and does NOT migrate):**
  `btc_prices`, `macro_indicators` — owned by the Data Ingestion Service.

## File Naming

```
NNN_<description>.sql
```

- `NNN` — zero-padded sequence number (001, 002, ...)
- Applied in **lexicographic order** by the migration runner

## Running Migrations

```bash
# From services/ai-service/
python -m app.database.migrations_runner
```

The runner tracks applied migrations in the `schema_migrations` table
and is idempotent — already-applied migrations are skipped.

## Guidelines

1. **Only create tables the AI Service owns.** No source tables.
2. **One logical change per file.** Easier to review, easier to revert.
3. **Idempotent DDL where possible.** Use `IF NOT EXISTS`.
4. **Never edit an applied migration.** Add a new one instead.
5. **Test locally before committing.** The migration runner is safe
   to re-run — idempotency is enforced by `schema_migrations`.

## Unified Predictions Table

The `btc_predictions` table (created by `002_create_btc_predictions.sql`)
is a **single unified table** that stores predictions for **all horizons**
and **all models**, distinguished by the `horizon` and `model_name`
columns.

### Supported Horizons

| Horizon | Written by | Description |
|---------|-----------|-------------|
| `24h`   | T1.2 hourly job (`hourly_prediction_job`) | 24 hourly forecast points |
| `7d`    | T2.2 daily job (`daily_7d_prediction_job`) | 168 hourly forecast points (7 days) |

The CHECK constraint `btc_predictions_horizon_valid` enforces
`horizon IN ('24h', '7d')`, so any future horizon must be added via
a new migration (not by widening the constraint in place).

### Supported Models

| Model | Status |
|-------|--------|
| `prophet` | ✅ Active |
| `xgboost` | 🔜 M6 |
| `lightgbm` | 🔜 M6 |

### Querying

To read the latest 24h predictions for Prophet at 85% confidence:

```sql
SELECT *
FROM btc_predictions
WHERE horizon = '24h'
  AND model_name = 'prophet'
  AND confidence = 0.85
  AND prediction_time = (
    SELECT MAX(prediction_time)
    FROM btc_predictions
    WHERE horizon = '24h'
      AND model_name = 'prophet'
      AND confidence = 0.85
  )
ORDER BY time ASC;
```

The `idx_btc_predictions_horizon_model_time` index covers this pattern
for both `24h` and `7d`.

### Why Unified (Not Split Tables)

An earlier ticket (T1.3) considered separate tables
(`btc_predictions_24h`, `btc_predictions_7d`). The unified approach
was chosen because:

- **One hypertable, one set of indexes, one migration** — cheaper ops.
- **Cross-horizon queries are trivial** (e.g., "compare 24h vs 7d
  consensus"). With split tables, every comparison becomes a UNION.
- **Adding a new horizon doesn't require a migration** — just widen the
  CHECK constraint if needed (and that's a rare event).
- **The M6 API naturally maps to `?horizon=24h` or `?horizon=7d`** —
  one query parameter, one table.