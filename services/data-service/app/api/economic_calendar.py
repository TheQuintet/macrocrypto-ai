"""
Economic calendar endpoints for data-service.
"""

import logging
from zoneinfo import ZoneInfo

from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    Query,
)
from app.config import settings
from app.api.dependencies import jwt_auth
from app.api.schemas.economic_calendar import (
    EconomicCalendarResponse,
)
from app.database.session import SessionLocal
from app.models.economic_event import EconomicEvent
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1",
    tags=["Economic Calendar"],
)


VALID_EVENT_TYPES = {
    "fed",
    "cpi",
    "vix",
    "employment",
    "gdp",
}

VALID_IMPACT_LEVELS = {
    "high",
    "medium",
    "low",
}


@router.get(
    "/economic-calendar",
    response_model=EconomicCalendarResponse,
    summary="Get economic calendar events",
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_economic_calendar(
    request: Request,
    event_type: str | None = Query(
        default=None,
        description="Filter by event type",
    ),
    impact_level: str | None = Query(
        default=None,
        description="Filter by impact level",
    ),
    timezone_name: str = Query(
        default="UTC",
        alias="timezone",
        description="IANA timezone used to display event dates",
    ),
    _: str | None = Depends(jwt_auth),
):
    """
    Return economic calendar events.

    Economic events are stored in UTC and converted to the
    requested IANA timezone before being returned.

    Supported event types:
        - fed
        - cpi
        - vix
        - employment
        - gdp

    Supported impact levels:
        - high
        - medium
        - low

    Examples:

        GET /api/v1/economic-calendar

        GET /api/v1/economic-calendar?event_type=cpi

        GET /api/v1/economic-calendar?impact_level=high

        GET /api/v1/economic-calendar?event_type=fed&impact_level=high

        GET /api/v1/economic-calendar?timezone=Africa/Addis_Ababa

        GET /api/v1/economic-calendar?timezone=America/New_York
    """

    # --------------------------------------------------
    # 1. Validate event type
    # --------------------------------------------------

    if (
        event_type is not None
        and event_type not in VALID_EVENT_TYPES
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid event_type. Must be one of: "
                f"{', '.join(sorted(VALID_EVENT_TYPES))}"
            ),
        )

    # --------------------------------------------------
    # 2. Validate impact level
    # --------------------------------------------------

    if (
        impact_level is not None
        and impact_level not in VALID_IMPACT_LEVELS
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid impact_level. Must be one of: "
                f"{', '.join(sorted(VALID_IMPACT_LEVELS))}"
            ),
        )

    # --------------------------------------------------
    # 3. Validate requested timezone
    # --------------------------------------------------

    try:
        user_timezone = ZoneInfo(timezone_name)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid timezone: {timezone_name}",
        )

    # --------------------------------------------------
    # 4. Create database session
    # --------------------------------------------------

    db = SessionLocal()

    try:

        # --------------------------------------------------
        # 5. Build query
        # --------------------------------------------------

        query = db.query(EconomicEvent)

        if event_type is not None:
            query = query.filter(
                EconomicEvent.event_type == event_type
            )

        if impact_level is not None:
            query = query.filter(
                EconomicEvent.impact_level == impact_level
            )

        # --------------------------------------------------
        # 6. Order chronologically
        # --------------------------------------------------

        events = query.order_by(
            EconomicEvent.event_date.asc()
        ).all()

        logger.info(
            "Retrieved %d economic calendar events (timezone=%s)",
            len(events),
            timezone_name,
        )

        # --------------------------------------------------
        # 7. Convert UTC timestamps to requested timezone
        # --------------------------------------------------

        for event in events:
            event.event_date = event.event_date.astimezone(
                user_timezone
            )

        # --------------------------------------------------
        # 8. Return API response
        # --------------------------------------------------

        return EconomicCalendarResponse(
            count=len(events),
            events=events,
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Failed to retrieve economic calendar events"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve economic calendar events",
        )

    finally:
        db.close()

        logger.info(
            "Economic calendar database session closed"
        )