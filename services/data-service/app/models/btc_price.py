"""
SQLAlchemy model for historical BTC price storage.

The table is stored in TimescaleDB as a hypertable
partitioned by time.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    PrimaryKeyConstraint,
)

from sqlalchemy.orm import declarative_base


Base = declarative_base()


class BTCPrice(Base):
    """
    Historical BTC market data.

    Every WebSocket update is stored as one row.
    """

    __tablename__ = "btc_prices"

    id = Column(
        Integer,
        autoincrement=True,
    )

    time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    price = Column(
        Float,
        nullable=False,
    )

    volume = Column(
        Float,
        nullable=True,
    )

    market_cap = Column(
        Float,
        nullable=True,
    )

    source = Column(
        String(50),
        nullable=False,
        default="binance",
        index=True,
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "time",
            "id",
        ),
    )