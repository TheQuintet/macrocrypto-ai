"""
Database model for historical Bitcoin market dominance.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, UniqueConstraint

from app.models.btc_price import Base


class BTCDominance(Base):
    """
    Historical Bitcoin market dominance percentage.

    Source:
        CoinGecko /global endpoint
    """

    __tablename__ = "btc_dominance"

    id = Column(Integer, primary_key=True, autoincrement=True)

    time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    dominance = Column(
        Float,
        nullable=False,
    )

    source = Column(
        String(50),
        nullable=False,
        default="coingecko",
    )

    __table_args__ = (
        UniqueConstraint(
            "time",
            name="uq_btc_dominance_time",
        ),
    )