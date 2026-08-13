"""
SQLAlchemy model for the currently identified macroeconomic regime.

Stores the latest regime classification and its validity period.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    CheckConstraint,
)


from app.models.btc_price import Base


class CurrentRegime(Base):
    """
    Current macroeconomic regime classification.
    """

    __tablename__ = "current_regime"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    regime_type = Column(
        String(50),
        nullable=False,
    )

    identified_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "regime_type IN "
            "('high_inflation', 'low_inflation', "
            "'rising_rates', 'falling_rates', "
            "'recession', 'growth')",
            name="ck_current_regime_type",
        ),
    )