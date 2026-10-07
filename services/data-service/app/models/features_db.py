"""
SQLAlchemy model for features_db.

The ML feature table: one row per hour (UTC) containing the
53-column contract v2 feature vector and its target.

Consumers:
    - The AI Service reads this via the DB path
      (fetch_training_frame_from_features_db) once its config
      defaults point at the hourly tables.
    - The hourly parquet writer produces a matching 53-column
      frame written to app/data/processed_v2_builder/.

Contract v2 (53 columns):
     2  ds, y
     4  raw market & on-chain
    13  macro & external assets
    10  technical indicators & ratios
     4  data-quality flags         (INTEGER, not BOOLEAN — D8)
    14  observation recency trackers (INTEGER, HOURS, names keep
          the _days_since_* suffix — D8)
     6  engineered features

Column types: 45 base + 6 engineered = Float; 4 flags + 14
trackers = Integer. Never Boolean — the AI Service's loader
expects numeric and the schema doc locks INTEGER (D8).

Model style mirrors app/models/macro_indicator.py and
app/models/macro_indicator_vintage.py:
    - Same Base import
    - Same Column(...) idiom
    - Same explicit nullable=
    - Same PrimaryKeyConstraint in __table_args__

See migrations/009_create_features_db.sql for the DDL and the
governance/hypertable notes.
"""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    PrimaryKeyConstraint,
)

from app.models.btc_price import Base


class FeaturesDB(Base):
    """
    One hourly feature row for the ML pipeline.

    `ds` is the primary key. `y` is the target: the BTC close at
    ds + 1 hour. All other columns are nullable (feature
    availability varies by source); the writer's job is to
    populate them faithfully, not to guarantee non-nullness.
    """

    __tablename__ = "features_db"

    # ------------------------------------------------------------------
    # Timestamp and target (2)
    # ------------------------------------------------------------------

    ds = Column(
        DateTime(timezone=True),
        nullable=False,
        primary_key=True,
    )

    y = Column(
        Float,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Raw market & on-chain (4)
    # ------------------------------------------------------------------

    btc_price = Column(Float, nullable=True)
    btc_volume = Column(Float, nullable=True)
    btc_dominance = Column(Float, nullable=True)
    active_addresses = Column(Float, nullable=True)

    # ------------------------------------------------------------------
    # Macro & external assets (13)
    # ------------------------------------------------------------------

    gold_spot = Column(Float, nullable=True)
    dxy = Column(Float, nullable=True)
    ten_year_treasury = Column(Float, nullable=True)
    vix = Column(Float, nullable=True)
    high_yield_spread = Column(Float, nullable=True)
    nasdaq_composite = Column(Float, nullable=True)
    equity_corr = Column(Float, nullable=True)
    high_yield_credit_stress_proxy = Column(Float, nullable=True)
    cpi = Column(Float, nullable=True)
    federal_funds_rate = Column(Float, nullable=True)
    gdp = Column(Float, nullable=True)
    m2_money_supply = Column(Float, nullable=True)
    unemployment = Column(Float, nullable=True)

    # ------------------------------------------------------------------
    # Technical indicators & ratios (10)
    # ------------------------------------------------------------------

    btc_log_return_1d = Column(Float, nullable=True)
    btc_log_return_7d = Column(Float, nullable=True)
    btc_log_return_30d = Column(Float, nullable=True)
    btc_sma_7 = Column(Float, nullable=True)
    btc_sma_30 = Column(Float, nullable=True)
    btc_sma_90 = Column(Float, nullable=True)
    btc_volatility_7d = Column(Float, nullable=True)
    btc_volatility_30d = Column(Float, nullable=True)
    btc_gold_ratio = Column(Float, nullable=True)
    btc_nasdaq_ratio = Column(Float, nullable=True)

    # ------------------------------------------------------------------
    # Data-quality flags (4) — INTEGER, not BOOLEAN
    # ------------------------------------------------------------------

    high_yield_spread_is_missing = Column(Integer, nullable=True)
    active_addresses_is_imputed = Column(Integer, nullable=True)
    unemployment_is_imputed = Column(Integer, nullable=True)
    warmup_complete = Column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Observation recency trackers (14) — INTEGER, stored in HOURS,
    # names keep the _days_since_* suffix (D8)
    # ------------------------------------------------------------------

    btc_dominance_days_since_last_observation = Column(
        Integer, nullable=True
    )
    gold_spot_days_since_last_observation = Column(
        Integer, nullable=True
    )
    dxy_days_since_last_observation = Column(
        Integer, nullable=True
    )
    ten_year_treasury_days_since_last_observation = Column(
        Integer, nullable=True
    )
    vix_days_since_last_observation = Column(
        Integer, nullable=True
    )
    nasdaq_composite_days_since_last_observation = Column(
        Integer, nullable=True
    )
    equity_corr_days_since_last_observation = Column(
        Integer, nullable=True
    )
    high_yield_credit_stress_proxy_days_since_last_observation = Column(
        Integer, nullable=True
    )
    active_addresses_days_since_last_observation = Column(
        Integer, nullable=True
    )
    cpi_days_since_release = Column(Integer, nullable=True)
    federal_funds_rate_days_since_release = Column(
        Integer, nullable=True
    )
    gdp_days_since_release = Column(Integer, nullable=True)
    m2_money_supply_days_since_release = Column(
        Integer, nullable=True
    )
    unemployment_days_since_release = Column(
        Integer, nullable=True
    )

    # ------------------------------------------------------------------
    # Engineered features (6)
    # ------------------------------------------------------------------

    eng_price_lag_1d = Column(Float, nullable=True)
    eng_price_lag_7d = Column(Float, nullable=True)
    eng_price_lag_30d = Column(Float, nullable=True)
    eng_returns_1d = Column(Float, nullable=True)
    eng_returns_7d = Column(Float, nullable=True)
    eng_returns_30d = Column(Float, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("ds"),
    )