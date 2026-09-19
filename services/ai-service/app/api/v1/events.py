"""Events API router (A5.4).

Exposes:
    - GET /api/v1/events/historical

Returns historical macro events with their BTC reactions plus
per-event-type aggregate metrics, in one payload:

    - ``events``: the per-event rows (A5.2), newest first.
    - ``by_type``: per-type aggregates (A5.3) — mean change, mean
      volatility, direction frequencies, min/max, confidence
      interval.
    - ``unmapped_names``: free-form names that did not match a
      canonical event type.
    - ``insufficient``: types with fewer than the minimum number
      of events required for aggregation.

Design:
    - The HTTP layer stays thin. Reading rows, filtering, and
      aggregating all live in ``app.events.service``, which this
      router calls. The router only validates query params and
      shapes the response.
    - ``event_type`` is validated manually against
      ``CANONICAL_EVENT_TYPES``, matching the pattern the
      correlation and predict endpoints use for manually-validated
      query parameters (Handoff §8.7).
    - ``start_date`` and ``end_date`` are parsed by FastAPI as
      ``date``; the only extra validation is that start <= end,
      which the service raises as ``ValueError`` and this router
      converts to a 422.
    - Empty results return 200 with an empty ``events`` list, not
      404. A filter that matches nothing is a valid query with an
      empty answer.
    - Redis caching is best-effort: a cache failure logs a warning
      and falls through to the service, never breaks the response.
      Matches Handoff §8.4.
    - No JWT auth (deferred, same as every other AI Service
      endpoint).
    - No rate limiting (deferred, same as every other AI Service
      endpoint).
"""

import json
import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.cache.redis_client import get_redis
from app.events.metrics import CANONICAL_EVENT_TYPES
from app.events.service import fetch_historical_events
from app.schemas.events import (
    EventResponse,
    EventTypeMetricsResponse,
    EventsErrorResponse,
    EventsFilters,
    EventsResponse,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
#: Cache TTL for the events response, in seconds. Keeps the
#: endpoint under its 500ms target for repeat calls without
#: serving stale data for more than a minute.
CACHE_TTL_SECONDS: int = 60

#: Cache key prefix. Includes the service name to avoid collisions
#: if the Redis instance is shared.
CACHE_KEY_PREFIX: str = "ai-service:events:historical"


# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/v1/events",
    tags=["events"],
)


# ============================================================
# HELPERS
# ============================================================
def _validate_event_types(event_type: Optional[List[str]]) -> Optional[List[str]]:
    """Validate the ``event_type`` query parameter.

    FastAPI parses repeated ``?event_type=`` params into a list.
    Each value must be one of ``CANONICAL_EVENT_TYPES``. Unknown
    values raise 422, matching the manual-validation pattern used
    elsewhere in the service.

    Args:
        event_type: The raw list from the query string, or None.

    Returns:
        The same list, unchanged, when all values are valid.

    Raises:
        HTTPException: 422 when any value is not a canonical type.
    """
    if not event_type:
        return None
    invalid = [v for v in event_type if v not in CANONICAL_EVENT_TYPES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "invalid_event_type",
                "message": (
                    f"Invalid event_type value(s) {invalid}. "
                    f"Must be one of {list(CANONICAL_EVENT_TYPES)}."
                ),
            },
        )
    return event_type


def _cache_key(
    event_type: Optional[List[str]],
    start_date: Optional[date],
    end_date: Optional[date],
) -> str:
    """Build a deterministic cache key from the filter tuple.

    Sorting the event-type list keeps ``?event_type=fed&event_type=cpi``
    and ``?event_type=cpi&event_type=fed`` on the same key.
    """
    types_part = ",".join(sorted(event_type)) if event_type else "-"
    start_part = start_date.isoformat() if start_date else "-"
    end_part = end_date.isoformat() if end_date else "-"
    return f"{CACHE_KEY_PREFIX}:{types_part}:{start_part}:{end_part}"


async def _read_cache(key: str) -> Optional[Dict[str, Any]]:
    """Best-effort cache read.

    Returns the parsed payload on hit, or None on miss or on any
    Redis failure. Never raises.
    """
    try:
        client = await get_redis()
        if client is None:
            return None
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:  # noqa: BLE001 — best-effort
        logger.warning(f"Events cache read failed for {key}: {e}")
        return None


async def _write_cache(key: str, payload: Dict[str, Any]) -> None:
    """Best-effort cache write. Never raises.

    Payloads that fail to serialize are dropped with a warning —
    the endpoint already has its response, caching is a bonus.
    """
    try:
        client = await get_redis()
        if client is None:
            return
        # The payload was built with model_dump(mode="json"), so
        # every value is JSON-serializable by construction. The
        # try/except is defense in depth.
        await client.set(key, json.dumps(payload), ex=CACHE_TTL_SECONDS)
    except Exception as e:  # noqa: BLE001 — best-effort
        logger.warning(f"Events cache write failed for {key}: {e}")


def _build_response(
    payload: Dict[str, Any],
    *,
    event_type: Optional[List[str]],
    start_date: Optional[date],
    end_date: Optional[date],
) -> EventsResponse:
    """Turn the service's dict into an ``EventsResponse``.

    The service returns rows as plain dicts (whatever the
    repository produced) and metrics as ``EventTypeMetrics``
    dataclasses. This function maps both to their response
    schemas.
    """
    events = [EventResponse(**row) for row in payload["events"]]
    by_type = {
        k: EventTypeMetricsResponse(**v.to_dict())
        for k, v in payload["by_type"].items()
    }
    return EventsResponse(
        generated_at=payload["generated_at"],
        count=payload["count"],
        filters=EventsFilters(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
        ),
        events=events,
        by_type=by_type,
        unmapped_names=payload["unmapped_names"],
        insufficient=payload["insufficient"],
    )


# ============================================================
# ENDPOINT
# ============================================================
@router.get(
    "/historical",
    response_model=EventsResponse,
    responses={
        422: {
            "model": EventsErrorResponse,
            "description": "Invalid query parameters.",
        },
    },
    summary="Get historical events and their BTC reactions",
    description=(
        "Return historical macro events with the BTC price reaction "
        "around each one, plus per-event-type aggregate metrics.\n\n"
        "Filter by one or more canonical event types with repeatable "
        "`?event_type=` parameters (`fed`, `cpi`, `gdp`, "
        "`employment`). Filter by date range with `start_date` and "
        "`end_date` (inclusive, ISO 8601).\n\n"
        "The `events` list contains the per-event rows, newest "
        "first. The `by_type` map contains aggregates computed from "
        "exactly the returned rows — mean change, mean volatility, "
        "direction frequencies, min/max changes, and a confidence "
        "interval. Types with fewer than three events are reported "
        "in `insufficient` rather than aggregated.\n\n"
        "Empty results return 200 with an empty `events` list."
    ),
)
async def get_historical_events(
    event_type: Optional[List[str]] = Query(
        default=None,
        description=(
            "Canonical event type to include. Repeatable: "
            "`?event_type=fed&event_type=cpi`. Values must be one "
            f"of {list(CANONICAL_EVENT_TYPES)}."
        ),
    ),
    start_date: Optional[date] = Query(
        default=None,
        description=(
            "Inclusive lower bound on event date (ISO 8601, "
            "e.g. 2024-01-01)."
        ),
    ),
    end_date: Optional[date] = Query(
        default=None,
        description=(
            "Inclusive upper bound on event date (ISO 8601, "
            "e.g. 2024-12-31)."
        ),
    ),
) -> EventsResponse:
    """Return historical events and per-type metrics.

    Args:
        event_type: Optional list of canonical event types.
        start_date: Optional inclusive lower bound on event date.
        end_date: Optional inclusive upper bound on event date.

    Returns:
        EventsResponse with the filtered events and their
        aggregates.

    Raises:
        HTTPException: 422 when an event_type value is invalid or
            when start_date is later than end_date.
    """
    logger.info(
        f"GET /api/v1/events/historical "
        f"(event_type={event_type}, "
        f"start_date={start_date}, end_date={end_date})"
    )

    # ---- 0. Validate query params ----
    event_type = _validate_event_types(event_type)
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "invalid_date_range",
                "message": (
                    f"start_date {start_date} is after "
                    f"end_date {end_date}"
                ),
            },
        )

    # ---- 1. Try the cache ----
    key = _cache_key(event_type, start_date, end_date)
    cached = await _read_cache(key)
    if cached is not None:
        logger.info(f"Events cache hit for {key}")
        return _build_response(
            cached,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
        )

    # ---- 2. Miss — call the service ----
    try:
        payload = await fetch_historical_events(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as e:
        # Defensive: the router already validates date order, but
        # the service is the source of truth. Convert to 422.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "invalid_filter",
                "message": str(e),
            },
        )

    # ---- 3. Build the response, then cache it ----
    response = _build_response(
        payload,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )
    await _write_cache(key, response.model_dump(mode="json"))

    logger.info(
        f"Returning {response.count} events, "
        f"{len(response.by_type)} types, "
        f"{len(response.insufficient)} insufficient, "
        f"{len(response.unmapped_names)} unmapped"
    )

    return response


__all__ = ["router"]