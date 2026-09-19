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
prediction_performance = Table(
    "prediction_performance",
    metadata,
    # Surrogate primary key
    Column("id", BigInteger, primary_key=True),
    # FK to btc_predictions.id
    Column("prediction_id", BigInteger, nullable=False),
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
# CONVENIENCE: table name constants
# ============================================================
# These are imported by repositories and tests so they don't
# repeat string literals.
TABLE_BTC_PRICES = settings.db_table_btc_prices
TABLE_MACRO_INDICATORS = settings.db_table_macro_indicators
TABLE_BTC_PREDICTIONS = settings.db_table_predictions
TABLE_PREDICTION_PERFORMANCE = "prediction_performance"