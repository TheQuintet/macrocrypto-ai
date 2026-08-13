"""
SQLAlchemy model for BTC performance metrics by macroeconomic regime.

Stores performance statistics associated with historical regimes.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
)

from app.models.btc_price import Base


class RegimePerformance(Base):
    """
    BTC performance metrics associated with a macroeconomic regime.
    """

    __tablename__ = "regime_performance"

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

    avg_return = Column(
        Float,
        nullable=True,
    )

    max_drawdown = Column(
        Float,
        nullable=True,
    )

    volatility = Column(
        Float,
        nullable=True,
    )

    sharpe_ratio = Column(
        Float,
        nullable=True,
    )

    btc_price_start = Column(
        Float,
        nullable=True,
    )

    btc_price_end = Column(
        Float,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )