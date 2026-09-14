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