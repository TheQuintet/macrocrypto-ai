"""
SQLAlchemy model for the hourly macro indicators table.

One row per hour (UTC). Materialized from raw macro_indicators
(long format) via pivot + rename + forward-fill.

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


class MacroIndicatorHourly(Base):
    """Hourly macro indicators, wide format."""

    __tablename__ = "macro_indicators_hourly"

    time = Column(
        DateTime(timezone=True),
        nullable=False,
        primary_key=True,
    )

    cpi = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    m2_growth = Column(Float, nullable=True)
    dxy = Column(Float, nullable=True)
    treasury_yield = Column(Float, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        PrimaryKeyConstraint("time"),
    )