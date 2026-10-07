"""
Service for fetching FRED macro indicator vintages.

Fetches the full revision history (vintages) for 5 revision-prone
FRED series and returns records ready for
MacroVintageRepository.create_many.

Why vintages matter
-------------------

FRED series like CPI and GDP get revised after initial release.
Training on the current value of, say, January 2024 CPI leaks
future information: at prediction time in January 2024, only the
initially-released value was knowable. This service preserves
every release so the features writer (B4) can merge PIT-correct
values by selecting, for each feature hour H, the latest vintage
whose release_date <= H.

Series fetched
--------------

    cpi                  <- CPIAUCSL
    unemployment         <- UNRATE
    federal_funds_rate   <- FEDFUNDS
    m2_money_supply      <- M2SL
    gdp                  <- GDP

No other series gets vintages. Market features (DXY, VIX, 10Y,
NASDAQ, HY spread) are not revision-prone.

No-op vintage filter
--------------------

For each (series_id, observation_date), consecutive releases where
the value did not change are collapsed to the first. This halves
the row count without affecting the PIT merge: "latest
release_date <= H" still yields the value in force at H.

The schema permits no-op rows; the service simply doesn't write
them. Dropping the filter later is a service change, not a schema
change. See migration 008 for the full policy note.

Design notes
------------

1. Timestamp convention: DATE, not TIMESTAMPTZ.

   FRED reports observation_date and release_date as calendar
   dates with no time-of-day meaning. Both are stored as DATE in
   the table. The features writer attaches midnight UTC when it
   computes hours-since-release.

2. fredapi is synchronous.

   Fred.get_series_all_releases() is a blocking HTTP call. It is
   wrapped in asyncio.to_thread() so collect() can be awaited
   from the scheduler without blocking the event loop.

3. Placeholder guard.

   The repo's .env has FRED_API_KEY=your_api_key_here as a
   placeholder. Without a guard, the daily job would silently
   hit FRED with a bad key, log errors, and write nothing — hard
   to diagnose. __init__ raises RuntimeError immediately if the
   key is missing, empty, or the literal placeholder. The
   scheduler wraps construction in try/except so the loop
   survives.

4. Partial failure.

   Each series is fetched in its own try/except. If one series
   fails, the others still complete and the service returns what
   it got. If all series fail, collect() returns []. This
   matches the defensive posture of HighYieldCreditStressService
   (B5) and GoldSpotService.

5. Lookback.

   Each run fetches VINTAGE_LOOKBACK_YEARS (default 20) of
   history. Idempotent writes make a wide window free on a
   healthy system: the ON CONFLICT clause skips
   already-stored triples. The CLI can override the window for
   one run via --years.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from typing import Any

import pandas as pd

from app.config import settings
from app.database.macro_vintage_repository import (
    MacroVintageRepository,
)


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------


# The five series that get vintages, in a fixed order for
# deterministic logging and iteration. The indicator_name values
# match the features_db column names (schemas.md §6.1).
VINTAGE_SERIES: dict[str, str] = {
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "federal_funds_rate": "FEDFUNDS",
    "m2_money_supply": "M2SL",
    "gdp": "GDP",
}


# Columns fredapi returns that we rely on. If any is missing,
# the service logs a clear error and skips the series rather than
# raising KeyError from deep inside pandas.
_REQUIRED_FRED_COLUMNS = {"date", "realtime_start", "value"}


# The literal placeholder shipped in .env. Fail loudly rather
# than attempt a FRED request with it.
_PLACEHOLDER_FRED_KEY = "your_api_key_here"


# ------------------------------------------------------------------
# FRED key guard
# ------------------------------------------------------------------


def _assert_fred_key_configured() -> None:
    """
    Raise RuntimeError if FRED_API_KEY is unset, empty, or the
    literal placeholder from .env.example.

    Called from __init__. The scheduler catches this and logs;
    the CLI lets it propagate with a clear message.

    The message points at .env.local because pydantic-settings
    prefers .env.local over .env when both exist. Setting the
    real key there leaves the placeholder in .env as documentation.
    """
    key = settings.FRED_API_KEY

    if key is None or key == "":
        raise RuntimeError(
            "FRED_API_KEY is not configured. Set it in "
            "services/data-service/.env.local "
            "(or .env if .env.local does not exist). "
            "Get a key at "
            "https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    if key == _PLACEHOLDER_FRED_KEY:
        raise RuntimeError(
            "FRED_API_KEY is still the placeholder value "
            f"'{_PLACEHOLDER_FRED_KEY}'. Set a real key in "
            "services/data-service/.env.local "
            "(or .env if .env.local does not exist)."
        )


# ------------------------------------------------------------------
# Service
# ------------------------------------------------------------------


class MacroVintageService:
    """
    Fetch FRED macro vintages and return records for persistence.

    Usage:

        db = SessionLocal()
        service = MacroVintageService(db)
        records = await service.collect()
        service.repository.create_many(records)

    Or with a custom FRED client (for tests):

        service = MacroVintageService(db, fred_client=FakeFred())
    """

    def __init__(
        self,
        db,
        fred_client: Any | None = None,
        lookback_years: int | None = None,
    ):
        """
        Args:
            db: SQLAlchemy session.
            fred_client: Optional injected FRED client. If None,
                a real fredapi.Fred is constructed using
                settings.FRED_API_KEY. Tests pass a fake.
            lookback_years: Optional override for
                settings.VINTAGE_LOOKBACK_YEARS. Used by the CLI
                --years flag. If None, the setting is used.
        """
        # Only enforce the key guard when we're about to build a
        # real client. Tests inject a fake and skip this check.
        if fred_client is None:
            _assert_fred_key_configured()

            # Import lazily so that merely importing this module
            # does not pull fredapi into the process.
            from fredapi import Fred

            self.fred = Fred(api_key=settings.FRED_API_KEY)
            self._owns_client = True
        else:
            self.fred = fred_client
            self._owns_client = False

        self.repository = MacroVintageRepository(db)

        if lookback_years is not None and lookback_years <= 0:
            raise ValueError(
                "lookback_years must be a positive integer"
            )

        self.lookback_years = (
            lookback_years
            if lookback_years is not None
            else settings.VINTAGE_LOOKBACK_YEARS
        )

    async def close(self) -> None:
        """
        fredapi.Fred holds no persistent connection and has no
        close() method. Kept as a no-op for symmetry with the
        other services so callers can uniformly `await
        service.close()` in a finally block.
        """
        return None

    async def collect(self) -> list[dict[str, Any]]:
        """
        Fetch every vintage for the 5 series within the lookback
        window and return records ready for create_many.

        Returns:
            A list of dicts, each with exactly these keys:

                {
                    "series_id":        str,   e.g. "CPIAUCSL"
                    "indicator_name":   str,   e.g. "cpi"
                    "observation_date": date,
                    "release_date":     date,
                    "value":            float,
                }

            Empty list if every series fails. Partial success
            returns whatever succeeded; failing series are logged
            and skipped.

        This method performs network I/O (via asyncio.to_thread)
        but no database writes. Persistence is the caller's
        responsibility, matching the pattern of GoldSpotService
        and HighYieldCreditStressService.
        """
        cutoff = _lookback_cutoff(self.lookback_years)

        logger.info(
            "Macro vintage collection starting "
            "(lookback=%d years, cutoff=%s)",
            self.lookback_years,
            cutoff.isoformat(),
        )

        all_frames: list[pd.DataFrame] = []
        failed_series: list[str] = []

        for indicator_name, series_id in VINTAGE_SERIES.items():
            frame = await self._fetch_one(
                indicator_name=indicator_name,
                series_id=series_id,
                cutoff=cutoff,
            )

            if frame is None or frame.empty:
                failed_series.append(series_id)
                continue

            all_frames.append(frame)

        if not all_frames:
            logger.warning(
                "Macro vintage collection: no data returned "
                "for any series (%d failed)",
                len(failed_series),
            )
            return []

        if failed_series:
            logger.warning(
                "Macro vintage collection: %d series failed "
                "(%s); proceeding with %d successful series",
                len(failed_series),
                ", ".join(failed_series),
                len(all_frames),
            )

        # ------------------------------------------------------
        # Combine, then apply the no-op vintage filter across
        # the union of all series.
        # ------------------------------------------------------

        combined = pd.concat(all_frames, ignore_index=True)

        before_filter = len(combined)
        combined = _remove_noop_vintages(combined)
        after_filter = len(combined)

        logger.info(
            "Macro vintage no-op filter: %d -> %d rows "
            "(removed %d)",
            before_filter,
            after_filter,
            before_filter - after_filter,
        )

        records = _frames_to_records(combined)

        logger.info(
            "Macro vintage collection complete: "
            "%d records ready for persistence",
            len(records),
        )

        return records

    async def _fetch_one(
        self,
        indicator_name: str,
        series_id: str,
        cutoff: date,
    ) -> pd.DataFrame | None:
        """
        Fetch and normalize one series.

        Returns a DataFrame with columns:
            series_id, indicator_name, observation_date,
            release_date, value
        or None on failure.

        Never raises: all errors are logged and swallowed so a
        single bad series does not abort the whole run.
        """
        logger.info(
            "Processing %s vintages (%s -> today)...",
            indicator_name,
            cutoff.isoformat(),
        )

        try:
            raw = await asyncio.to_thread(
                self.fred.get_series_all_releases,
                series_id,
            )
        except Exception:
            logger.exception(
                "Macro vintage fetch failed for %s (%s)",
                indicator_name,
                series_id,
            )
            return None

        if raw is None or len(raw) == 0:
            logger.warning(
                "Macro vintage fetch returned no rows for %s (%s)",
                indicator_name,
                series_id,
            )
            return None

        missing = _REQUIRED_FRED_COLUMNS - set(raw.columns)
        if missing:
            logger.error(
                "Macro vintage fetch for %s (%s) is missing "
                "expected columns %s; got %s",
                indicator_name,
                series_id,
                sorted(missing),
                list(raw.columns),
            )
            return None

        # ------------------------------------------------------
        # Normalize. fredapi returns:
        #   date           -> observation_date
        #   realtime_start -> release_date
        #   value          -> value
        # ------------------------------------------------------

        frame = raw.loc[:, ["date", "realtime_start", "value"]].copy()
        frame = frame.rename(
            columns={
                "date": "observation_date",
                "realtime_start": "release_date",
            }
        )

        # Coerce to proper date types. fredapi usually returns
        # pandas datetime64, but be defensive against string
        # returns across versions.
        frame["observation_date"] = pd.to_datetime(
            frame["observation_date"]
        ).dt.date
        frame["release_date"] = pd.to_datetime(
            frame["release_date"]
        ).dt.date

        # Drop rows with null value or dates. FRED occasionally
        # emits a release with no value (holiday, series start).
        frame = frame.dropna(
            subset=["observation_date", "release_date", "value"]
        )

        # Filter to the lookback window.
        frame = frame[frame["observation_date"] >= cutoff]

        frame["series_id"] = series_id
        frame["indicator_name"] = indicator_name

        # Reorder for readability.
        frame = frame[
            [
                "series_id",
                "indicator_name",
                "observation_date",
                "release_date",
                "value",
            ]
        ]

        frame["value"] = frame["value"].astype("float64")

        logger.info(
            "  %s: fetched=%d rows on/after %s",
            indicator_name,
            len(frame),
            cutoff.isoformat(),
        )

        return frame


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _lookback_cutoff(years: int) -> date:
    """
    Return today's date minus `years` years, as a `date`.

    Used to filter FRED results to a window. Uses 365.25-day
    years and floors to the day; the exact calendar day within
    a day or two does not matter for a 20-year window.
    """
    days = int(years * 365.25)
    return (pd.Timestamp.utcnow().normalize() - pd.Timedelta(days=days)).date()


def _remove_noop_vintages(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """
    Collapse consecutive same-value vintages per
    (series_id, observation_date).

    Sort by (series_id, observation_date, release_date), then
    keep rows where `value` differs from the previous row for the
    same (series_id, observation_date). The first row per group
    is always kept.

    Identical semantics to remove_noop_vintages() in the
    original app/scripts/fetch_macro_vintages.py.
    """
    if frame.empty:
        return frame

    frame = frame.sort_values(
        ["series_id", "observation_date", "release_date"],
    ).reset_index(drop=True)

    value_changed = (
        frame.groupby(["series_id", "observation_date"])["value"]
        .diff()
        .fillna(1)
        != 0
    )

    return frame[value_changed].reset_index(drop=True)


def _frames_to_records(
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Convert the combined DataFrame into a list of record dicts
    matching what MacroVintageRepository.create_many expects.

    Each record has exactly:
        series_id, indicator_name, observation_date,
        release_date, value

    No created_at: the table default supplies it.
    """
    records: list[dict[str, Any]] = []

    for row in frame.itertuples(index=False):
        records.append(
            {
                "series_id": row.series_id,
                "indicator_name": row.indicator_name,
                "observation_date": row.observation_date,
                "release_date": row.release_date,
                "value": float(row.value),
            }
        )

    return records