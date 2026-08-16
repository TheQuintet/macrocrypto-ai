"""
SQLAlchemy model for BTC reaction to macroeconomic events.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from app.models.btc_price import Base


class RegimeEventAnalysis(Base):
    """
    BTC price reaction to a macroeconomic event
    within a specific macroeconomic regime.
    """

    __tablename__ = "regime_event_analysis"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    regime_id = Column(
        Integer,
        ForeignKey("macro_regimes.id"),
        nullable=False,
        index=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    event_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    btc_price_before = Column(
        Float,
        nullable=False,
    )

    btc_price_after = Column(
        Float,
        nullable=False,
    )

    btc_return = Column(
        Float,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )