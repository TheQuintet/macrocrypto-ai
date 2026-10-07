# Data Service — Hourly Runbook

Operational procedures for the hourly data pipeline
(`btc_prices_hourly`, `macro_indicators_hourly`) introduced in
Chat 3 and monitored in Chat 4.

**Audience:** whoever is on call when an alert fires, or whoever
is looking at the pipeline after a break.

**Assumptions:** you have shell access to the data-service host,
the database is reachable at the configured `DATABASE_URL`, and
you're in the repo root
(`~/GitHub Repos/macrocrypto-ai`).

---

## 1. TL;DR

| Symptom | First command |
|---|---|
| "Are there gaps?" | `python -m app.scripts.verify_hourly_tables --table all --days 7` |
| "Is the pipeline alive?" | `curl -s http://localhost:8001/health \| jq .hourly_freshness` |
| "Fix gaps I can fix" | `python -m app.scripts.verify_hourly_tables --table all --days 7 --repair` |
| "Get fresh raw data" | `python -m app.scripts.run_hourly_backfills --btc --days 7` (and/or `--gold`) |
| "Nothing is running" | check container status, then restart the data-service |

The rest of this runbook expands on each.

---

## 2. How to check for gaps

### 2.1 The short version

```bash
cd services/data-service
python -m app.scripts.verify_hourly_tables --table all --days 7
```

Exit codes:

| Code | Meaning |
|---|---|
| 0 | No gaps. Nothing to do. |
| 1 | Gaps found. Read the report; decide whether to repair. |
| 2 | Bad arguments. Fix the command. |
| 3 | Database or runtime error. Investigate before repairing. |

Sample output (gaps exist):

```
=== btc_prices_hourly ===
  range:   2026-01-08T14:00:00+00:00 -> 2026-01-15T14:00:00+00:00
  expected hours: 168
  actual hours:   165
  missing hours:  3 (1.79%)
    MATERIALIZATION_GAP: 2
    RAW_DATA_GAP:        1
  first missing hours:
    2026-01-10T03:00:00+00:00  MATERIALIZATION_GAP
    2026-01-10T04:00:00+00:00  MATERIALIZATION_GAP
    2026-01-12T09:00:00+00:00  RAW_DATA_GAP
  suggested commands:
    # BTC raw ticks are missing for some hours. Fetch hourly candles first:
    python -m app.scripts.run_hourly_backfills --btc --start 2026-01-08 --end 2026-01-15
    # Then re-materialize (--repair covers MATERIALIZATION_GAP hours only):
    python -m app.scripts.verify_hourly_tables --table btc --start 2026-01-08 --end 2026-01-15 --repair
```

### 2.2 The two kinds of gap

The verify command classifies every missing hour:

- **MATERIALIZATION_GAP** — raw data exists for that hour, but
  the hourly table has no row. Re-running the hourly writer on
  that hour will produce a row. The fix is local and fast.
- **RAW_DATA_GAP** — raw data does not exist either. Re-running
  the hourly writer will not help; the raw data must be fetched
  first.

The classification rule is asymmetric by design, matching the
two writers in `scheduler.py`:

- **BTC** (`btc_prices_hourly`): raw data means "at least one
  `btc_prices` tick in `[hour, hour+1)`". If no tick exists,
  the writer skips the hour — so no tick means RAW_DATA_GAP.
- **Macro** (`macro_indicators_hourly`): raw data means "at
  least one `macro_indicators` observation with `time <= hour`".
  If no prior observation exists, the row would be all-NULL —
  so no prior observation means RAW_DATA_GAP.

### 2.3 Which table(s) to scan

| Goal | Command |
|---|---|
| BTC only | `--table btc` |
| Macro only | `--table macro` |
| Both | `--table all` |

### 2.4 Which window to scan

| Window | Command |
|---|---|
| Last 24h | `--days 1` |
| Last 7 days (default for the background scan) | `--days 7` |
| Last 30 days (CLI default) | `--days 30` |
| Explicit range | `--start 2026-01-01 --end 2026-01-15` |

`--start` and `--end` are ISO-8601. If the input carries no
timezone, UTC is assumed. `--end` is exclusive.

---

## 3. What to do if MATERIALIZATION_GAP

These are the easy ones: the raw data is present; only the
hourly materialization is behind.

### 3.1 Repair in place

```bash
cd services/data-service
python -m app.scripts.verify_hourly_tables --table btc --days 7 --repair
```

`--repair` re-runs Chat 3's `write_hour` primitive once per
MATERIALIZATION_GAP hour. It does **not** touch RAW_DATA_GAP
hours. It is idempotent: re-running is always safe.

The command still exits **1** even if the repair fully
succeeded, because gaps *were* found. A repair result line is
printed after the report:

```
  repair: attempted=2 succeeded=2 skipped=0 raw_gaps=1 errors=0
```

If `errors > 0`, the command exits 3 and the affected hours'
failure reasons are in the logs.

### 3.2 Verify the repair

```bash
python -m app.scripts.verify_hourly_tables --table btc --days 7
```

Should now exit 0 for the repaired hours. Remaining gaps would
be RAW_DATA_GAPs (see §4).

### 3.3 Why these happened

Usually one of:

- The scheduler was paused or crashed briefly.
- The service restarted and the periodic task missed a minute.
- A manual `DELETE` was run without a re-materialize.

If MATERIALIZATION_GAPs appear repeatedly for the same table,
check the writer task's logs — see §5.

---

## 4. What to do if RAW_DATA_GAP

These require an external fetch first, then a re-materialize.

### 4.1 BTC RAW_DATA_GAP

Fetch hourly BTC candles from Binance:

```bash
cd services/data-service
python -m app.scripts.run_hourly_backfills --btc --days 30
```

Or for an explicit range:

```bash
python -m app.scripts.run_hourly_backfills --btc \
    --start 2026-01-01 --end 2026-01-15
```

Then re-materialize:

```bash
python -m app.scripts.verify_hourly_tables --table btc --days 30 --repair
```

**Range cap:** Binance hourly klines go back to 2017-08-17. If
your `--start` is earlier, the service caps it automatically
and logs the cap. Hours before that date are permanently
un-backfillable via Binance.

**Skip-if-ticks-exist:** if the raw table already has tick-level
data (WebSocket or REST ticks) for a given hour, the backfill
**skips** the hourly candle for that hour. Ticks are strictly
more informative, and writing both would double-count volume in
`btc_prices_hourly.volume`. This is by design — see
`hourly_backfill_service.py`.

### 4.2 Macro RAW_DATA_GAP

Macro gaps mean FRED data is missing. Fetch it with Phase A's
daily backfill (unchanged):

```bash
cd services/data-service
python -m app.scripts.run_backfills
```

Then re-materialize:

```bash
python -m app.scripts.verify_hourly_tables --table macro --days 30 --repair
```

**Important:** the macro hourly table holds FRED series
(`cpi`, `interest_rate` ← `federal_funds_rate`, `m2_growth` ←
`m2_money_supply`, `dxy`, `treasury_yield` ←
`ten_year_treasury`). It does **not** hold gold. Gold is a raw
indicator that flows into `features_db` directly, not into
`macro_indicators_hourly`. Do not run
`run_hourly_backfills --gold` to fix a macro gap.

**Pre-FRED-history gaps:** if the RAW_DATA_GAP precedes the
earliest available FRED observation for those indicators, there
is nothing to backfill. The row would be all-NULL and the
correct response is to accept the gap.

### 4.3 Gold RAW_DATA_GAP (does not exist as such)

There is no gold RAW_DATA_GAP class for the hourly tables,
because gold does not feed `macro_indicators_hourly`. Gold
feeds `features_db`, which is out of scope for Chat 4. If you
suspect gold data is missing, verify the daily macro job is
running — see §5.

### 4.4 Verify the repair

```bash
python -m app.scripts.verify_hourly_tables --table all --days 30
```

Exit 0 means the gap is closed. Exit 1 with the same gaps
means the raw fetch didn't produce rows in the range you
asked for — re-read §4.1/§4.2 for the range caps, and check
the fetch command's own log output for how many rows it
persisted.

---

## 5. What to do if the scheduler is silent

Symptom: `/health` reports `hourly_freshness.status == "stale"`
for one or both tables for more than a few hours.

### 5.1 Check the pipeline

```bash
curl -s http://localhost:8001/health | jq .hourly_freshness
```

Expected output for a healthy pipeline:

```json
{
  "btc_prices_hourly": {
    "latest_hour": "2026-01-15T14:00:00+00:00",
    "hours_behind": 1,
    "status": "fresh"
  },
  "macro_indicators_hourly": {
    "latest_hour": "2026-01-15T14:00:00+00:00",
    "hours_behind": 1,
    "status": "fresh"
  }
}
```

Interpretation:

| `status` | Meaning |
|---|---|
| `fresh` | Newest row is ≤ 3 hours behind. Normal. |
| `stale` | Newest row is > 3 hours behind. Something is wrong. |
| `unknown` | Table is empty or unreachable. Check the DB. |

### 5.2 Check the DB directly

```bash
docker exec -it macro-postgres psql -U macro -d macrocrypto -c \
  "SELECT max(time) FROM btc_prices_hourly;"
docker exec -it macro-postgres psql -U macro -c \
  "SELECT max(time) FROM macro_indicators_hourly;"
```

If the `max(time)` is behind, the writers aren't running.

### 5.3 Check the writers

The hourly writers run as scheduler tasks inside the
data-service process:

- `periodic_hourly_btc_prices` — every hour at :01 UTC
- `periodic_hourly_macro_indicators` — every hour at :02 UTC

Look for lines like these in the data-service logs:

```
⏱️  Hourly BTC prices scheduler started
⏱️  Hourly BTC prices scheduler woke up
⏱️  Wrote btc_prices_hourly row for 2026-01-15T13:00:00+00:00
```

If you don't see the "scheduler started" line at startup, the
task never launched. Restart the service:

```bash
docker restart macro-data-service
# or, if running locally:
# kill the running uvicorn and re-run `python -m app.main`
```

### 5.4 Check for exceptions

If the "scheduler started" line is present but "woke up" is
never logged, the task is stuck in `wait_until_next_hour`.
Check system time on the host — a wrong clock can cause the
next-run computation to sleep for a very long time.

If "woke up" appears but no "Wrote ..." follows, the writer
raised. Grep the logs for:

```
🔥 Hourly BTC prices scheduler failed
🔥 Hourly macro indicators scheduler failed
```

These lines will be followed by a traceback. Common causes:
DB connection lost, table missing (migration not applied), or
unexpected raw data shape.

### 5.5 After restart

Confirm freshness within 10 minutes:

```bash
curl -s http://localhost:8001/health | jq .hourly_freshness
```

Then run gap detection (§2) to see what the outage missed.

---

## 6. What to do if Binance rate-limits

Symptom: `run_hourly_backfills --btc` logs lines like:

```
[HOURLY-BACKFILL] Binance rate limited at 2026-01-15T... (attempt 2/4); sleeping 4.0s
```

The service backs off exponentially up to 4 retries (waits of
2s, 4s, 8s, 16s) and then raises if it still can't succeed.

### 6.1 If the retries succeed

Nothing to do. The log line is informational. The backfill
completes normally.

### 6.2 If the retries exhaust

Symptom: the command exits non-zero with a traceback ending in
something like `429 Too Many Requests`.

What to do:

1. **Wait.** Binance rate limits reset within a minute (or an
   hour for the harsher 418 IP ban). Check
   https://www.binance.com/en/support/faq/ for the current
   policy.
2. **Re-run the command.** It is idempotent — already-fetched
   hours are skipped on the second run.
3. **Narrow the range.** If you're fetching years of history,
   do it in smaller `--days` chunks.
4. **Check other processes.** If multiple hosts are hitting
   Binance from the same IP, they compete for the same bucket.
   Coordinate or distribute.

### 6.3 Preventing it

- Don't run `run_hourly_backfills` more often than needed.
  It's a recovery tool, not a heartbeat.
- Prefer `--days N` over huge `--start/--end` ranges.
- The default 30-day window is 720 candles — well within
  Binance's single-IP budget.

---

## 7. How to safely re-run any backfill

**Every backfill in the hourly pipeline is idempotent.** Re-running
is always safe, and the second run usually shows `0` rows
written.

The idempotency guarantees:

| Command | How it's idempotent |
|---|---|
| `run_hourly_backfills --btc` | Pre-checks existing `btc_prices.time` values; skips hours with ticks; `save_historical_prices` dedupes by `time`. |
| `run_hourly_backfills --gold` | `MacroIndicatorRepository.create_many` uses `ON CONFLICT (time, indicator_name) DO NOTHING`. |
| `verify_hourly_tables --repair` | `write_hour` uses `ON CONFLICT (time) DO NOTHING` in the hourly tables. |
| `run_live_path --btc-hourly-backfill` | Same `write_hour` primitive; same guarantee. |
| `run_live_path --macro-hourly-backfill` | Same. |

If you're unsure whether a previous run completed, just run it
again. It won't duplicate anything.

**What is *not* idempotent:** raw-table schema changes,
migrations, and manual `DELETE` statements. If you delete a
row, the next backfill will write it again — that's fine — but
be aware you're changing history.

---

## 8. How to validate a backfill

After any backfill, verify that the data landed and the gap is
closed.

### 8.1 Check the row count

```bash
docker exec -it macro-postgres psql -U macro -d macrocrypto -c \
  "SELECT source, count(*) FROM btc_prices
   WHERE time >= now() - interval '30 days'
   GROUP BY source;"
```

Expected: `binance_backfill_hourly` rows for the hours you
asked for, plus any live tick rows (source `binance` or
similar) from the WebSocket/REST collectors.

### 8.2 Re-run gap detection

```bash
python -m app.scripts.verify_hourly_tables --table btc --days 30
```

Exit 0 means the gap is closed and no new gaps appeared.

### 8.3 Spot-check a specific hour

```bash
docker exec -it macro-postgres psql -U macro -d macrocrypto -c \
  "SELECT time, close, volume FROM btc_prices_hourly
   WHERE time = '2026-01-15T12:00:00+00:00';"
```

If the row exists, has a plausible `close`, and a non-zero
`volume` (when ticks existed), the hour is healthy.

### 8.4 Check /health

```bash
curl -s http://localhost:8001/health | jq .hourly_freshness
```

Should show `fresh` for both tables.

---

## 9. Background gap scan

The data-service runs a read-only gap scan in the background:

- **When:** once at startup, then every
  `HOURLY_GAP_SCAN_INTERVAL_HOURS` (default 6h).
- **Window:** the last `HOURLY_GAP_SCAN_LOOKBACK_HOURS`
  (default 168h = 7 days).
- **What:** both `btc_prices_hourly` and
  `macro_indicators_hourly`.
- **Does not:** repair anything. Never fetches from external
  providers. Never writes to any table.

When gaps exist, it logs WARNINGs:

```
🔍 Hourly gap scan (periodic scan): btc_prices_hourly has 3 missing hour(s)
   over the last 168h (MATERIALIZATION_GAP=2, RAW_DATA_GAP=1).
   Run `python -m app.scripts.verify_hourly_tables --table btc --days 7` for details,
   or --repair to fix MATERIALIZATION_GAP hours.
🔍   2026-01-10T03:00:00+00:00  MATERIALIZATION_GAP
🔍   2026-01-10T04:00:00+00:00  MATERIALIZATION_GAP
🔍   2026-01-12T09:00:00+00:00  RAW_DATA_GAP
```

To disable the background scan entirely:

```
HOURLY_GAP_SCAN_ENABLED=false
```

in the environment. The CLI path (`verify_hourly_tables.py`) is
unaffected by this flag — you can always run it manually.

To tune the interval or lookback:

```
HOURLY_GAP_SCAN_INTERVAL_HOURS=3    # more frequent
HOURLY_GAP_SCAN_LOOKBACK_HOURS=336  # 14 days
```

`INTERVAL_HOURS` is a float; `0.5` means "every 30 minutes,"
which is useful for debugging but not recommended for
production.

---

## 10. Quick reference — all hourly commands

| Task | Command |
|---|---|
| Scan both tables, last 7 days | `python -m app.scripts.verify_hourly_tables --table all --days 7` |
| Scan BTC only, last 30 days | `python -m app.scripts.verify_hourly_tables --table btc --days 30` |
| Scan an explicit range | `python -m app.scripts.verify_hourly_tables --table all --start 2026-01-01 --end 2026-01-15` |
| Repair MATERIALIZATION_GAPs in place | `python -m app.scripts.verify_hourly_tables --table all --days 7 --repair` |
| Fetch BTC raw hourly (30d default) | `python -m app.scripts.run_hourly_backfills --btc` |
| Fetch BTC raw hourly (explicit range) | `python -m app.scripts.run_hourly_backfills --btc --start 2026-01-01 --end 2026-01-15` |
| Fetch gold raw hourly | `python -m app.scripts.run_hourly_backfills --gold` |
| Fetch both raw sources | `python -m app.scripts.run_hourly_backfills --all` |
| Fetch daily FRED (Phase A) | `python -m app.scripts.run_backfills` |
| Write BTC hourly for the last completed hour | `python -m app.scripts.run_live_path --btc-hourly` |
| Write macro hourly for the last completed hour | `python -m app.scripts.run_live_path --macro-hourly` |
| Verify via run_live_path (equivalent) | `python -m app.scripts.run_live_path --verify-hourly --table btc --days 7` |
| Health check | `curl -s http://localhost:8001/health \| jq` |

---

## 11. Known limitations

- **Binance hourly history starts 2017-08-17.** Earlier gaps
  cannot be filled from Binance hourly klines.
- **Yahoo hourly history is ~730 days.** Earlier gaps cannot
  be filled from Yahoo hourly.
- **Pre-FRED-history macro gaps are permanent.** If a macro
  raw observation never existed for an hour, there is nothing
  to backfill.
- **No auto-repair.** `--repair` is opt-in. The background
  scan logs warnings only. This is deliberate: external
  fetches and materialization are human-triggered decisions.
- **No cross-region replication.** Backups are the operator's
  responsibility. See the four-paths doc §7.