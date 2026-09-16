"""Event impact aggregation metrics (A5.3).

Given the per-event rows produced by A5.2's ``ReactionCalculator``
and persisted in ``historical_event_impacts``, compute per-event-type
summary statistics: average price change, average volatility,
direction frequencies, min/max changes, and confidence intervals on
the mean.

Two-layer design
----------------
This module follows the same shape as ``app.events.reaction`` and
``app.correlation.calculator``:

1. **Pure functions** at module level. No I/O. Trivially testable.
   They take a list of row-like objects (dicts or dataclasses) and
   return numbers or small dataclasses. Anything invalid raises
   ``ValueError``; anything insufficient returns ``None`` so the
   caller can record a skip.

2. **Orchestrator** (``EventMetricsCalculator``) that owns the async
   repository reads and iterates the pure functions. It reads
   ``historical_event_impacts`` via ``EventImpactRepository`` — the
   read methods A5.1 shipped — and never writes.

Event type normalization
------------------------
A5.2 stores free-form ``event_name`` values ("FOMC", "CPI Release",
"Non-Farm Payrolls"). A5.3's acceptance criteria refer to event
*types* ("Fed", "CPI", "GDP", "Employment"). This module owns the
mapping from free-form names to canonical type keys via
``EVENT_TYPE_ALIASES``. Unmapped names normalize to their own
lowercased, whitespace-collapsed form so that, for example, three
events all named "ECB Rate Decision" aggregate together even though
the type is not in the canonical set.

Metrics computed
----------------
For each canonical type with at least ``MIN_EVENTS_FOR_METRICS``
events:

* ``n_events``           — sample size
* ``mean_change``        — arithmetic mean of ``price_change_percent``
* ``mean_volatility``    — arithmetic mean of ``volatility``
* ``direction_frequencies`` — fraction of rows in each direction
* ``min_change``, ``max_change`` — extremes of ``price_change_percent``
* ``mean_change_ci``     — two-sided confidence interval on the mean
* ``confidence_level``   — the level used for the interval (0.95)

All percentages are in percent, matching the stored columns and the
``volatility_pct`` units from A5.2.

Confidence interval
-------------------
Two-sided CI on the mean using the t-distribution, which degenerates
to the normal for large n and widens correctly for small n. This
matches ``app.correlation.calculator``'s convention, which also uses
``scipy.stats``. The chosen level is ``CONFIDENCE_LEVEL = 0.95``.

If the sample has zero variance (all changes identical), the CI is
the point itself: ``(mean, mean)``. This is what the t-interval
formula yields when the standard error is zero, and it is the
mathematically correct answer — there is no uncertainty about the
mean when every observation is the same.

Storage
-------
Metrics are computed **on the fly** from ``historical_event_impacts``.
No new table is introduced. If the row count ever becomes a
performance concern, a follow-up branch can add a materialized view;
A5.4's endpoint will call this module per request and can layer
caching on top without changing the calculator.
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from scipy import stats as _scipy_stats

from app.database.repositories.event_impact_repository import (
    EventImpactRepository,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Minimum number of events of a given type required to publish
#: aggregate metrics. Below this, per-type statistics are noise.
MIN_EVENTS_FOR_METRICS: int = 3

#: Confidence level for the interval on the mean. Two-sided.
CONFIDENCE_LEVEL: float = 0.95

#: Canonical event-type keys this module recognizes. Rows whose
#: ``event_name`` does not map to one of these are grouped under
#: their own normalized name; they are still aggregated, just not
#: under a canonical label.
CANONICAL_EVENT_TYPES: Tuple[str, ...] = (
    "fed",
    "cpi",
    "gdp",
    "employment",
)

#: Free-form event names (lowercased) → canonical type key.
#: Matching is done after lowercasing and whitespace collapsing,
#: so "FOMC" and "fomc" both match. Unknown names fall through to
#: ``normalize_event_type``'s default behavior.
EVENT_TYPE_ALIASES: Dict[str, str] = {
    # Federal Reserve / FOMC
    "fomc": "fed",
    "fed": "fed",
    "federal reserve": "fed",
    "fomc meeting": "fed",
    "fomc decision": "fed",
    "fed decision": "fed",
    # CPI / inflation
    "cpi": "cpi",
    "cpi release": "cpi",
    "cpi report": "cpi",
    "inflation": "cpi",
    "inflation report": "cpi",
    "inflation rate": "cpi",
    # GDP
    "gdp": "gdp",
    "gdp release": "gdp",
    "gdp report": "gdp",
    "gross domestic product": "gdp",
    # Employment
    "nfp": "employment",
    "non-farm payrolls": "employment",
    "nonfarm payrolls": "employment",
    "employment": "employment",
    "employment report": "employment",
    "jobs report": "employment",
    "unemployment": "employment",
    "unemployment rate": "employment",
}


# ---------------------------------------------------------------------------
# Event-type normalization
# ---------------------------------------------------------------------------


def normalize_event_type(event_name: str) -> str:
    """Map a free-form event name to a canonical type key.

    Lowercases and collapses internal whitespace, then looks the
    result up in ``EVENT_TYPE_ALIASES``. If there is no match, the
    normalized name itself is returned — so a set of events all
    named "ECB Rate Decision" aggregates together under the key
    ``"ecb rate decision"`` even though it is not one of the
    canonical types.

    Empty or whitespace-only input raises ``ValueError``: an event
    with no name cannot be grouped.

    Args:
        event_name: The free-form name as stored in
            ``historical_event_impacts.event_name``.

    Returns:
        A canonical type key (one of ``CANONICAL_EVENT_TYPES``), or
        the normalized free-form name.

    Raises:
        ValueError: If ``event_name`` is empty or whitespace only.
    """
    if event_name is None:
        raise ValueError("event_name must not be None")
    key = " ".join(str(event_name).lower().split())
    if not key:
        raise ValueError("event_name must not be empty")
    return EVENT_TYPE_ALIASES.get(key, key)


# ---------------------------------------------------------------------------
# Small row-access helper
# ---------------------------------------------------------------------------


def _get(row: Any, name: str, default: Any = None) -> Any:
    """Read a field from a dict-like or object-like row.

    The repository's read methods return dicts (``result.mappings()``),
    but the pure functions here are also used against the
    ``EventImpactRow`` dataclass in tests. This helper hides the
    difference.
    """
    if isinstance(row, dict):
        return row.get(name, default)
    return getattr(row, name, default)


# ---------------------------------------------------------------------------
# Pure aggregation functions
# ---------------------------------------------------------------------------


def mean_change(rows: Iterable[Any]) -> float:
    """Arithmetic mean of ``price_change_percent`` across rows.

    Args:
        rows: Iterable of row-like objects with a
            ``price_change_percent`` field.

    Returns:
        The mean, in percent.

    Raises:
        ValueError: If ``rows`` is empty.
    """
    values = [float(_get(r, "price_change_percent")) for r in rows]
    if not values:
        raise ValueError("mean_change requires at least one row")
    return statistics.fmean(values)


def mean_volatility(rows: Iterable[Any]) -> float:
    """Arithmetic mean of ``volatility`` across rows.

    Args:
        rows: Iterable of row-like objects with a ``volatility``
            field.

    Returns:
        The mean, in percent.

    Raises:
        ValueError: If ``rows`` is empty.
    """
    values = [float(_get(r, "volatility")) for r in rows]
    if not values:
        raise ValueError("mean_volatility requires at least one row")
    return statistics.fmean(values)


def direction_frequencies(rows: Iterable[Any]) -> Dict[str, float]:
    """Fraction of rows in each direction.

    Returns a dict with keys ``"up"``, ``"down"``, and
    ``"neutral"``, even if a given key's frequency is zero. The
    three values sum to 1.0 (subject to floating-point rounding).

    Args:
        rows: Iterable of row-like objects with a ``direction``
            field. Values other than ``"up"``, ``"down"``, or
            ``"neutral"`` are ignored — they are not counted
            toward any bucket, so the sum can be less than 1.0 in
            that case. (This is defensive: the A5.1 CHECK
            constraint prevents such rows from existing.)

    Returns:
        Dict mapping direction to fraction.

    Raises:
        ValueError: If ``rows`` is empty.
    """
    materialized = list(rows)
    if not materialized:
        raise ValueError(
            "direction_frequencies requires at least one row"
        )
    total = len(materialized)
    counts: Dict[str, int] = {"up": 0, "down": 0, "neutral": 0}
    for row in materialized:
        direction = _get(row, "direction")
        if direction in counts:
            counts[direction] += 1
    return {k: v / total for k, v in counts.items()}


def min_max_change(rows: Iterable[Any]) -> Tuple[float, float]:
    """Return ``(min, max)`` of ``price_change_percent`` across rows.

    Args:
        rows: Iterable of row-like objects with a
            ``price_change_percent`` field.

    Returns:
        Tuple of (minimum, maximum), both in percent.

    Raises:
        ValueError: If ``rows`` is empty.
    """
    values = [float(_get(r, "price_change_percent")) for r in rows]
    if not values:
        raise ValueError("min_max_change requires at least one row")
    return (min(values), max(values))


def confidence_interval(
    values: Iterable[float],
    *,
    confidence: float = CONFIDENCE_LEVEL,
) -> Tuple[float, float]:
    """Two-sided confidence interval on the mean of ``values``.

    Uses the t-distribution, which is correct for small samples and
    converges to the normal as n grows. For n == 1, returns the
    point itself (``(v, v)``) — there is no information about
    spread from a single observation, and the t-interval is
    undefined. For zero-variance samples (all values equal), also
    returns ``(v, v)``: the standard error is zero, so there is no
    uncertainty about the mean.

    Args:
        values: Iterable of floats.
        confidence: Two-sided confidence level in (0, 1). Defaults
            to ``CONFIDENCE_LEVEL``.

    Returns:
        Tuple ``(lower, upper)``.

    Raises:
        ValueError: If ``values`` is empty, or if ``confidence``
            is not in the open interval ``(0, 1)``.
    """
    if not 0.0 < confidence < 1.0:
        raise ValueError(
            f"confidence must be in (0, 1), got {confidence}"
        )
    arr = [float(v) for v in values]
    if not arr:
        raise ValueError(
            "confidence_interval requires at least one value"
        )
    if len(arr) == 1:
        return (arr[0], arr[0])

    mean = statistics.fmean(arr)
    stderr = statistics.stdev(arr) / math.sqrt(len(arr))
    if stderr == 0.0:
        return (mean, mean)

    # Two-sided interval: split the tail probability.
    alpha = 1.0 - confidence
    t_crit = _scipy_stats.t.ppf(1.0 - alpha / 2.0, df=len(arr) - 1)
    half_width = t_crit * stderr
    return (mean - half_width, mean + half_width)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class EventTypeMetrics:
    """Aggregate metrics for one event type.

    Attributes:
        event_type: The canonical type key ("fed", "cpi", ...) or a
            normalized free-form name when the type is not in
            ``CANONICAL_EVENT_TYPES``.
        n_events: Number of events aggregated.
        mean_change: Mean ``price_change_percent``, in percent.
        mean_volatility: Mean ``volatility``, in percent.
        direction_frequencies: Fraction of rows in each direction,
            keys ``"up"``, ``"down"``, ``"neutral"``.
        min_change: Minimum ``price_change_percent``.
        max_change: Maximum ``price_change_percent``.
        mean_change_ci: Two-sided confidence interval on
            ``mean_change``.
        confidence_level: The level used for the interval.
    """

    event_type: str
    n_events: int
    mean_change: float
    mean_volatility: float
    direction_frequencies: Dict[str, float]
    min_change: float
    max_change: float
    mean_change_ci: Tuple[float, float]
    confidence_level: float = CONFIDENCE_LEVEL

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "event_type": self.event_type,
            "n_events": self.n_events,
            "mean_change": self.mean_change,
            "mean_volatility": self.mean_volatility,
            "direction_frequencies": dict(self.direction_frequencies),
            "min_change": self.min_change,
            "max_change": self.max_change,
            "mean_change_ci": list(self.mean_change_ci),
            "confidence_level": self.confidence_level,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"EventTypeMetrics(event_type={self.event_type!r}, "
            f"n_events={self.n_events}, "
            f"mean_change={self.mean_change:+.2f}%, "
            f"mean_volatility={self.mean_volatility:.4f})"
        )


@dataclass
class MetricsCalculationResult:
    """Rollup result for one aggregation pass over all event types.

    Attributes:
        calculated_at: When the pass started.
        by_type: Mapping from event type to its ``EventTypeMetrics``.
        unmapped_names: Free-form event names seen that did not map
            to a canonical type. Informational — those rows were
            still aggregated under their normalized name.
        insufficient: Types with fewer than
            ``MIN_EVENTS_FOR_METRICS`` events. Included so the
            caller can log them without inspecting ``by_type``.
        total_rows: Total number of rows considered.
        elapsed_seconds: Wall-clock duration of the pass.
    """

    calculated_at: datetime
    by_type: Dict[str, EventTypeMetrics] = field(default_factory=dict)
    unmapped_names: List[str] = field(default_factory=list)
    insufficient: List[str] = field(default_factory=list)
    total_rows: int = 0
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable summary."""
        return {
            "calculated_at": self.calculated_at.isoformat(),
            "total_rows": self.total_rows,
            "by_type": {
                k: v.to_dict() for k, v in self.by_type.items()
            },
            "unmapped_names": list(self.unmapped_names),
            "insufficient": list(self.insufficient),
            "elapsed_seconds": self.elapsed_seconds,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"MetricsCalculationResult(types={len(self.by_type)}, "
            f"insufficient={len(self.insufficient)}, "
            f"total_rows={self.total_rows})"
        )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_event_type(
    event_type: str,
    rows: List[Any],
) -> Optional[EventTypeMetrics]:
    """Aggregate one event type's rows, or return ``None`` if
    the sample is too small.

    Args:
        event_type: The canonical type key (output of
            ``normalize_event_type``).
        rows: The rows belonging to this type.

    Returns:
        An ``EventTypeMetrics``, or ``None`` if ``len(rows) <
        MIN_EVENTS_FOR_METRICS``.
    """
    if len(rows) < MIN_EVENTS_FOR_METRICS:
        return None

    changes = [float(_get(r, "price_change_percent")) for r in rows]
    return EventTypeMetrics(
        event_type=event_type,
        n_events=len(rows),
        mean_change=mean_change(rows),
        mean_volatility=mean_volatility(rows),
        direction_frequencies=direction_frequencies(rows),
        min_change=min_max_change(rows)[0],
        max_change=min_max_change(rows)[1],
        mean_change_ci=confidence_interval(
            changes, confidence=CONFIDENCE_LEVEL
        ),
        confidence_level=CONFIDENCE_LEVEL,
    )


def aggregate_by_type(
    rows: Iterable[Any],
) -> Tuple[Dict[str, EventTypeMetrics], List[str], List[str]]:
    """Group rows by canonical event type and aggregate each group.

    Args:
        rows: Iterable of row-like objects with ``event_name`` and
            the numeric fields the aggregators read.

    Returns:
        A tuple ``(by_type, unmapped_names, insufficient)``:

        * ``by_type``: dict from canonical type key to
          ``EventTypeMetrics``. Types with fewer than
          ``MIN_EVENTS_FOR_METRICS`` rows are omitted.
        * ``unmapped_names``: sorted unique free-form event names
          seen that did not match ``EVENT_TYPE_ALIASES``.
        * ``insufficient``: sorted type keys whose group size was
          below the minimum, and thus omitted from ``by_type``.
    """
    groups: Dict[str, List[Any]] = {}
    unmapped: set = set()

    for row in rows:
        raw_name = _get(row, "event_name")
        if raw_name is None:
            # Defensive: A5.1 prevents this, but skip rather than
            # crash if a hand-inserted row leaks through.
            continue
        key = normalize_event_type(raw_name)
        groups.setdefault(key, []).append(row)
        # Track free-form names not in the alias table. Note that
        # keys equal to one of the canonical names are not
        # "unmapped" — they are aliases.
        if key not in CANONICAL_EVENT_TYPES and key not in EVENT_TYPE_ALIASES:
            unmapped.add(str(raw_name))

    by_type: Dict[str, EventTypeMetrics] = {}
    insufficient: List[str] = []
    for key, group_rows in groups.items():
        metrics = aggregate_event_type(key, group_rows)
        if metrics is None:
            insufficient.append(key)
        else:
            by_type[key] = metrics

    return by_type, sorted(unmapped), sorted(insufficient)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class EventMetricsCalculator:
    """Compute per-event-type aggregate metrics from stored rows.

    The calculator reads ``historical_event_impacts`` via the
    injected ``EventImpactRepository``, groups the rows by canonical
    event type, aggregates each group, and returns a
    ``MetricsCalculationResult``. It never writes.

    Metrics are computed on the fly — no metrics table exists. A
    caller that needs the same metrics repeatedly (A5.4's endpoint,
    A5.5's job) can layer caching on top without changing this
    class.

    Example:
        async with session_scope() as session:
            calc = EventMetricsCalculator(
                event_impact_repo=EventImpactRepository(session),
            )
            result = await calc.run()
            for event_type, metrics in result.by_type.items():
                print(event_type, metrics.mean_change)

    Args:
        event_impact_repo: Repository providing read access to
            ``historical_event_impacts``.
    """

    def __init__(
        self,
        event_impact_repo: EventImpactRepository,
    ) -> None:
        self.event_impact_repo = event_impact_repo

    async def run(
        self,
        *,
        impact_level: Optional[str] = None,
        limit: int = 1000,
    ) -> MetricsCalculationResult:
        """Aggregate metrics for all event types in the repository.

        Args:
            impact_level: Optional filter. When set, only rows with
                this ``impact_level`` are considered.
            limit: Maximum number of rows to read. Defaults to
                1000, matching the repository's own default.

        Returns:
            A ``MetricsCalculationResult`` with one
            ``EventTypeMetrics`` per type that met the minimum
            sample size, plus the lists of unmapped names and
            insufficient types.
        """
        started = datetime.now(timezone.utc)

        rows = await self.event_impact_repo.fetch_all(
            impact_level=impact_level,
            limit=limit,
        )

        by_type, unmapped, insufficient = aggregate_by_type(rows)

        finished = datetime.now(timezone.utc)
        result = MetricsCalculationResult(
            calculated_at=started,
            by_type=by_type,
            unmapped_names=unmapped,
            insufficient=insufficient,
            total_rows=len(rows),
            elapsed_seconds=(finished - started).total_seconds(),
        )

        logger.info(
            f"Event metrics aggregation complete: "
            f"{len(by_type)} types, "
            f"{len(insufficient)} insufficient, "
            f"{len(unmapped)} unmapped, "
            f"{len(rows)} rows, "
            f"in {result.elapsed_seconds:.3f}s"
        )

        return result


__all__ = [
    "CANONICAL_EVENT_TYPES",
    "CONFIDENCE_LEVEL",
    "EVENT_TYPE_ALIASES",
    "MIN_EVENTS_FOR_METRICS",
    "EventMetricsCalculator",
    "EventTypeMetrics",
    "MetricsCalculationResult",
    "aggregate_by_type",
    "aggregate_event_type",
    "confidence_interval",
    "direction_frequencies",
    "mean_change",
    "mean_volatility",
    "min_max_change",
    "normalize_event_type",
]