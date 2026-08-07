"""
SQLAlchemy model for macroeconomic indicator storage.

Stores historical macroeconomic data from sources
such as FRED.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    PrimaryKeyConstraint,
    UniqueConstraint,
)

from app.models.btc_price import Base


class MacroIndicator(Base):
    """
    Historical macroeconomic indicator data.

    Examples:
    - CPI Inflation
    - Federal Funds Rate
    - GDP
    - Unemployment Rate
    - M2 Money Supply
    """

    __tablename__ = "macro_indicators"

    id = Column(
        Integer,
        nullable=False,
        autoincrement=True,
    )

    time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    indicator_name = Column(
        String(100),
        nullable=False,
        index=True,
    )

    value = Column(
        Float,
        nullable=False,
    )

    previous_value = Column(
        Float,
        nullable=True,
    )

    change_percent = Column(
        Float,
        nullable=True,
    )

    source = Column(
        String(50),
        nullable=False,
        default="fred",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
    PrimaryKeyConstraint(
        "time",
        "id",
    ),
    UniqueConstraint(
        "time",
        "indicator_name",
        name="uq_macro_indicator_time_name",
    ),
)