"""
SQLAlchemy model for macro indicator vintages.

Stores the point-in-time (PIT) revision history of revision-prone
FRED macro series. Each row is one release of one observation:

    (series_id, observation_date, release_date) -> value

For a given (series_id, observation_date), multiple rows exist —
one per time the value was revised. The features writer uses
"latest release_date <= feature_hour" to select the value that
was actually known at that hour.

Populated for 5 series only:
    CPIAUCSL  -> cpi
    UNRATE    -> unemployment
    FEDFUNDS  -> federal_funds_rate
    M2SL      -> m2_money_supply
    GDP       -> gdp

Market features (DXY, VIX, 10Y, NASDAQ, HY spread) are not
revision-prone and do not get vintages.

See migrations/008_create_macro_indicator_vintages.sql for the
DDL and a longer discussion of the no-op vintage policy.

Model style mirrors app/models/macro_indicator.py:
    - Same Base import
    - Same Column(...) idiom
    - Named UniqueConstraint for ON CONFLICT targeting
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)

from app.models.btc_price import Base


class MacroIndicatorVintage(Base):
    """
    One vintage (release) of one macro indicator observation.

    A "vintage" is the value of an observation as it was known
    at a particular release date. When FRED revises a series,
    the same observation_date gets a new release_date with a
    different value. Both rows are stored; the PIT merge picks
    the one whose release_date is the latest that does not exceed
    the feature hour.
    """

    __tablename__ = "macro_indicator_vintages"

    id = Column(
        Integer,
        nullable=False,
        autoincrement=True,
        primary_key=True,
    )

    # FRED series identifier, e.g. "CPIAUCSL".
    series_id = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # Human-readable feature name used by features_db,
    # e.g. "cpi". Denormalized from series_id so the features
    # writer can join by feature name without a lookup table.
    indicator_name = Column(
        String(100),
        nullable=False,
        index=True,
    )

    # The date the value describes, e.g. 2024-01-01 for January
    # 2024 CPI. DATE, not TIMESTAMPTZ — FRED reports daily,
    # monthly, or quarterly observations, all anchored to a
    # calendar date with no time-of-day meaning.
    observation_date = Column(
        Date,
        nullable=False,
    )

    # The date the value became known. For the first release of
    # an observation, this is shortly after the period ends. For
    # revisions, this is when the revision was published.
    release_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    # The value as of this vintage. NOT NULL: vintages are only
    # written for observations that have a value at release time.
    value = Column(
        Float,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "series_id",
            "observation_date",
            "release_date",
            name="uq_macro_vintage_series_obs_release",
        ),
    )