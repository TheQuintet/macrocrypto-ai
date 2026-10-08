"""
SQLAlchemy model for the hourly BTC price table.

One row per hour (UTC). Materialized from raw btc_prices ticks,
btc_dominance, and macro_indicators (for active_addresses).

The table is stored in TimescaleDB as a hypertable partitioned
by time.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    PrimaryKeyConstraint,
)

from app.models.btc_price import Base


class BTCPriceHourly(Base):
    """Hourly BTC price and derived features."""

    __tablename__ = "btc_prices_hourly"

    time = Column(
        DateTime(timezone=True),
        nullable=False,
        primary_key=True,
    )

    close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    dominance = Column(Float, nullable=True)
    active_addresses = Column(Float, nullable=True)
    price_lag_7d = Column(Float, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        PrimaryKeyConstraint("time"),
    )