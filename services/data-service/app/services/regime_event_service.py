"""
Macro event analysis service.

Computes BTC's reaction to macroeconomic events over a
48-hour window centered on each event's timestamp, and writes
one row per (regime, event_type, event_date) triple to
regime_event_analysis.

Design notes:

    - Events come from economic_events (populated by
      EconomicCalendarService from FRED). event_type is one of
      {'fed','cpi','employment','gdp'}; we map those onto the
      regime_event_analysis vocabulary
      {'fed_meeting','cpi_release','employment_report','gdp_release'}.

    - The window is symmetric: [event - 24h, event + 24h].
      Both endpoints use a PIT lookup — the last btc_prices tick
      with time <= endpoint — so the analysis never peeks at a
      future price.

    - Events are filtered to:
        * impact_level in {high, medium}
        * event_date within the last LOOKBACK days
        * event_date at least 24h in the past
          (so the "after" price exists)

    - Idempotent by pre-check: regime_event_analysis has no
      unique constraint on (regime_id, event_type, event_date),
      so the service calls repository.exists(...) for each
      candidate and skips matches.

    - Batch write: all staged rows commit in one transaction.
      A single bad event rolls back the batch.

    The ReactionCalculator in the AI Service provides the
    reference semantics for "BTC reaction to an event". This
    service ports that logic (PIT lookup + symmetric window)
    rather than copying its implementation.
"""

import logging
from datetime import date, datetime, timedelta, timezone
import csv
import io

from sqlalchemy.orm import Session

from app.database.regime_event_repository import (
    RegimeEventRepository,
)
from app.database.regime_repository import (
    RegimeRepository,
)

logger = logging.getLogger(__name__)


SUPPORTED_EVENTS = {
    "fed_meeting",
    "cpi_release",
    "gdp_release",
    "employment_report",
}


# Map economic_events.event_type -> regime_event_analysis.event_type.
# The two tables use different vocabularies on purpose: the raw
# calendar is short-form ('fed'), the analysis table is
# human-readable ('fed_meeting').
_EVENT_TYPE_MAP = {
    "fed": "fed_meeting",
    "cpi": "cpi_release",
    "gdp": "gdp_release",
    "employment": "employment_report",
}


# Impact levels we compute reactions for. Low-impact events are
# excluded — they tend not to move BTC meaningfully and would
# bloat the table.
_IMPACT_LEVELS = ("high", "medium")


# How far back to scan economic_events on each run.
_DEFAULT_LOOKBACK_DAYS = 90


# Half-width of the reaction window, in hours.
_EVENT_WINDOW_HOURS = 24


class RegimeEventService:
    """
    Calculates BTC reactions to macroeconomic events.
    """

    def __init__(self, db: Session):
        self.db = db
        self.events = RegimeEventRepository(db)
        self.regimes = RegimeRepository(db)

    # ============================================================
    # VALIDATION
    # ============================================================

    @staticmethod
    def validate_event_type(
        event_type: str,
    ) -> None:
        """
        Validate supported macroeconomic event types.
        """

        if event_type not in SUPPORTED_EVENTS:
            raise ValueError(
                f"Unsupported event type: {event_type}"
            )

    # ============================================================
    # BTC REACTION
    # ============================================================

    @staticmethod
    def calculate_reaction(
        btc_price_before: float,
        btc_price_after: float,
    ) -> float:
        """
        Calculate BTC percentage return around an event.
        """

        if btc_price_before <= 0:
            raise ValueError(
                "BTC price before event must be greater than zero"
            )

        return (
            (
                btc_price_after
                - btc_price_before
            )
            / btc_price_before
        ) * 100

    # ============================================================
    # CREATE EVENT ANALYSIS
    # ============================================================

    def analyze_event(
        self,
        regime_id: int,
        event_type: str,
        event_date: date,
        btc_price_before: float,
        btc_price_after: float,
    ):
        """
        Calculate and persist BTC reaction to a macroeconomic event.
        """

        self.validate_event_type(event_type)

        btc_return = self.calculate_reaction(
            btc_price_before,
            btc_price_after,
        )

        return self.events.create_event_analysis(
            regime_id=regime_id,
            event_type=event_type,
            event_date=event_date,
            btc_price_before=btc_price_before,
            btc_price_after=btc_price_after,
            btc_return=btc_return,
        )

    # ============================================================
    # GET EVENT ANALYSIS
    # ============================================================

    def get_event_analysis(
        self,
        regime_id: int | None = None,
    ):
        """
        Retrieve persisted macro event analysis.

        If regime_id is provided, return events belonging
        to that regime.

        Otherwise return all event analysis records.
        """

        if regime_id is not None:
            return self.events.get_by_regime(
                regime_id
            )

        return self.events.get_all()

    def export_event_analysis_csv(
        self,
        event_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        """
        Export macro event analysis as CSV.

        Optional filters:
        - event_type
        - start_date
        - end_date
        """

        events = self.get_event_analysis(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
        )

        output = io.StringIO()

        fieldnames = [
            "id",
            "regime_id",
            "event_type",
            "event_date",
            "btc_price_before",
            "btc_price_after",
            "btc_return",
            "created_at",
        ]

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for event in events:
            writer.writerow(
                {
                    "id": event.id,
                    "regime_id": event.regime_id,
                    "event_type": event.event_type,
                    "event_date": event.event_date,
                    "btc_price_before": event.btc_price_before,
                    "btc_price_after": event.btc_price_after,
                    "btc_return": event.btc_return,
                    "created_at": event.created_at,
                }
            )

        return output.getvalue()

    # ============================================================
    # EVENT REACTION — REAL IMPLEMENTATION
    # ============================================================

    def process_current_regime_event(self, regime):
        """
        Compute BTC reactions for events in the active regime.

        Thin wrapper around process_regime_events() so existing
        callers keep working. regime may be a MacroRegime or
        CurrentRegime instance; only .id is used.
        """

        if regime is None:
            logger.info(
                "RegimeEventService: no active regime; "
                "skipping event analysis"
            )
            return {
                "events_scanned": 0,
                "rows_inserted": 0,
                "skipped_existing": 0,
                "skipped_missing_price": 0,
                "skipped_unmapped_type": 0,
            }

        regime_id = getattr(regime, "id", None)

        if regime_id is None:
            # CurrentRegime has an id, but guard against mocks
            # and odd callers.
            logger.warning(
                "RegimeEventService: regime has no id; "
                "skipping event analysis"
            )
            return {
                "events_scanned": 0,
                "rows_inserted": 0,
                "skipped_existing": 0,
                "skipped_missing_price": 0,
                "skipped_unmapped_type": 0,
            }

        return self.process_regime_events(regime_id)

    def process_regime_events(
        self,
        regime_id: int,
        lookback_days: int = _DEFAULT_LOOKBACK_DAYS,
    ) -> dict:
        """
        Scan recent economic_events and write BTC reactions to
        regime_event_analysis for the given regime.

        Returns a summary dict:
            {
                "events_scanned":        int,
                "rows_inserted":         int,
                "skipped_existing":      int,
                "skipped_missing_price": int,
                "skipped_unmapped_type": int,
            }

        Idempotent: a second call with the same events is a
        no-op (the exists() pre-check skips them). The whole
        batch commits in one transaction — a single failure
        rolls back everything.
        """

        events = self._recent_events(lookback_days)

        stats = {
            "events_scanned": len(events),
            "rows_inserted": 0,
            "skipped_existing": 0,
            "skipped_missing_price": 0,
            "skipped_unmapped_type": 0,
        }

        if not events:
            logger.info(
                "RegimeEventService: no candidate events in the "
                "last %d days; nothing to do",
                lookback_days,
            )
            return stats

        rows_to_insert: list[dict] = []
        now = datetime.now(timezone.utc)

        for event in events:
            mapped_type = self._normalize_event_type(
                event.event_type
            )

            if mapped_type is None:
                stats["skipped_unmapped_type"] += 1
                continue

            event_dt = event.event_date
            if event_dt.tzinfo is None:
                event_dt = event_dt.replace(tzinfo=timezone.utc)

            # Skip if the "after" window is still in the future.
            # (Guaranteed by _recent_events, but belt-and-braces.)
            if event_dt + timedelta(hours=_EVENT_WINDOW_HOURS) > now:
                continue

            event_day = event_dt.date()

            if self.events.exists(
                regime_id=regime_id,
                event_type=mapped_type,
                event_date=event_day,
            ):
                stats["skipped_existing"] += 1
                continue

            before_dt = event_dt - timedelta(
                hours=_EVENT_WINDOW_HOURS
            )
            after_dt = event_dt + timedelta(
                hours=_EVENT_WINDOW_HOURS
            )

            price_before = self._get_btc_price_at_or_before(
                before_dt
            )
            price_after = self._get_btc_price_at_or_before(
                after_dt
            )

            if price_before is None or price_after is None:
                stats["skipped_missing_price"] += 1
                continue

            try:
                btc_return = self.calculate_reaction(
                    price_before,
                    price_after,
                )
            except ValueError:
                stats["skipped_missing_price"] += 1
                continue

            rows_to_insert.append(
                {
                    "regime_id": regime_id,
                    "event_type": mapped_type,
                    "event_date": event_day,
                    "btc_price_before": price_before,
                    "btc_price_after": price_after,
                    "btc_return": btc_return,
                }
            )

        if not rows_to_insert:
            logger.info(
                "RegimeEventService: %d event(s) scanned, no new "
                "rows to insert (existing=%d, missing_price=%d, "
                "unmapped=%d)",
                stats["events_scanned"],
                stats["skipped_existing"],
                stats["skipped_missing_price"],
                stats["skipped_unmapped_type"],
            )
            return stats

        try:
            stats["rows_inserted"] = (
                self.events.create_event_analysis_many(
                    rows_to_insert
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception(
                "RegimeEventService: batch insert failed; "
                "rolled back"
            )
            raise

        logger.info(
            "RegimeEventService: inserted %d row(s) for "
            "regime_id=%s (scanned=%d, existing=%d, "
            "missing_price=%d, unmapped=%d)",
            stats["rows_inserted"],
            regime_id,
            stats["events_scanned"],
            stats["skipped_existing"],
            stats["skipped_missing_price"],
            stats["skipped_unmapped_type"],
        )

        return stats

    # ============================================================
    # PRIVATE HELPERS
    # ============================================================

    def _recent_events(
        self,
        lookback_days: int,
    ) -> list:
        """
        Return candidate economic_events for reaction analysis.

        Filters:
            - event_date >= now - lookback_days
            - event_date <= now - EVENT_WINDOW_HOURS
              (so the "after" price exists)
            - impact_level in _IMPACT_LEVELS

        Loaded lazily to avoid a top-level import cycle risk.
        """

        from app.models.economic_event import EconomicEvent

        now = datetime.now(timezone.utc)
        earliest = now - timedelta(days=lookback_days)
        latest = now - timedelta(hours=_EVENT_WINDOW_HOURS)

        return (
            self.db.query(EconomicEvent)
            .filter(
                EconomicEvent.event_date >= earliest,
                EconomicEvent.event_date <= latest,
                EconomicEvent.impact_level.in_(
                    _IMPACT_LEVELS
                ),
            )
            .order_by(EconomicEvent.event_date.asc())
            .all()
        )

    def _get_btc_price_at_or_before(
        self,
        dt: datetime,
    ) -> float | None:
        """
        PIT lookup: the price of the last btc_prices tick with
        time <= dt.

        Returns None if no such tick exists (the raw table has
        no history old enough).
        """

        from app.models.btc_price import BTCPrice

        row = (
            self.db.query(BTCPrice.price)
            .filter(BTCPrice.time <= dt)
            .order_by(BTCPrice.time.desc())
            .first()
        )

        if row is None:
            return None

        return float(row[0])

    @staticmethod
    def _normalize_event_type(
        raw: str | None,
    ) -> str | None:
        """
        Map economic_events.event_type to the
        regime_event_analysis vocabulary.

        Returns None if the raw type has no mapping.
        """

        if not raw:
            return None

        return _EVENT_TYPE_MAP.get(raw.lower())