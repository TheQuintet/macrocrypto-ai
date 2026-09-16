"""Methodology API router (A4.1).

Exposes:
    - GET /api/v1/methodology

Returns the AI Service's methodology documentation as a structured
JSON response:
    - Model variants and their training strategies
    - Correlation method (Pearson) and its windows, thresholds, and
      labels
    - Regime classification method and its thresholds
    - External data sources with their URLs
    - Known limitations

Design:
    - The content lives in ``app.methodology``. The endpoint is a
      thin read path: build the dataclass, convert to the response
      model, return it. No database, no Redis, no I/O.
    - The response is static for a given process. Latency is
      effectively the cost of pydantic validation, well under the
      A4.1 target of 500 ms.
    - Version tracking is A4.2's job. This branch returns the
      current version string from the methodology object, but does
      not offer version history or version comparison.
    - No JWT auth (deferred, same as the other endpoints).
    - No rate limiting (deferred, same as the other endpoints).
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.methodology import build_methodology
from app.schemas.methodology import (
    MethodologyErrorResponse,
    MethodologyResponse,
)

logger = logging.getLogger(__name__)


# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/v1/methodology",
    tags=["methodology"],
)


# ============================================================
# ENDPOINT
# ============================================================
@router.get(
    "",
    response_model=MethodologyResponse,
    responses={
        500: {
            "model": MethodologyErrorResponse,
            "description": "Methodology content could not be served.",
        },
    },
    summary="Get the AI Service methodology documentation",
    description=(
        "Return the AI Service's methodology as structured JSON: "
        "model variants, correlation method and thresholds, regime "
        "classification, external data sources, and known "
        "limitations.\n\n"
        "The response is static for a given service version. The "
        "`version` field tracks changes to the methodology itself; "
        "history and comparison are out of scope for this endpoint."
    ),
)
async def get_methodology() -> MethodologyResponse:
    """Return the AI Service methodology documentation.

    Returns:
        MethodologyResponse with the full methodology content.

    Raises:
        HTTPException: 500 if the methodology content cannot be
            converted to the response model. This is a defensive
            branch — the canonical content is validated by
            ``tests/unit/test_methodology.py`` and should never
            fail at runtime.
    """
    logger.info("GET /api/v1/methodology")

    try:
        methodology = build_methodology()
        payload = methodology.to_dict()
        return MethodologyResponse.model_validate(payload)
    except Exception as e:
        logger.error(
            f"Failed to build methodology response: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "methodology_unavailable",
                "message": (
                    "Methodology content could not be served."
                ),
                "detail": str(e),
            },
        )


__all__ = ["router"]