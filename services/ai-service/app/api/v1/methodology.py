"""Methodology API router (A4.1, A4.2).

Exposes:
    - GET /api/v1/methodology
    - GET /api/v1/methodology/versions
    - GET /api/v1/methodology/changelog

Returns the AI Service's methodology documentation as a structured
JSON response, plus version-tracking endpoints:
    - Model variants and their training strategies
    - Correlation method (Pearson) and its windows, thresholds, and
      labels
    - Regime classification method and its thresholds
    - External data sources with their URLs
    - Known limitations
    - The list of every shipped methodology version
    - The changelog of what changed in each version

Design:
    - The content lives in ``app.methodology``. The endpoints are
      thin read paths: build the dataclass, convert to the response
      model, return it. No database, no Redis, no I/O.
    - The response is static for a given process. Latency is
      effectively the cost of pydantic validation, well under the
      A4.1 target of 500 ms.
    - ``GET /api/v1/methodology`` accepts an optional ``?version=``
      query parameter. Omitted, it returns the current version —
      the pre-A4.2 behavior. Passing an unknown version returns a
      structured 404.
    - ``/versions`` and ``/changelog`` are separate endpoints so
      the base endpoint's response shape stays unchanged for
      existing callers.
    - No JWT auth (deferred, same as the other endpoints).
    - No rate limiting (deferred, same as the other endpoints).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.methodology import (
    build_methodology,
    get_methodology_changelog,
    list_methodology_versions,
)
from app.schemas.methodology import (
    MethodologyChangelogResponse,
    MethodologyErrorResponse,
    MethodologyResponse,
    MethodologyVersionListResponse,
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
# ENDPOINTS
# ============================================================
@router.get(
    "",
    response_model=MethodologyResponse,
    responses={
        404: {
            "model": MethodologyErrorResponse,
            "description": "Requested methodology version not found.",
        },
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
        "The `version` field tracks changes to the methodology "
        "itself. Use `?version=` to retrieve a specific historical "
        "version, or omit it to receive the current version. Use "
        "`/api/v1/methodology/versions` to list every available "
        "version and `/api/v1/methodology/changelog` for the "
        "release notes."
    ),
)
async def get_methodology(
    version: Optional[str] = Query(
        default=None,
        description=(
            "Optional methodology version to retrieve (e.g. "
            "'1.0.0'). Omit for the current version."
        ),
    ),
) -> MethodologyResponse:
    """Return the AI Service methodology documentation.

    Args:
        version: Optional methodology version string. ``None``
            returns the current version.

    Returns:
        MethodologyResponse with the requested (or current)
        methodology content.

    Raises:
        HTTPException: 404 if ``version`` is provided and not
            registered. 500 if the methodology content cannot be
            built or converted to the response model.
    """
    logger.info(
        f"GET /api/v1/methodology"
        f"{f' (version={version})' if version is not None else ''}"
    )

    # Build the methodology. A KeyError means the caller asked for a
    # version that is not registered — that is a 404. Any other
    # exception (a bug in the registry, a corrupted module-level
    # constant, etc.) is a 500 with a structured body.
    try:
        methodology = build_methodology(version)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "unknown_version",
                "message": (
                    f"Methodology version {version!r} is not "
                    f"registered. See "
                    f"/api/v1/methodology/versions for the list of "
                    f"available versions."
                ),
                "detail": "",
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to build methodology: {e}", exc_info=True
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

    # Convert to the response model. A failure here is also a 500,
    # but with a different log message so the operator can tell the
    # two paths apart.
    try:
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


@router.get(
    "/versions",
    response_model=MethodologyVersionListResponse,
    responses={
        500: {
            "model": MethodologyErrorResponse,
            "description": "Version list could not be served.",
        },
    },
    summary="List every released methodology version",
    description=(
        "Return the list of every methodology version ever "
        "released, oldest first, plus the current version. Use the "
        "`?version=` parameter on `/api/v1/methodology` to retrieve "
        "any of these versions."
    ),
)
async def get_methodology_versions() -> MethodologyVersionListResponse:
    """Return every released methodology version.

    Returns:
        MethodologyVersionListResponse with the current version and
        the ascending list of every registered version.

    Raises:
        HTTPException: 500 if the version list cannot be served.
    """
    logger.info("GET /api/v1/methodology/versions")

    try:
        versions = list_methodology_versions()
        current = build_methodology().version
        return MethodologyVersionListResponse(
            current_version=current,
            versions=versions,
        )
    except Exception as e:
        logger.error(
            f"Failed to build version list: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "version_list_unavailable",
                "message": (
                    "Methodology version list could not be served."
                ),
                "detail": str(e),
            },
        )


@router.get(
    "/changelog",
    response_model=MethodologyChangelogResponse,
    responses={
        500: {
            "model": MethodologyErrorResponse,
            "description": "Changelog could not be served.",
        },
    },
    summary="Get the methodology changelog",
    description=(
        "Return the changelog of every methodology version, newest "
        "first. Each entry names the version, its release date, a "
        "one-sentence summary, and a list of individual changes."
    ),
)
async def get_methodology_changelog_endpoint() -> (
    MethodologyChangelogResponse
):
    """Return the methodology changelog, newest version first.

    Returns:
        MethodologyChangelogResponse with every changelog entry.

    Raises:
        HTTPException: 500 if the changelog cannot be served.
    """
    logger.info("GET /api/v1/methodology/changelog")

    try:
        entries = get_methodology_changelog()
        return MethodologyChangelogResponse(
            entries=[e.to_dict() for e in entries],
        )
    except Exception as e:
        logger.error(
            f"Failed to build changelog: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "changelog_unavailable",
                "message": "Methodology changelog could not be served.",
                "detail": str(e),
            },
        )


__all__ = ["router"]