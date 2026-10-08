"""SQLAlchemy Core table definitions for the AI Service.

This module defines the tables the AI Service reads from and writes
to. It uses SQLAlchemy Core (not ORM) because:
    - TimescaleDB hypertables are simpler to express as Core Tables
    - Queries are mostly analytical (SELECT / INSERT), not object graphs
    - Raw SQL is used for Timescale-specific DDL (create_hypertable)
      — those live in later branches (T1.3, T3.2, T5.1)

Tables:
    - btc_prices:              Source — hourly BTC OHLCV + market metrics
                               (written by Data Ingestion Service)
    - macro_indicators:        Source — macro features (CPI, rates, etc.)
                               (written by Data Ingestion Service)
    - features_db:             Source — canonical 47-column ML dataset
                               (written by Data Service, read by AI Service)
    - btc_predictions:         Target — hourly predictions from the AI Service
                               (unified table; 24h and 7d horizons)
    - prediction_performance:  Target — per-point evaluation metrics (T5.1)
    - threshold_breaches:      Target — threshold breach history (T5.4)
    - model_performance:       Target — per-model aggregate metrics (M7)
    - btc_macro_correlation:   Target — BTC-vs-macro correlation metrics (A1.1)
    - export_history:          Target — export request history (A2.1)
    - historical_event_impacts: Target — historical event impact data (A5.1)
    - model_champions:         State — the active champion per (horizon, regime)
    - champion_candidates:     State — daily top candidate per (horizon, regime)

CLI isolation (_cli variants):
    Eight of the target tables have `_cli` mirror variants that the
    manual CLI (app.cli.pipeline) writes to when CLI_MODE=true.
    This keeps CLI runs sandboxed away from production tables.

        btc_predictions         <-> btc_predictions_cli
        prediction_performance  <-> prediction_performance_cli
        threshold_breaches      <-> threshold_breaches_cli
        model_performance       <-> model_performance_cli
        btc_macro_correlation   <-> btc_macro_correlation_cli
        historical_event_impacts<-> historical_event_impacts_cli
        model_champions         <-> model_champions_cli
        champion_candidates     <-> champion_candidates_cli

    The `_cli` tables are structurally identical (same columns,
    constraints, indexes) via SQLAlchemy's to_metadata() helper.
    They are created by migrations, and populated only by the CLI.

    Note: SQLAlchemy's to_metadata() cannot express the partial
    unique index on model_champions (it uses COALESCE), so the DB
    index is created by the migration only. The Core Table
    definition is used for queries and inserts.

Naming:
    Table names are pulled from Settings so they can be overridden
    via env vars without touching code. See app/config.py.
"""

import logging

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# METADATA
# ============================================================
# A single shared MetaData instance anchors all Core Table objects.
# Later branches can attach Alembic to this metadata for migrations.
metadata = MetaData()


# ============================================================
# SOURCE TABLE: btc_prices
# ============================================================
# Hourly BTC OHLCV + market metrics. Written by the Data Ingestion
# Service. The AI Service reads the last N hours to build the
# training / prediction frame.
btc_prices = Table(
    settings.db_table_btc_prices,
    metadata,
    Column("time", DateTime(timezone=True), primary_key=True),
    # Target price (Prophet's `y`)
    Column("close", Float, nullable=False),
    # BTC market features (the 5 BTC regressors)
    Column("volume", Float, nullable=True),
    Column("volatility", Float, nullable=True),
    Column("dominance", Float, nullable=True),
    Column("active_addresses", Float, nullable=True),
    Column("price_lag_7d", Float, nullable=True),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# SOURCE TABLE: macro_indicators
# ============================================================
# Macro features, forward-filled to hourly frequency. Written by
# the Data Ingestion Service.
macro_indicators = Table(
    settings.db_table_macro_indicators,
    metadata,
    Column("time", DateTime(timezone=True), primary_key=True),
    # The 5 macro regressors
    Column("cpi", Float, nullable=True),
    Column("interest_rate", Float, nullable=True),
    Column("m2_growth", Float, nullable=True),
    Column("dxy", Float, nullable=True),
    Column("treasury_yield", Float, nullable=True),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# SOURCE TABLE: features_db
# ============================================================
# The canonical 47-column ML dataset. Written by the Data Service
# (in the data-service repo). The AI Service reads from it when
# feature_source="features_db".
#
# Column contract mirrors the parquet files (train_scaled.parquet
# and siblings) plus the two renames noted below:
#
#   - observation_date  ->  ds
#   - target_next_price ->  y
#
# The table is defined here as a Core Table so the AI Service can
# query it. The table ITSELF is created by the data-service's
# migrations (migration owner: data-service). The AI Service never
# writes to it.
#
# The definition below is intentionally permissive: most feature
# columns are nullable because not every row is expected to have
# every feature (e.g. gdp updates quarterly). Nullability matches
# the parquet semantics.
#
# Columns are grouped by role for readability:
#   - ds, y              — timestamp + target
#   - raw market          — 4 columns
#   - macro & external    — 13 columns
#   - technical           — 10 columns
#   - data-quality flags  — 4 columns
#   - recency trackers    — 14 columns
#
# The data-service table also carries 6 deprecated eng_* columns.
# They are deliberately not mapped here: the frozen 47-column
# parquet is the feature contract.
features_db = Table(
    settings.features_db_table,
    metadata,
    # ---- Timestamp + target ----
    Column("ds", DateTime(timezone=True), primary_key=True),
    Column("y", Float, nullable=False),
    # ---- Raw market & on-chain ----
    Column("btc_price", Float, nullable=True),
    Column("btc_volume", Float, nullable=True),
    Column("btc_dominance", Float, nullable=True),
    Column("active_addresses", Float, nullable=True),
    # ---- Macro & external assets ----
    Column("gold_spot", Float, nullable=True),
    Column("dxy", Float, nullable=True),
    Column("ten_year_treasury", Float, nullable=True),
    Column("vix", Float, nullable=True),
    Column("high_yield_spread", Float, nullable=True),
    Column("nasdaq_composite", Float, nullable=True),
    Column("equity_corr", Float, nullable=True),
    Column("high_yield_credit_stress_proxy", Float, nullable=True),
    Column("cpi", Float, nullable=True),
    Column("federal_funds_rate", Float, nullable=True),
    Column("gdp", Float, nullable=True),
    Column("m2_money_supply", Float, nullable=True),
    Column("unemployment", Float, nullable=True),
    # ---- Technical indicators & ratios ----
    Column("btc_log_return_1d", Float, nullable=True),
    Column("btc_log_return_7d", Float, nullable=True),
    Column("btc_log_return_30d", Float, nullable=True),
    Column("btc_sma_7", Float, nullable=True),
    Column("btc_sma_30", Float, nullable=True),
    Column("btc_sma_90", Float, nullable=True),
    Column("btc_volatility_7d", Float, nullable=True),
    Column("btc_volatility_30d", Float, nullable=True),
    Column("btc_gold_ratio", Float, nullable=True),
    Column("btc_nasdaq_ratio", Float, nullable=True),
    # ---- Data-quality flags ----
    Column("high_yield_spread_is_missing", Integer, nullable=True),
    Column("active_addresses_is_imputed", Integer, nullable=True),
    Column("unemployment_is_imputed", Integer, nullable=True),
    Column("warmup_complete", Integer, nullable=True),
    # ---- Observation recency trackers ----
    Column("btc_dominance_days_since_last_observation", Integer, nullable=True),
    Column("gold_spot_days_since_last_observation", Integer, nullable=True),
    Column("dxy_days_since_last_observation", Integer, nullable=True),
    Column("ten_year_treasury_days_since_last_observation", Integer, nullable=True),
    Column("vix_days_since_last_observation", Integer, nullable=True),
    Column("nasdaq_composite_days_since_last_observation", Integer, nullable=True),
    Column("equity_corr_days_since_last_observation", Integer, nullable=True),
    Column("high_yield_credit_stress_proxy_days_since_last_observation", Integer, nullable=True),
    Column("active_addresses_days_since_last_observation", Integer, nullable=True),
    Column("cpi_days_since_release", Integer, nullable=True),
    Column("federal_funds_rate_days_since_release", Integer, nullable=True),
    Column("gdp_days_since_release", Integer, nullable=True),
    Column("m2_money_supply_days_since_release", Integer, nullable=True),
    Column("unemployment_days_since_release", Integer, nullable=True),
)


# ============================================================
# TARGET TABLE: btc_predictions
# ============================================================
# Unified predictions table. Filtered by `horizon` ('24h' or '7d')
# and `model_name` ('prophet', 'xgboost', 'lightgbm', ...).
#
# The `id` column was added in migration 003 as a surrogate key
# for foreign-key references from prediction_performance.
# BIGSERIAL in the migration implies NOT NULL + a sequence default,
# so the DB always populates it — nullable=False matches reality.
btc_predictions = Table(
    settings.db_table_predictions,
    metadata,
    # Surrogate identifier (added in migration 003)
    Column("id", BigInteger, nullable=False, unique=True),
    # Time the prediction is for (the forecast timestamp)
    Column("time", DateTime(timezone=True), primary_key=True),
    # Metadata
    Column("prediction_time", DateTime(timezone=True), primary_key=True),
    Column("horizon", String(8), primary_key=True),  # '24h' or '7d'
    Column("model_name", String(64), primary_key=True),  # 'prophet', etc.
    Column("confidence", Float, primary_key=True),  # 0.70, 0.85, 0.95
    # Values
    Column("predicted_price", Float, nullable=False),
    Column("lower_bound", Float, nullable=False),
    Column("upper_bound", Float, nullable=False),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# TARGET TABLE: prediction_performance
# ============================================================
# Per-evaluated-point metrics for stored predictions (T5.1).
# One row per (prediction, actual price observed at forecast time).
# Rolling metrics (mae, rmse, mape) are nullable and populated by
# T5.2's backtesting pipeline. `market_condition` is populated by
# T5.3's classification logic.
#
# `prediction_id` was made nullable in migration 005 so backtest
# rows (which have no corresponding btc_predictions row) can be
# stored alongside production evaluation rows.
prediction_performance = Table(
    "prediction_performance",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # FK to btc_predictions.id (NULL for backtest rows)
    Column("prediction_id", BigInteger, nullable=True),
    # Denormalized from btc_predictions for query performance
    Column("horizon", String(8), nullable=False),
    Column("model_name", String(64), nullable=False),
    Column("model_version", String(64), nullable=False),
    # Evaluation
    Column("forecast_date", DateTime(timezone=True), nullable=False),
    Column("predicted_price", Float, nullable=False),
    Column("actual_price", Float, nullable=False),
    # Rolling metrics (nullable — populated by T5.2)
    Column("mae", Float, nullable=True),
    Column("rmse", Float, nullable=True),
    Column("mape", Float, nullable=True),
    # Classification (nullable — populated by T5.3)
    Column("market_condition", String(16), nullable=True),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# TARGET TABLE: threshold_breaches
# ============================================================
# One row per (horizon, model, metric) that breached its configured
# threshold during a daily accuracy check (T5.4). Feeds T5.6's
# streak-based escalation logic.
threshold_breaches = Table(
    "threshold_breaches",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # When the daily check ran
    Column(
        "detected_at",
        DateTime(timezone=True),
        server_default=text("now()"),
    ),
    # Which model-horizon the breach belongs to
    Column("horizon", String(8), nullable=False),
    Column("model_name", String(64), nullable=False),
    # Which metric breached
    Column("metric", String(32), nullable=False),
    Column("metric_unit", String(16), nullable=False),
    # The actual value and the configured threshold
    Column("value", Float, nullable=False),
    Column("threshold", Float, nullable=False),
    # Direction of the breach:
    #   'above' — MAE, RMSE, MAPE (higher is worse)
    #   'below' — directional accuracy (lower is worse)
    Column("breach_direction", String(8), nullable=False),
    # Number of consecutive days this metric has been breaching
    Column(
        "consecutive_days",
        Integer,
        nullable=False,
        server_default=text("1"),
    ),
    # Optional context
    Column("model_version", String(64), nullable=True),
    Column("notes", Text, nullable=True),
)


# ============================================================
# TARGET TABLE: model_performance
# ============================================================
# One row per (model_name, horizon, calculated_at). Stores
# aggregate performance metrics for a model-horizon pair computed
# at a point in time. Unlike prediction_performance (one row per
# evaluated point), this table stores one row per aggregation run,
# making long-term trend queries cheap.
#
# Populated by a dedicated job (a later branch); M8 reads from it
# for the multi-model performance API.
model_performance = Table(
    "model_performance",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # Which model-horizon the aggregate is for
    Column("model_name", String(64), nullable=False),
    Column("horizon", String(8), nullable=False),
    # Aggregate metrics — all nullable because not every run
    # produces every metric (e.g. directional_accuracy requires
    # direction ground truth, which is not always available)
    Column("mae", Float, nullable=True),
    Column("rmse", Float, nullable=True),
    Column("mape", Float, nullable=True),
    Column("directional_accuracy", Float, nullable=True),
    # How many evaluated points contributed to the aggregate
    Column("sample_size", Integer, nullable=False),
    # When the aggregation was computed (the timestamp of the run)
    Column("calculated_at", DateTime(timezone=True), nullable=False),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# TARGET TABLE: btc_macro_correlation
# ============================================================
# One row per (indicator_name, window_days, calculated_at).
# Stores the Pearson correlation between BTC price and each
# macroeconomic indicator over a rolling window.
#
# Populated by A1.2's calculation logic; A1.3 derives the
# strength and direction labels, A1.4 computes the p-value and
# significance, and A1.6 exposes it via an API endpoint.
#
# The composite primary key is (indicator_name, window_days,
# calculated_at) — a natural key. Unlike prediction_performance
# and model_performance, there is no surrogate id because the
# three business columns uniquely identify a row.
btc_macro_correlation = Table(
    "btc_macro_correlation",
    metadata,
    # Business key: which macro indicator
    #   'inflation' — CPI-based
    #   'rates'     — interest rate
    #   'gdp'       — gross domestic product growth
    #   'unemployment' — unemployment rate
    Column("indicator_name", String(32), primary_key=True),
    # Which rolling window (30 / 90 / 365 days)
    Column("window_days", Integer, primary_key=True),
    # When the calculation was computed (the timestamp of the run)
    Column("calculated_at", DateTime(timezone=True), primary_key=True),
    # Pearson correlation coefficient in [-1, 1]
    Column("correlation_coefficient", Float, nullable=False),
    # Derived label: 'strong', 'medium', or 'weak' (A1.3)
    Column("strength", String(16), nullable=False),
    # Derived label: 'positive' or 'negative' (A1.3)
    Column("direction", String(16), nullable=False),
    # Statistical significance (A1.4). Nullable so that A1.2 can
    # write rows before significance is computed.
    Column("p_value", Float, nullable=True),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# TARGET TABLE: export_history
# ============================================================
# One row per export request an analyst or system process has
# made. Records what was requested (export_type, data_types,
# timeframe) and the outcome (status, file_name, file_size,
# downloaded_at).
#
# Populated by the export pipeline (A2.2 through A2.6); read by
# the export history API (a later branch). Rows are created when
# the request arrives (status='pending'), updated when the file
# is generated (status='completed', file_name + file_size set),
# and updated again when the caller downloads the file
# (downloaded_at set).
#
# Design notes:
#   - `user_id` is a VARCHAR(64) opaque identifier, NOT a foreign
#     key. The auth system lives in a different service; there is
#     no `users` table in this database to reference. It is
#     nullable because system-triggered exports (scheduled jobs,
#     tests, future automation) have no user.
#   - `data_types` is JSONB so the array is indexable and the DB
#     can enforce valid JSON at insert time. The contents are a
#     list of strings (e.g. ["btc_price", "correlations"]). The
#     default is an empty JSON array — an export with no data
#     types is meaningless but not a constraint violation.
#   - `file_size` and `downloaded_at` are nullable because they
#     are populated at different stages of the export lifecycle
#     (file_size when the file is generated, downloaded_at when
#     the caller retrieves it).
export_history = Table(
    "export_history",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # Opaque user identifier (nullable — system-triggered exports
    # have no user)
    Column("user_id", String(64), nullable=True),
    # Export format: 'csv', 'png', or 'pdf'
    Column("export_type", String(8), nullable=False),
    # JSON array of data types included in the export, e.g.
    # ["btc_price", "correlations", "regimes", "events"].
    # NOT NULL with a default empty array.
    Column(
        "data_types",
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    ),
    # Timeframe of the exported data: '30d', '90d', '1y', or '5y'
    Column("timeframe", String(8), nullable=False),
    # Generated filename (populated when the file is created)
    Column("file_name", String(255), nullable=False),
    # File size in bytes (populated when the file is created,
    # hence nullable on the initial insert)
    Column("file_size", BigInteger, nullable=True),
    # Lifecycle status: 'pending', 'completed', or 'failed'
    Column(
        "status",
        String(16),
        nullable=False,
        server_default=text("'pending'"),
    ),
    # When the export was requested
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    ),
    # When the file was last downloaded (nullable — most rows
    # will be downloaded once or not at all)
    Column("downloaded_at", DateTime(timezone=True), nullable=True),
)


# ============================================================
# TARGET TABLE: historical_event_impacts
# ============================================================
# One row per historical event and the BTC reaction to it. The
# row records the event's identity (event_name, event_date), its
# classified significance (impact_level), and the price reaction
# over the 48-hour window centered on the event date
# (btc_price_before, btc_price_after, price_change_percent,
# volatility, direction).
#
# Populated by A5.2's reaction calculation; A5.3 aggregates the
# per-event rows into per-event-type metrics; A5.4 exposes both
# via an API endpoint; A5.5 runs the update as a scheduled job.
#
# Design notes:
#   - event_date is a DATE, not a TIMESTAMPTZ. Events happen on a
#     calendar day, and the BTC price window that defines the
#     reaction is measured in days relative to it. Using a date
#     avoids timezone ambiguity: "the FOMC meeting of 2024-03-20"
#     is a date, not a moment.
#   - UNIQUE (event_name, event_date) enforces the natural key.
#     The same event does not happen twice on the same day; if a
#     loader re-processes the same event (e.g. after correcting
#     the price window), it must UPSERT rather than INSERT. This
#     makes A5.5's daily job idempotent by construction.
#   - btc_price_before and btc_price_after are NOT NULL with a
#     positive-value CHECK. An event with no price before or
#     after its window is not a valid row; A5.2 should skip it
#     rather than write a row with NULLs.
#   - volatility is the standard deviation of percentage returns
#     over the window, so it is non-negative by definition. The
#     CHECK enforces that.
#   - direction has no CHECK in the migration beyond the enum
#     values ('up', 'down', 'neutral'). It is derived from
#     price_change_percent, but the table stores both because
#     a threshold can move a near-zero change into "neutral"
#     without changing the exact percentage.
historical_event_impacts = Table(
    "historical_event_impacts",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # Event identity — the natural key is (event_name, event_date)
    Column("event_name", String(64), nullable=False),
    Column("event_date", Date, nullable=False),
    # Classified significance: 'high', 'medium', or 'low'
    Column("impact_level", String(16), nullable=False),
    # Price before the event (24h before the event date)
    Column("btc_price_before", Float, nullable=False),
    # Price after the event (24h after the event date)
    Column("btc_price_after", Float, nullable=False),
    # Percentage change from before to after (signed)
    Column("price_change_percent", Float, nullable=False),
    # Standard deviation of percentage returns over the window
    # (non-negative by definition)
    Column("volatility", Float, nullable=False),
    # Derived direction: 'up', 'down', or 'neutral'
    Column("direction", String(16), nullable=False),
    # Housekeeping
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    ),
)


# ============================================================
# STATE TABLE: model_champions
# ============================================================
# Stores the currently-active champion model per (horizon,
# market_condition). One row per active champion.
#
# Written by daily_promote_champion_job (Phase 3). Read by the
# prediction jobs to decide which model to load for a given
# horizon (and, when regime selection is enabled, for a given
# market regime).
#
# market_condition semantics:
#   NULL       — global champion for the horizon
#   'bull'     — champion when the market is in a bull regime
#   'bear'     — champion when the market is in a bear regime
#   'volatile' — champion when the market is volatile
#   'neutral'  — champion when the market is neutral
#
# When champion_enable_regime_selection is false (default), only
# global champions (market_condition IS NULL) are written and
# consulted. When true, per-regime champions are also written and
# the prediction jobs pick the corresponding one (with global as
# fallback).
#
# This table HAS a _cli variant (model_champions_cli), created
# by migration 014. When CLI_MODE=true, all reads and writes go
# to the CLI table instead, so CLI promotions never affect
# production state.
model_champions = Table(
    "model_champions",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # Which horizon this champion is for
    Column("horizon", String(8), nullable=False),
    # Which market regime. NULL = global champion.
    Column("market_condition", String(16), nullable=True),
    # The champion model
    Column("model_name", String(64), nullable=False),
    Column("model_version", String(64), nullable=False),
    # When the champion was promoted
    Column(
        "promoted_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    ),
    # The metric and value that justified the promotion
    Column("metric_name", String(16), nullable=False),
    Column("metric_value", Float, nullable=False),
    # Sample size and window used to compute metric_value
    Column("sample_size", Integer, nullable=False),
    Column("lookback_days", Integer, nullable=False),
    # The model that was displaced (NULL for the first champion)
    Column("previous_champion", String(64), nullable=True),
    # Free-form reason for the promotion (audit trail)
    Column("reason", Text, nullable=True),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# STATE TABLE: champion_candidates
# ============================================================
# Daily top-ranked candidate per (horizon, market_condition).
# Feeds the stability gate: "has this model been the top
# candidate for N consecutive days?"
#
# Written by daily_promote_champion_job each time it runs.
# One row per (candidate_date, horizon, market_condition,
# model_name, metric_name).
#
# Has a _cli variant (champion_candidates_cli), created by
# migration 014. Routed via CLI mode.
champion_candidates = Table(
    "champion_candidates",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # The date this candidate was the top pick
    Column("candidate_date", Date, nullable=False),
    # Which horizon this candidate is for
    Column("horizon", String(8), nullable=False),
    # Which market regime. NULL = global candidate.
    Column("market_condition", String(16), nullable=True),
    # The top-ranked model for this (date, horizon, regime)
    Column("model_name", String(64), nullable=False),
    # The metric and value that made this model the top candidate
    Column("metric_name", String(16), nullable=False),
    Column("metric_value", Float, nullable=False),
    # Sample size used to compute metric_value
    Column("sample_size", Integer, nullable=False),
    # Housekeeping
    Column("created_at", DateTime(timezone=True), server_default=text("now()")),
)


# ============================================================
# CLI MIRROR TABLES (_cli variants)
# ============================================================
# The manual CLI (app.cli.pipeline) writes to these sandboxed
# tables when CLI_MODE=true. They are structurally identical to
# their production counterparts — same columns, constraints, and
# indexes — created via SQLAlchemy's Table.to_metadata() which
# deep-copies the table definition under a new name.
#
# The tables are created by migrations/011_create_cli_tables.sql.
# The AI Service reads/writes them via the same repository methods;
# the repository picks the CLI variant when settings.cli_mode is
# True (see each repository's _resolve_table helper).
#
# Every write-target table gets a CLI variant. Source tables
# (btc_prices, macro_indicators, features_db) do NOT — they are
# shared, read-only inputs. The 8 write-targets are:
#
#     btc_predictions
#     prediction_performance
#     threshold_breaches
#     model_performance
#     btc_macro_correlation
#     historical_event_impacts
#     model_champions
#     champion_candidates
#
# All 8 have _cli variants, so a CLI run never touches
# production data — including the champion state.

btc_predictions_cli = btc_predictions.to_metadata(
    metadata,
    name=f"{btc_predictions.name}_cli",
)

prediction_performance_cli = prediction_performance.to_metadata(
    metadata,
    name=f"{prediction_performance.name}_cli",
)

threshold_breaches_cli = threshold_breaches.to_metadata(
    metadata,
    name=f"{threshold_breaches.name}_cli",
)

model_performance_cli = model_performance.to_metadata(
    metadata,
    name=f"{model_performance.name}_cli",
)

btc_macro_correlation_cli = btc_macro_correlation.to_metadata(
    metadata,
    name=f"{btc_macro_correlation.name}_cli",
)

historical_event_impacts_cli = historical_event_impacts.to_metadata(
    metadata,
    name=f"{historical_event_impacts.name}_cli",
)

# The champion-state tables also get CLI mirrors. This was not
# part of the original six because we initially assumed champion
# state was a single source of truth. On reflection, full CLI
# isolation requires the champion state to be sandboxed too.
model_champions_cli = model_champions.to_metadata(
    metadata,
    name=f"{model_champions.name}_cli",
)

champion_candidates_cli = champion_candidates.to_metadata(
    metadata,
    name=f"{champion_candidates.name}_cli",
)


# ============================================================
# INDEXES — btc_predictions
# ============================================================
# The composite read index is attached to the Core Table so
# queries benefit from it. Other indexes are created by the
# migrations only.
Index(
    "idx_btc_predictions_horizon_model_time",
    btc_predictions.c.horizon,
    btc_predictions.c.model_name,
    btc_predictions.c.prediction_time,
)


# ============================================================
# INDEXES — prediction_performance
# ============================================================
# The common read index for T5.5's endpoint: "latest metrics for
# a horizon + model, over the last N days".
Index(
    "idx_prediction_performance_horizon_model_date",
    prediction_performance.c.horizon,
    prediction_performance.c.model_name,
    prediction_performance.c.forecast_date,
)


# ============================================================
# INDEXES — threshold_breaches
# ============================================================
# The common read index for T5.6: "recent breaches for a model".
Index(
    "idx_threshold_breaches_horizon_model_date",
    threshold_breaches.c.horizon,
    threshold_breaches.c.model_name,
    threshold_breaches.c.detected_at,
)


# ============================================================
# INDEXES — model_performance
# ============================================================
# Single-column indexes for the three most common filter columns.
# The composite index below covers the common access pattern;
# the single-column ones cover ad-hoc filters (e.g. "all models
# on horizon=7d" or "everything computed since T").
Index(
    "idx_model_performance_model_name",
    model_performance.c.model_name,
)
Index(
    "idx_model_performance_horizon",
    model_performance.c.horizon,
)
Index(
    "idx_model_performance_calculated_at",
    model_performance.c.calculated_at,
)

# Composite index for the primary read pattern:
# "give me the latest N rows for this (model, horizon)".
# DESC on calculated_at because readers almost always want the
# newest first.
Index(
    "idx_model_performance_model_horizon_calc",
    model_performance.c.model_name,
    model_performance.c.horizon,
    model_performance.c.calculated_at.desc(),
)


# ============================================================
# INDEXES — btc_macro_correlation
# ============================================================
# Single-column indexes for the three most common filter columns.
Index(
    "idx_btc_macro_correlation_indicator_name",
    btc_macro_correlation.c.indicator_name,
)
Index(
    "idx_btc_macro_correlation_window_days",
    btc_macro_correlation.c.window_days,
)
Index(
    "idx_btc_macro_correlation_calculated_at",
    btc_macro_correlation.c.calculated_at,
)

# Composite index for the primary read pattern:
# "give me the latest N rows for this (indicator, window)".
# DESC on calculated_at because readers almost always want the
# newest first (the A1.6 API returns the most recent correlation).
Index(
    "idx_btc_macro_correlation_indicator_window_calc",
    btc_macro_correlation.c.indicator_name,
    btc_macro_correlation.c.window_days,
    btc_macro_correlation.c.calculated_at.desc(),
)


# ============================================================
# INDEXES — export_history
# ============================================================
# Single-column index for the "all my exports" query.
Index(
    "idx_export_history_user_id",
    export_history.c.user_id,
)

# Single-column index for "most recent exports across all users".
# DESC because readers almost always want the newest first.
Index(
    "idx_export_history_created_at",
    export_history.c.created_at.desc(),
)

# Composite index for the primary read pattern:
# "my most recent exports".
Index(
    "idx_export_history_user_created",
    export_history.c.user_id,
    export_history.c.created_at.desc(),
)


# ============================================================
# INDEXES — historical_event_impacts
# ============================================================
# Index on event_name for "all reactions to event type X".
Index(
    "idx_historical_event_impacts_event_name",
    historical_event_impacts.c.event_name,
)

# Index on event_date for "all events in this date range". DESC
# because readers almost always want the newest events first.
Index(
    "idx_historical_event_impacts_event_date",
    historical_event_impacts.c.event_date.desc(),
)


# ============================================================
# INDEXES — features_db
# ============================================================
# Primary read pattern: "give me the latest N rows", so a
# DESC index on `ds` covers the common scan.
Index(
    "idx_features_db_ds_desc",
    features_db.c.ds.desc(),
)


# ============================================================
# INDEXES — model_champions
# ============================================================
# Primary read pattern: "give me the active champion(s) for
# horizon X" — used by prediction jobs at every cycle.
Index(
    "idx_model_champions_horizon",
    model_champions.c.horizon,
)

# Audit: "show me promotion history".
Index(
    "idx_model_champions_promoted_at",
    model_champions.c.promoted_at.desc(),
)


# ============================================================
# INDEXES — champion_candidates
# ============================================================
# Primary read pattern: the stability check. "Give me the
# consecutive run of candidate_date rows for this (horizon,
# market_condition, model_name), most recent first."
#
# Note: the migration creates a partial index using
# COALESCE(market_condition, '__global__') to include NULLs.
# SQLAlchemy Core cannot express that COALESCE expression
# directly in an Index() definition, so the composite index here
# is a simpler version that helps the common query.
Index(
    "idx_champion_candidates_stability",
    champion_candidates.c.horizon,
    champion_candidates.c.model_name,
    champion_candidates.c.candidate_date.desc(),
)

# Secondary read: "show me the top candidate for every (horizon,
# regime) on the most recent N days".
Index(
    "idx_champion_candidates_date",
    champion_candidates.c.candidate_date.desc(),
)


# ============================================================
# CONVENIENCE: table name constants
# ============================================================
# These are imported by repositories and tests so they don't
# repeat string literals.
TABLE_BTC_PRICES = settings.db_table_btc_prices
TABLE_MACRO_INDICATORS = settings.db_table_macro_indicators
TABLE_FEATURES_DB = settings.features_db_table
TABLE_BTC_PREDICTIONS = settings.db_table_predictions
TABLE_PREDICTION_PERFORMANCE = "prediction_performance"
TABLE_THRESHOLD_BREACHES = "threshold_breaches"
TABLE_MODEL_PERFORMANCE = "model_performance"
TABLE_BTC_MACRO_CORRELATION = "btc_macro_correlation"
TABLE_EXPORT_HISTORY = "export_history"
TABLE_HISTORICAL_EVENT_IMPACTS = "historical_event_impacts"
TABLE_MODEL_CHAMPIONS = "model_champions"
TABLE_CHAMPION_CANDIDATES = "champion_candidates"

# CLI variant names (the underlying tables are created via
# to_metadata above; these constants are the string names).
TABLE_BTC_PREDICTIONS_CLI = f"{settings.db_table_predictions}_cli"
TABLE_PREDICTION_PERFORMANCE_CLI = "prediction_performance_cli"
TABLE_THRESHOLD_BREACHES_CLI = "threshold_breaches_cli"
TABLE_MODEL_PERFORMANCE_CLI = "model_performance_cli"
TABLE_BTC_MACRO_CORRELATION_CLI = "btc_macro_correlation_cli"
TABLE_HISTORICAL_EVENT_IMPACTS_CLI = "historical_event_impacts_cli"
TABLE_MODEL_CHAMPIONS_CLI = "model_champions_cli"
TABLE_CHAMPION_CANDIDATES_CLI = "champion_candidates_cli"