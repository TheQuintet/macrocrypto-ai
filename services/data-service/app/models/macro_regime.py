"""
SQLAlchemy model for macroeconomic regime classification.

Stores historical macroeconomic regime periods.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    String,
    CheckConstraint,
    Index,
)

from app.models.btc_price import Base


class MacroRegime(Base):
    """
    Historical macroeconomic regime classification.
    """

    __tablename__ = "macro_regimes"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    regime_type = Column(
        String(50),
        nullable=False,
    )

    start_date = Column(
        Date,
        nullable=False,
    )

    end_date = Column(
        Date,
        nullable=True,
    )

    duration_days = Column(
        Integer,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "regime_type IN "
            "('high_inflation', 'low_inflation', "
            "'rising_rates', 'falling_rates', "
            "'recession', 'growth')",
            name="ck_macro_regime_type",
        ),
        Index(
            "ix_macro_regimes_regime_type",
            "regime_type",
        ),
        Index(
            "ix_macro_regimes_start_date",
            "start_date",
        ),
        Index(
            "ix_macro_regimes_end_date",
            "end_date",
        ),
    )