"""Correlation API router.

Exposes:
    - GET /api/v1/correlation/btc

Returns the latest BTC-vs-macro correlation per indicator for a
requested rolling window:
    - Pearson correlation coefficient
    - Derived strength (strong / medium / weak) and its display color
    - Derived direction (positive / negative) and its display arrow
    - Two-tailed p-value, significance flag, and confidence level
    - Optionally, a historical series per indicator

Design:
    - Reads from btc_macro_correlation via CorrelationRepository.
    - The display fields (strength_color, direction_arrow,
      is_significant, confidence_level) are populated on-read via
      helpers from `app.correlation.calculator`, so the display
      logic lives in one place and the schema stays a dumb
      container.
    - History is opt-in via ?include_history=true, matching the
      performance endpoint's pattern (M8).
    - Empty results return 200 with an empty entries list, not 404.
      A missing window simply has no rows yet — the caller can
      distinguish "no data" from "bad request".
    - No JWT auth (deferred, same as the other endpoints).
    - No rate limiting (deferred, same as the other endpoints).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query, status

from app.correlation.calculator import (
    confidence_from_p_value,
    derive_significance,
    direction_arrow,
    strength_color,
)
from app.database.engine import session_scope
from app.database.repositories.correlation_repository import (
    CorrelationRepository,
)
from app.schemas.correlation import (
    CorrelationEntry,
    CorrelationErrorResponse,
    CorrelationHistoryPoint,
    CorrelationResponse,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
DEFAULT_WINDOW_DAYS = 90
DEFAULT_HISTORY_LIMIT = 30
MAX_HISTORY_LIMIT = 90
DEFAULT_HISTORY_DAYS = 90
MAX_HISTORY_DAYS = 365

# Valid values for window_days. Validated manually because
# FastAPI's Literal[30, 90, 365] for numeric types is unreliable
# when combined with a separate default= on Query (same class of
# bug we hit for Literal[float] confidence levels in the predict
# endpoint).
VALID_WINDOW_DAYS = (30, 90, 365)


# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/v1/correlation",
    tags=["correlation"],
)


# ============================================================
# HELPERS
# ============================================================
def _build_history_point(row: Dict[str, Any]) -> CorrelationHistoryPoint:
    """Build one CorrelationHistoryPoint from a repository row.

    Rows come from CorrelationRepository.fetch_history() and have
    keys: calculated_at, correlation_coefficient, strength,
    direction, p_value. The display fields are derived from the
    helpers so the derivation rules live in one place.

    Args:
        row: A single history row.

    Returns:
        A populated CorrelationHistoryPoint.
    """
    p_value = row.get("p_value")
    return CorrelationHistoryPoint(
        calculated_at=row["calculated_at"],
        correlation_coefficient=float(row["correlation_coefficient"]),
        strength=row["strength"],
        strength_color=strength_color(row["strength"]),
        direction=row["direction"],
        direction_arrow=direction_arrow(row["direction"]),
        p_value=p_value,
        is_significant=derive_significance(p_value),
        confidence_level=confidence_from_p_value(p_value),
    )


def _build_entry(
    row: Dict[str, Any],
    history: List[CorrelationHistoryPoint],
) -> CorrelationEntry:
    """Build one CorrelationEntry from a repository row.

    Rows come from CorrelationRepository.fetch_latest_per_indicator()
    and have keys: indicator_name, window_days, calculated_at,
    correlation_coefficient, strength, direction, p_value.

    Args:
        row: A single latest-per-indicator row.
        history: The history points to attach (may be empty).

    Returns:
        A populated CorrelationEntry.
    """
    p_value = row.get("p_value")
    return CorrelationEntry(
        indicator_name=row["indicator_name"],
        window_days=int(row["window_days"]),
        correlation_coefficient=float(row["correlation_coefficient"]),
        strength=row["strength"],
        strength_color=strength_color(row["strength"]),
        direction=row["direction"],
        direction_arrow=direction_arrow(row["direction"]),
        p_value=p_value,
        is_significant=derive_significance(p_value),
        confidence_level=confidence_from_p_value(p_value),
        calculated_at=row["calculated_at"],
        history=history,
    )


# ============================================================
# ENDPOINT
# ============================================================
@router.get(
    "/btc",
    response_model=CorrelationResponse,
    responses={
        422: {
            "model": CorrelationErrorResponse,
            "description": "Invalid query parameters.",
        },
    },
    summary="Get BTC-vs-macro correlation metrics",
    description=(
        "Return the latest Pearson correlation between BTC price and "
        "each macroeconomic indicator over a rolling window. For each "
        "indicator, the response includes the raw coefficient, the "
        "derived strength and direction labels with their display "
        "hints (color and arrow), the two-tailed p-value, the "
        "statistical significance flag, and the confidence level.\n\n"
        "Set `include_history=true` to attach a historical series "
        "per indicator (oldest first). `history_days` controls how "
        "far back the series goes; `history_limit` caps the number "
        "of points returned."
    ),
)
async def get_btc_correlation(
    window_days: int = Query(
        default=DEFAULT_WINDOW_DAYS,
        description=(
            "Rolling window length in days: 30, 90, or 365. "
            f"Default {DEFAULT_WINDOW_DAYS}."
        ),
    ),
    include_history: bool = Query(
        default=False,
        description=(
            "When true, attach a `history` array to each entry "
            "containing the historical correlation series for that "
            "(indicator, window), ordered oldest-first."
        ),
    ),
    history_limit: int = Query(
        default=DEFAULT_HISTORY_LIMIT,
        ge=1,
        le=MAX_HISTORY_LIMIT,
        description=(
            f"Maximum number of history points per entry "
            f"(1-{MAX_HISTORY_LIMIT}). Only used when "
            f"include_history=true. The most recent N points are "
            f"returned."
        ),
    ),
    history_days: int = Query(
        default=DEFAULT_HISTORY_DAYS,
        ge=1,
        le=MAX_HISTORY_DAYS,
        description=(
            f"How far back the history series extends, in days "
            f"(1-{MAX_HISTORY_DAYS}). Only used when "
            f"include_history=true."
        ),
    ),
) -> CorrelationResponse:
    """Return the latest BTC-vs-macro correlation metrics.

    Args:
        window_days: Rolling window length (30, 90, or 365).
        include_history: When True, attach per-entry history.
        history_limit: Max history points per entry.
        history_days: Look-back window for the history series.

    Returns:
        CorrelationResponse with one entry per indicator that has
        data in the requested window.

    Raises:
        HTTPException: 422 when window_days is not 30, 90, or 365.
    """
    logger.info(
        f"GET /api/v1/correlation/btc "
        f"(window_days={window_days}, "
        f"include_history={include_history}, "
        f"history_limit={history_limit}, "
        f"history_days={history_days})"
    )

    # ---- 0. Validate window_days ----
    # FastAPI's Literal[30, 90, 365] for numeric types is unreliable
    # when combined with a separate default= on Query. We declare
    # window_days as a plain int and validate manually here.
    if window_days not in VALID_WINDOW_DAYS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "invalid_window_days",
                "message": (
                    f"Invalid window_days {window_days}. "
                    f"Must be one of {list(VALID_WINDOW_DAYS)}."
                ),
            },
        )

    async with session_scope() as session:
        repo = CorrelationRepository(session)

        # ---- 1. Fetch the latest per (indicator, window) ----
        latest_rows = await repo.fetch_latest_per_indicator(
            window_days=window_days
        )

        # ---- 2. Fetch history per indicator (opt-in) ----
        entries: List[CorrelationEntry] = []
        for row in latest_rows:
            history_points: List[CorrelationHistoryPoint] = []

            if include_history:
                try:
                    history_rows = await repo.fetch_history(
                        indicator_name=row["indicator_name"],
                        window_days=int(row["window_days"]),
                        days=history_days,
                    )
                    # fetch_history returns ascending by calculated_at.
                    # Truncate to the most recent N, keeping ascending
                    # order.
                    if len(history_rows) > history_limit:
                        history_rows = history_rows[-history_limit:]
                    history_points = [
                        _build_history_point(r) for r in history_rows
                    ]
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch history for "
                        f"{row['indicator_name']}/{row['window_days']}: "
                        f"{e}"
                    )
                    history_points = []

            try:
                entries.append(_build_entry(row, history_points))
            except Exception as e:
                logger.error(
                    f"Failed to build correlation entry for "
                    f"{row.get('indicator_name')}/"
                    f"{row.get('window_days')}: {e}",
                    exc_info=True,
                )

    response = CorrelationResponse(
        window_days=window_days,
        generated_at=datetime.now(timezone.utc),
        entries=entries,
    )

    logger.info(
        f"Returning {len(entries)} correlation entries "
        f"for {window_days}-day window"
    )

    return response