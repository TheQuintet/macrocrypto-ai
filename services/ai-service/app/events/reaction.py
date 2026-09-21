"""BTC price reaction calculation for historical events (A5.2).

Given an event (event_name, event_date, impact_level), compute the
BTC price reaction over the 48-hour window centered on the event
date and return an ``EventImpactRow`` ready to be written to the
``historical_event_impacts`` table.

Design:

    - Two layers, matching app.correlation.calculator:
        1. Pure functions: ``price_change_percent``,
           ``volatility_pct``, ``classify_direction``. No I/O.
           Trivially testable.
        2. Orchestrator: ``ReactionCalculator``. Fetches BTC prices
           via PredictionRepository, runs the pure functions, builds
           the rows.
    - Async (repository calls are async).
    - Fails softly: an event with insufficient price data is
      skipped, not raised. Skips are captured in the result object
      so the caller (A5.5's job) can report them in the run summary.
    - Does not commit — the caller controls the transaction.

Data flow:

    For each event:
        1. Compute ``before_time = event_date 00:00 UTC - 24h``
        2. Compute ``after_time  = event_date 00:00 UTC + 24h``
        3. Fetch BTC price nearest ``before_time`` (tolerance: 1h)
        4. Fetch BTC price nearest ``after_time`` (tolerance: 1h)
        5. Fetch the full BTC series in [before_time, after_time]
        6. If any of the three is empty, skip the event
        7. Compute price_change_percent and volatility
        8. Classify direction
        9. Build an EventImpactRow and append to the result

Window definition:

    The reaction window is exactly 48 hours: 24 hours before the
    event's UTC midnight to 24 hours after. This is a policy
    decision, not a magic number, and it lives in this module as
    ``PRICE_WINDOW_HOURS_BEFORE`` and ``PRICE_WINDOW_HOURS_AFTER``
    so a future branch can change it in one place. The A5.2
    acceptance criteria specify 24h on each side, so those are the
    values shipped.

Direction rule:

    direction is classified from the sign of price_change_percent
    with a small deadband: changes whose absolute value is below
    ``DIRECTION_THRESHOLD_PCT`` are classified as "neutral". The
    deadband exists so that a 0.01% move from rounding is not
    labelled "up". The threshold is deliberately small (0.5%) and
    lives in this module as a constant, because no other branch
    needs it. The stored ``price_change_percent`` keeps the exact
    value; only the *label* is affected by the deadband.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.database.repositories.event_impact_repository import (
    EventImpactRow,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Window size on each side of the event's UTC midnight. The A5.2
# acceptance criteria specify 24 hours on each side; the total
# window is therefore 48 hours.
PRICE_WINDOW_HOURS_BEFORE: int = 24
PRICE_WINDOW_HOURS_AFTER: int = 24

# Tolerance for "the price at this exact time". The BTC price
# series is hourly, so an exact match is not guaranteed; the
# repository returns the nearest row within this many hours.
PRICE_LOOKUP_TOLERANCE_HOURS: int = 1

# Direction deadband. A price change whose absolute value is below
# this threshold is classified as "neutral". Chosen small enough
# that any real market move lands on "up" or "down", and large
# enough that floating-point rounding does not produce spurious
# "up"/"down" labels.
DIRECTION_THRESHOLD_PCT: float = 0.5

# The minimum number of BTC price points required for the
# volatility calculation. Standard deviation needs at least two
# samples; we require three to avoid a std of zero being treated
# as a meaningful signal.
MIN_PRICE_POINTS: int = 3


# ============================================================
# RESULT DATACLASSES
# ============================================================
@dataclass
class ReactionSkip:
    """A single skipped event, with the reason.

    Attributes:
        event_name: The event that was skipped.
        event_date: The date of the skipped event.
        reason: Short machine-readable reason (e.g.
            'missing_before_price').
        detail: Optional human-readable detail (e.g. the timestamp
            the lookup was anchored to).
    """

    event_name: str
    event_date: date
    reason: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict."""
        return {
            "event_name": self.event_name,
            "event_date": self.event_date.isoformat(),
            "reason": self.reason,
            "detail": self.detail,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ReactionSkip(event_name={self.event_name!r}, "
            f"event_date={self.event_date}, reason={self.reason!r})"
        )


@dataclass
class ReactionCalculationResult:
    """Structured result of one ``ReactionCalculator.run`` call.

    Attributes:
        calculated_at: The timestamp this run started.
        rows: The ``EventImpactRow`` instances that were built and
            are ready for the caller to persist.
        rows_built: Convenience count of ``rows``. Set after the
            loop, so a caller can log it without touching the list.
        skipped: The ``ReactionSkip`` entries for events that could
            not be processed (missing prices, empty window, etc.).
        errors: Dicts with ``event_name``, ``event_date``, and
            ``error`` for events that raised an unexpected
            exception.
        elapsed_seconds: Wall-clock duration of the run.
    """

    calculated_at: datetime
    rows: List[EventImpactRow] = field(default_factory=list)
    rows_built: int = 0
    skipped: List[ReactionSkip] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable summary.

        ``rows`` is deliberately omitted — the caller already holds
        it, and the full rows may be large. Counts and skip/error
        details are included.
        """
        return {
            "calculated_at": self.calculated_at.isoformat(),
            "rows_built": self.rows_built,
            "skipped": [s.to_dict() for s in self.skipped],
            "errors": list(self.errors),
            "elapsed_seconds": self.elapsed_seconds,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ReactionCalculationResult("
            f"rows={len(self.rows)}, "
            f"skipped={len(self.skipped)}, "
            f"errors={len(self.errors)})"
        )


# ============================================================
# PURE FUNCTIONS
# ============================================================
def price_change_percent(
    price_before: float,
    price_after: float,
) -> float:
    """Compute the percentage change from before to after.

    The result is signed: positive means the price rose, negative
    means it fell. A ``price_before`` of zero or negative is not a
    valid input (BTC prices are always positive) and raises
    ``ValueError``; the caller is expected to have already rejected
    such rows.

    Args:
        price_before: Price at the start of the window.
        price_after: Price at the end of the window.

    Returns:
        Percentage change, e.g. 3.97 for a +3.97% move.

    Raises:
        ValueError: If ``price_before`` is zero or negative.
    """
    if price_before <= 0:
        raise ValueError(
            f"price_before must be positive, got {price_before}"
        )
    return (price_after - price_before) / price_before * 100.0


def volatility_pct(prices: Iterable[float]) -> float:
    """Compute the standard deviation of hourly percentage returns.

    The input is the price series over the reaction window, in time
    order. Percentage returns are computed as the pct_change between
    consecutive prices; the result is the standard deviation of
    those returns, expressed as a percentage (2.1 == 2.1%).

    Units: this function returns PERCENT, not a decimal fraction.
    That matches the migration 010 comment for the ``volatility``
    column ("Standard deviation of percentage returns over the
    window") and keeps the value in the same units as
    ``price_change_percent``.

    The A5.1 schema stores this in the ``volatility`` column, which
    has a non-negative CHECK. Standard deviation is non-negative by
    definition, so the CHECK is always satisfiable.

    Args:
        prices: Ordered sequence of prices (oldest first).

    Returns:
        Standard deviation of percentage returns, as a percent.

    Raises:
        ValueError: If fewer than ``MIN_PRICE_POINTS`` prices are
            provided, or if any price is non-positive.
    """
    arr = list(prices)

    if len(arr) < MIN_PRICE_POINTS:
        raise ValueError(
            f"volatility needs at least {MIN_PRICE_POINTS} prices, "
            f"got {len(arr)}"
        )

    if any(p <= 0 for p in arr):
        raise ValueError(
            "volatility requires all prices to be positive"
        )

    # Percentage returns between consecutive prices.
    returns = [
        (arr[i] - arr[i - 1]) / arr[i - 1] * 100.0
        for i in range(1, len(arr))
    ]

    # Population standard deviation (ddof=0). For a full window
    # of hourly returns this is the natural choice; the choice of
    # ddof is documented here so a future branch can revisit it.
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)

    return variance ** 0.5


def classify_direction(
    change_pct: float,
    *,
    threshold_pct: float = DIRECTION_THRESHOLD_PCT,
) -> str:
    """Classify a price change into up, down, or neutral.

    A change whose absolute value is below ``threshold_pct`` is
    classified as "neutral". Otherwise the sign determines the
    label: positive is "up", negative is "down".

    The threshold exists so that a small move from rounding or
    noise is not labelled as a direction. The exact percentage is
    always stored separately on the row; only the label is affected.

    Args:
        change_pct: The percentage change to classify.
        threshold_pct: The deadband width. Defaults to
            ``DIRECTION_THRESHOLD_PCT``.

    Returns:
        One of "up", "down", "neutral".
    """
    if abs(change_pct) < threshold_pct:
        return "neutral"
    return "up" if change_pct > 0 else "down"


# ============================================================
# CALCULATOR
# ============================================================
class ReactionCalculator:
    """Orchestrates BTC price reaction calculations for events.

    Given a list of events, fetches the BTC price at the start and
    end of each event's 48-hour window, computes the reaction
    metrics, and returns an ``EventImpactRow`` per event that has
    sufficient data.

    The calculator does not commit. The caller is expected to build
    the calculator inside a ``session_scope()`` and write the rows
    via ``EventImpactRepository.save_rows`` before the scope exits.

    Example:
        async with session_scope() as session:
            calc = ReactionCalculator(
                prediction_repo=PredictionRepository(session),
            )
            result = await calc.run(events)
            if result.rows:
                repo = EventImpactRepository(session)
                await repo.save_rows(result.rows)
    """

    def __init__(
        self,
        prediction_repo: PredictionRepository,
        *,
        hours_before: int = PRICE_WINDOW_HOURS_BEFORE,
        hours_after: int = PRICE_WINDOW_HOURS_AFTER,
    ) -> None:
        """Initialize the calculator.

        Args:
            prediction_repo: A PredictionRepository bound to a
                session. Used to fetch BTC prices.
            hours_before: Hours before the event's UTC midnight that
                the reaction window opens. Defaults to 24.
            hours_after: Hours after the event's UTC midnight that
                the reaction window closes. Defaults to 24.

        Raises:
            ValueError: If either window size is not positive.
        """
        if hours_before <= 0:
            raise ValueError(
                f"hours_before must be positive, got {hours_before}"
            )
        if hours_after <= 0:
            raise ValueError(
                f"hours_after must be positive, got {hours_after}"
            )

        self.prediction_repo = prediction_repo
        self.hours_before = hours_before
        self.hours_after = hours_after

        logger.info(
            f"ReactionCalculator initialized "
            f"(window={hours_before}h before, {hours_after}h after)"
        )

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def run(
        self, events: Iterable[Any]
    ) -> ReactionCalculationResult:
        """Run the reaction calculation for a list of events.

        The ``events`` argument is an iterable of anything with
        ``event_name``, ``event_date``, and ``impact_level``
        attributes, or a list of dicts with those keys. The
        calculator only reads those three fields; anything else on
        the input is ignored.

        Args:
            events: Iterable of event specs.

        Returns:
            A ``ReactionCalculationResult`` with the built rows and
            the skip/error lists.
        """
        start = datetime.now(timezone.utc)
        result = ReactionCalculationResult(calculated_at=start)

        for event in events:
            spec = _normalize_event(event)
            if spec is None:
                result.skipped.append(
                    ReactionSkip(
                        event_name=str(
                            _get(event, "event_name", "<unknown>")
                        ),
                        event_date=date.today(),
                        reason="invalid_event_spec",
                        detail=(
                            "event is missing "
                            "event_name/event_date/impact_level"
                        ),
                    )
                )
                continue

            try:
                row = await self._compute_one(
                    event_name=spec["event_name"],
                    event_date=spec["event_date"],
                    impact_level=spec["impact_level"],
                    skipped=result.skipped,
                )
                if row is not None:
                    result.rows.append(row)
            except Exception as e:
                logger.error(
                    f"Failed to compute reaction for "
                    f"{spec['event_name']}/{spec['event_date']}: {e}",
                    exc_info=True,
                )
                result.errors.append(
                    {
                        "event_name": spec["event_name"],
                        "event_date": spec["event_date"].isoformat(),
                        "error": str(e),
                    }
                )

        result.rows_built = len(result.rows)
        result.elapsed_seconds = (
            datetime.now(timezone.utc) - start
        ).total_seconds()

        logger.info(
            f"Reaction calculation complete: "
            f"{result.rows_built} built, "
            f"{len(result.skipped)} skipped, "
            f"{len(result.errors)} errors, "
            f"in {result.elapsed_seconds:.3f}s"
        )

        return result

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================
    async def _compute_one(
        self,
        event_name: str,
        event_date: date,
        impact_level: str,
        skipped: List[ReactionSkip],
    ) -> Optional[EventImpactRow]:
        """Compute the reaction row for one event.

        On any skip condition, appends a ``ReactionSkip`` to
        ``skipped`` and returns None. On success, returns an
        ``EventImpactRow``.

        Args:
            event_name: The event's name.
            event_date: The event's calendar date.
            impact_level: The event's classified significance.
            skipped: A list to append skip reasons to.

        Returns:
            An ``EventImpactRow`` on success, or None when skipped.
        """
        # ---- 1. Compute the window boundaries ----
        event_midnight = datetime.combine(
            event_date, time(0, 0), tzinfo=timezone.utc
        )
        before_time = event_midnight - timedelta(
            hours=self.hours_before
        )
        after_time = event_midnight + timedelta(
            hours=self.hours_after
        )

        # ---- 2. Fetch the two endpoint prices ----
        price_before = await self.prediction_repo.fetch_btc_price_at(
            before_time,
            tolerance_hours=PRICE_LOOKUP_TOLERANCE_HOURS,
        )
        if price_before is None:
            logger.info(
                f"Skipping {event_name}/{event_date}: no BTC price "
                f"within {PRICE_LOOKUP_TOLERANCE_HOURS}h of "
                f"{before_time.isoformat()}"
            )
            skipped.append(
                ReactionSkip(
                    event_name=event_name,
                    event_date=event_date,
                    reason="missing_before_price",
                    detail=before_time.isoformat(),
                )
            )
            return None

        price_after = await self.prediction_repo.fetch_btc_price_at(
            after_time,
            tolerance_hours=PRICE_LOOKUP_TOLERANCE_HOURS,
        )
        if price_after is None:
            logger.info(
                f"Skipping {event_name}/{event_date}: no BTC price "
                f"within {PRICE_LOOKUP_TOLERANCE_HOURS}h of "
                f"{after_time.isoformat()}"
            )
            skipped.append(
                ReactionSkip(
                    event_name=event_name,
                    event_date=event_date,
                    reason="missing_after_price",
                    detail=after_time.isoformat(),
                )
            )
            return None

        # ---- 3. Fetch the full window for volatility ----
        window_df = await self.prediction_repo.fetch_btc_prices_range(
            before_time, after_time
        )

        if window_df is None or window_df.empty:
            logger.info(
                f"Skipping {event_name}/{event_date}: no BTC prices "
                f"in window [{before_time.isoformat()}, "
                f"{after_time.isoformat()}]"
            )
            skipped.append(
                ReactionSkip(
                    event_name=event_name,
                    event_date=event_date,
                    reason="empty_window",
                    detail=(
                        f"{before_time.isoformat()}.."
                        f"{after_time.isoformat()}"
                    ),
                )
            )
            return None

        prices = window_df["close"].tolist()

        if len(prices) < MIN_PRICE_POINTS:
            logger.info(
                f"Skipping {event_name}/{event_date}: only "
                f"{len(prices)} prices in window "
                f"(need >= {MIN_PRICE_POINTS})"
            )
            skipped.append(
                ReactionSkip(
                    event_name=event_name,
                    event_date=event_date,
                    reason="insufficient_window_prices",
                    detail=f"{len(prices)} prices",
                )
            )
            return None

        # ---- 4. Compute the metrics ----
        change = price_change_percent(price_before, price_after)
        volatility = volatility_pct(prices)
        direction = classify_direction(change)

        logger.info(
            f"Computed {event_name}/{event_date}: "
            f"before={price_before:.2f}, after={price_after:.2f}, "
            f"change={change:+.2f}%, volatility={volatility:.4f}, "
            f"direction={direction}"
        )

        # ---- 5. Build the row ----
        return EventImpactRow(
            event_name=event_name,
            event_date=event_date,
            impact_level=impact_level,
            btc_price_before=price_before,
            btc_price_after=price_after,
            price_change_percent=change,
            volatility=volatility,
            direction=direction,
        )


# ============================================================
# INPUT NORMALIZATION
# ============================================================
def _get(event: Any, name: str, default: Any = None) -> Any:
    """Read a field from a dict or object."""
    if isinstance(event, dict):
        return event.get(name, default)
    return getattr(event, name, default)


def _normalize_event(event: Any) -> Optional[Dict[str, Any]]:
    """Normalize an event spec to a dict, or return None if invalid.

    Accepts dicts or objects with ``event_name``, ``event_date``,
    and ``impact_level``. ``event_date`` must be a ``date`` (not a
    ``datetime``); a ``datetime`` is rejected to match the A5.1
    validator's rule.

    Args:
        event: The event spec to normalize.

    Returns:
        A dict with keys ``event_name``, ``event_date``,
        ``impact_level``, or None if the spec is invalid.
    """
    name = _get(event, "event_name")
    event_date = _get(event, "event_date")
    impact_level = _get(event, "impact_level")

    if not name or not str(name).strip():
        return None
    if event_date is None:
        return None
    if not isinstance(event_date, date):
        return None
    if isinstance(event_date, datetime):
        return None
    if not impact_level:
        return None

    return {
        "event_name": str(name),
        "event_date": event_date,
        "impact_level": str(impact_level),
    }


__all__ = [
    "DIRECTION_THRESHOLD_PCT",
    "MIN_PRICE_POINTS",
    "PRICE_LOOKUP_TOLERANCE_HOURS",
    "PRICE_WINDOW_HOURS_AFTER",
    "PRICE_WINDOW_HOURS_BEFORE",
    "ReactionCalculationResult",
    "ReactionCalculator",
    "ReactionSkip",
    "classify_direction",
    "price_change_percent",
    "volatility_pct",
]