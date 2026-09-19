"""SQLAlchemy Core table definitions for the AI Service.

This module defines the tables the AI Service reads from and writes
to. It uses SQLAlchemy Core (not ORM) because:
    - TimescaleDB hypertables are simpler to express as Core Tables
    - Queries are mostly analytical (SELECT / INSERT), not object graphs
    - Raw SQL is used for Timescale-specific DDL (create_hypertable)
      — those live in later branches (T1.3, T3.2, T5.1)

Tables:
    - btc_prices:        Source — hourly BTC OHLCV + market metrics
                         (written by Data Ingestion Service)
    - macro_indicators:  Source — macro features (CPI, rates, etc.)
                         (written by Data Ingestion Service)
    - btc_predictions:   Target — hourly predictions from the AI Service
                         (unified table, filtered by `horizon` and
                         `model_name`; 24h today, 7d and multi-model later)

Naming:
    Table names are pulled from Settings so they can be overridden
    via env vars without touching code. See app/config.py.
"""

import logging

from sqlalchemy import (
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
# This is the schema T1.2 writes to. T1.3 will add the hypertable
# DDL, indexes, and a migration file. The columns here are the
# minimum required for T1.2's writes to succeed.
btc_predictions = Table(
    settings.db_table_predictions,
    metadata,
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
# INDEXES
# ============================================================
# T1.3 will define the canonical indexes as part of the migration.
# This lightweight index helps the common read pattern used in T1.2:
# "give me the latest predictions for a given horizon and model".
Index(
    "idx_btc_predictions_horizon_model_time",
    btc_predictions.c.horizon,
    btc_predictions.c.model_name,
    btc_predictions.c.prediction_time,
)