"""
SQLAlchemy model for historical BTC price storage.

Initially this table works as a normal PostgreSQL table.

If TimescaleDB is enabled later it can be converted into a
hypertable without changing the application code.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
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
        primary_key=True,
        autoincrement=True,
    )

    time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
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