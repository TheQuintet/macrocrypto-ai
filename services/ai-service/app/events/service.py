"""Service layer for the events endpoint (A5.4).

Wraps the read path for ``GET /api/v1/events/historical`` in one
place so the router stays a thin HTTP layer. The service:

    1. Opens a session via ``session_scope()``.
    2. Reads event rows with ``EventImpactRepository``, applying
       the caller's filters.
    3. Aggregates the rows with ``aggregate_by_type`` (the pure
       layer from A5.3), so the metrics reflect exactly the rows
       that were returned — not a separate DB query that could
       drift.
    4. Returns a plain dict shaped for the endpoint's response
       schema.

The service does not do HTTP. It raises only:
    - ``ValueError`` for filter combinations it can detect as
      invalid (start_date > end_date), which the router turns
      into a 422.
    - Whatever the repository raises on a database failure,
      which the router turns into a 500.

Filter semantics
----------------
``event_type`` filters by canonical type. Since the canonical key
is derived (not stored) — the DB stores free-form ``event_name``
— the filter is applied **after** reading, using
``normalize_event_type`` on each row. This means an unfiltered
read is required to apply the type filter; the row count is
bounded by ``limit``.

``start_date`` and ``end_date`` are inclusive and are applied at
the SQL level via ``EventImpactRepository.fetch_by_date_range``,
so the DB does the range narrowing.

When both a date range and an event_type filter are present, the
date range goes to the DB and the type filter is applied in
memory on the returned rows.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.engine import session_scope
from app.database.repositories.event_impact_repository import (
    EventImpactRepository,
)
from app.events.metrics import (
    MIN_EVENTS_FOR_METRICS,
    aggregate_by_type,
    normalize_event_type,
)

logger = logging.getLogger(__name__)


#: Default row cap for an events read. Matches the repository's
#: own default and keeps the response bounded.
DEFAULT_EVENT_LIMIT: int = 1000


async def fetch_historical_events(
    *,
    event_type: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = DEFAULT_EVENT_LIMIT,
) -> Dict[str, Any]:
    """Read event rows, apply filters, aggregate, and return a dict.

    Args:
        event_type: Optional list of canonical event types to
            include. Values are matched against
            ``normalize_event_type(row["event_name"])``. An empty
            list is treated as "no filter".
        start_date: Optional inclusive lower bound on ``event_date``.
        end_date: Optional inclusive upper bound on ``event_date``.
        limit: Maximum rows to read from the DB.

    Returns:
        A dict with keys ``events``, ``by_type``, ``unmapped_names``,
        ``insufficient``, ``count``, ``generated_at``. The router
        maps this to ``EventsResponse``.

    Raises:
        ValueError: If ``start_date`` is later than ``end_date``.
    """
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise ValueError(
                f"start_date {start_date} is after end_date {end_date}"
            )

    async with session_scope() as session:
        repo = EventImpactRepository(session)

        # ---- 1. Read rows, narrowing by date range at the SQL level ----
        if start_date is not None and end_date is not None:
            rows = await repo.fetch_by_date_range(
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        else:
            rows = await repo.fetch_all(limit=limit)

        # ---- 2. Apply the event_type filter in memory ----
        # The canonical key is derived, not stored, so the filter
        # cannot be pushed to SQL. The row count is bounded by
        # `limit`, so this is a linear pass over a bounded list.
        if event_type:
            wanted = set(event_type)
            rows = [
                r for r in rows
                if normalize_event_type(r["event_name"]) in wanted
            ]

    # ---- 3. Aggregate the filtered rows ----
    # Note: aggregation uses exactly the rows the response returns,
    # so `by_type` and `events` are always consistent.
    by_type, unmapped, insufficient = aggregate_by_type(rows)

    return {
        "generated_at": datetime.now(timezone.utc),
        "count": len(rows),
        "events": rows,
        "by_type": by_type,
        "unmapped_names": unmapped,
        "insufficient": insufficient,
    }


__all__ = ["DEFAULT_EVENT_LIMIT", "fetch_historical_events"]