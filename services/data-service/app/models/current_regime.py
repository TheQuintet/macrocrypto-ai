# # """
# # SQLAlchemy model for the currently identified macroeconomic regime.

# # Stores the latest regime classification and its validity period.
# # """

# # from datetime import datetime, timezone

# # from sqlalchemy import (
# #     Column,
# #     DateTime,
# #     Integer,
# #     String,
# #     CheckConstraint,
# # )


# # from app.models.btc_price import Base


# # class CurrentRegime(Base):
# #     """
# #     Current macroeconomic regime classification.
# #     """

# #     __tablename__ = "current_regime"

# #     id = Column(
# #         Integer,
# #         primary_key=True,
# #         autoincrement=True,
# #     )

# #     regime_type = Column(
# #         String(50),
# #         nullable=False,
# #     )

# #     identified_at = Column(
# #         DateTime(timezone=True),
# #         nullable=False,
# #         default=lambda: datetime.now(timezone.utc),
# #     )

# #     expires_at = Column(
# #         DateTime(timezone=True),
# #         nullable=True,
# #     )

# #     __table_args__ = (
# #         CheckConstraint(
# #             "regime_type IN "
# #             "('high_inflation', 'low_inflation', "
# #             "'rising_rates', 'falling_rates', "
# #             "'recession', 'growth')",
# #             name="ck_current_regime_type",
# #         ),
# #     )

# """
# SQLAlchemy model for the currently identified macroeconomic regime.

# Stores the latest regime classification, confidence level,
# and its validity period.
# """

# from datetime import datetime, timezone

# from sqlalchemy import (
#     CheckConstraint,
#     Column,
#     DateTime,
#     Float,
#     Integer,
#     String,
# )

# from app.models.btc_price import Base


# class CurrentRegime(Base):
#     """
#     Current macroeconomic regime classification.

#     The confidence value represents the application's
#     confidence in the identified regime as a percentage
#     from 0.0 to 100.0.
#     """

#     __tablename__ = "current_regime"

#     id = Column(
#         Integer,
#         primary_key=True,
#         autoincrement=True,
#     )

#     regime_type = Column(
#         String(50),
#         nullable=False,
#     )

#     confidence = Column(
#         Float,
#         nullable=False,
#         default=100.0,
#     )

#     identified_at = Column(
#         DateTime(timezone=True),
#         nullable=False,
#         default=lambda: datetime.now(timezone.utc),
#     )

#     expires_at = Column(
#         DateTime(timezone=True),
#         nullable=True,
#     )

#     __table_args__ = (
#         CheckConstraint(
#             "regime_type IN "
#             "('high_inflation', 'low_inflation', "
#             "'rising_rates', 'falling_rates', "
#             "'recession', 'growth')",
#             name="ck_current_regime_type",
#         ),
#         CheckConstraint(
#             "confidence >= 0 AND confidence <= 100",
#             name="ck_current_regime_confidence",
#         ),
#     )

"""
SQLAlchemy model for the currently identified macroeconomic regime.

Stores the latest regime classification, confidence level,
visual market indicator, and validity period.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    CheckConstraint,
)

from app.models.btc_price import Base


class CurrentRegime(Base):
    """
    Current macroeconomic regime classification.

    Stores:
    - Regime type
    - Classification confidence percentage
    - Visual market indicator
    - Identification timestamp
    - Optional expiration timestamp
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

    confidence = Column(
        Float,
        nullable=False,
    )

    visual_indicator = Column(
        String(20),
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

        CheckConstraint(
            "confidence >= 0 AND confidence <= 100",
            name="ck_current_regime_confidence",
        ),

        CheckConstraint(
            "visual_indicator IN "
            "('bull', 'bear', 'recession')",
            name="ck_current_regime_visual_indicator",
        ),
    )