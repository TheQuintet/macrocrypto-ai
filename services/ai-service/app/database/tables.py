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
    - btc_predictions:         Target — hourly predictions from the AI Service
                               (unified table; 24h and 7d horizons)
    - prediction_performance:  Target — per-point evaluation metrics (T5.1)
    - threshold_breaches:      Target — threshold breach history (T5.4)
    - model_performance:       Target — per-model aggregate metrics (M7)
    - btc_macro_correlation:   Target — BTC-vs-macro correlation metrics (A1.1)

Naming:
    Table names are pulled from Settings so they can be overridden
    via env vars without touching code. See app/config.py.
"""

import logging

from sqlalchemy import (
    BigInteger,
    Column,
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
# CONVENIENCE: table name constants
# ============================================================
# These are imported by repositories and tests so they don't
# repeat string literals.
TABLE_BTC_PRICES = settings.db_table_btc_prices
TABLE_MACRO_INDICATORS = settings.db_table_macro_indicators
TABLE_BTC_PREDICTIONS = settings.db_table_predictions
TABLE_PREDICTION_PERFORMANCE = "prediction_performance"
TABLE_THRESHOLD_BREACHES = "threshold_breaches"
TABLE_MODEL_PERFORMANCE = "model_performance"
TABLE_BTC_MACRO_CORRELATION = "btc_macro_correlation"