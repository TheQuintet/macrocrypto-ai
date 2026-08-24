"""
FRED economic calendar collector.

Collects economic release dates for:
- Federal Reserve / FOMC
- Consumer Price Index (CPI)
- Employment Situation
- Gross Domestic Product (GDP)

This collector is responsible only for fetching and normalizing
calendar data. Database persistence is handled separately.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings


logger = logging.getLogger(__name__)


class EconomicCalendarCollector:
    """
    Collector for FRED economic calendar release dates.
    """

    def __init__(self):
        self.base_url = settings.FRED_API_URL
        self.api_key = settings.FRED_API_KEY
        self.timeout = 10.0
        self.request_delay = settings.FRED_REQUEST_DELAY

        self.client = httpx.AsyncClient(
            timeout=self.timeout
        )

        logger.info(
            "EconomicCalendarCollector initialized"
        )

    async def _get_release_dates(
        self,
        release_id: int,
    ) -> dict[str, Any]:
        """
        Fetch release dates for a FRED release.

        FRED's release/dates endpoint does not provide
        start_date/end_date parameters for filtering actual
        release dates. Therefore, the returned dates are
        filtered locally by the caller.
        """

        if not self.api_key:
            logger.error(
                "FRED API key is missing"
            )
            return {}

        endpoint = (
            f"{self.base_url}/release/dates"
        )

        params = {
            "release_id": release_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "asc",
            "limit": 10000,
        }

        try:
            await asyncio.sleep(
                self.request_delay
            )

            logger.info(
                "Fetching FRED release dates: "
                "release_id=%s",
                release_id,
            )

            response = await self.client.get(
                endpoint,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

            logger.info(
                "Successfully fetched FRED release dates: "
                "release_id=%s, count=%s",
                release_id,
                data.get("count", 0),
            )

            return data

        except httpx.TimeoutException:
            logger.error(
                "Timeout fetching FRED release %s",
                release_id,
            )
            return {}

        except httpx.HTTPStatusError as error:
            logger.error(
                "FRED HTTP error %s for release %s",
                error.response.status_code,
                release_id,
            )
            return {}

        except Exception as error:
            logger.error(
                "Error fetching FRED release %s: %s",
                release_id,
                error,
            )
            return {}

    def _normalize_release_dates(
        self,
        data: dict[str, Any],
        event_name: str,
        event_type: str,
        impact_level: str,
        btc_description: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """
        Convert FRED release dates into normalized
        economic event dictionaries.

        Only events within the requested date range
        are returned.
        """

        release_dates = data.get(
            "release_dates",
            []
        )

        events = []

        for release in release_dates:

            release_date = release.get("date")

            if not release_date:
                continue

            try:
                event_date = datetime.strptime(
                    release_date,
                    "%Y-%m-%d",
                ).replace(
                    tzinfo=timezone.utc
                )

            except ValueError:
                logger.warning(
                    "Invalid FRED release date: %s",
                    release_date,
                )
                continue

            if (
                event_date < start_date
                or event_date > end_date
            ):
                continue

            events.append(
                {
                    "event_name": event_name,
                    "event_type": event_type,
                    "event_date": event_date,
                    "impact_level": impact_level,
                    "description": btc_description,
                }
            )

        return events

    async def get_events_by_type(
        self,
        event_type: str,
        days: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch economic calendar events for a configured
        event type.

        Supported event types:
        - fed
        - cpi
        - employment
        - gdp
        """

        release_id = settings.FRED_CALENDAR_RELEASES.get(
            event_type
        )

        if release_id is None:
            logger.error(
                "Unsupported economic event type: %s",
                event_type,
            )
            return []

        if days is None:
            days = (
                settings.FRED_CALENDAR_LOOKBACK_DAYS
            )

        end_date = datetime.now(
            timezone.utc
        ).replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        start_date = (
            end_date
            - timedelta(days=days)
        )

        data = await self._get_release_dates(
            release_id=release_id
        )

        event_metadata = {
            "fed": {
                "event_name": "FOMC Press Release",
                "impact_level": "high",
                "description": (
                    "Federal Reserve policy decisions and "
                    "guidance can strongly affect interest-rate "
                    "expectations, the US dollar, liquidity, "
                    "and Bitcoin."
                ),
            },
            "cpi": {
                "event_name": "Consumer Price Index",
                "impact_level": "high",
                "description": (
                    "CPI measures US inflation. Higher-than-"
                    "expected inflation can increase rate "
                    "expectations and pressure Bitcoin, while "
                    "lower inflation can support risk assets "
                    "and Bitcoin."
                ),
            },
            "employment": {
                "event_name": "Employment Situation",
                "impact_level": "high",
                "description": (
                    "US employment data indicates labor-market "
                    "strength and can influence Federal Reserve "
                    "policy expectations, Treasury yields, "
                    "and Bitcoin."
                ),
            },
            "gdp": {
                "event_name": "Gross Domestic Product",
                "impact_level": "high",
                "description": (
                    "GDP measures US economic growth. Strong "
                    "or weak growth can influence monetary-policy "
                    "expectations, risk sentiment, and Bitcoin."
                ),
            },
        }

        metadata = event_metadata.get(
            event_type
        )

        if metadata is None:
            logger.error(
                "Missing metadata for economic event type: %s",
                event_type,
            )
            return []

        return self._normalize_release_dates(
            data=data,
            event_name=metadata["event_name"],
            event_type=event_type,
            impact_level=metadata["impact_level"],
            btc_description=metadata["description"],
            start_date=start_date,
            end_date=end_date,
        )

    async def get_all_events(
        self,
        days: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch all configured economic calendar events.
        """

        if days is None:
            days = (
                settings.FRED_CALENDAR_LOOKBACK_DAYS
            )

        logger.info(
            "Fetching all economic calendar events "
            "(days=%s)",
            days,
        )

        events = []

        for event_type in (
            settings.FRED_CALENDAR_RELEASES
        ):
            type_events = await self.get_events_by_type(
                event_type=event_type,
                days=days,
            )

            events.extend(type_events)

        events.sort(
            key=lambda event: event["event_date"]
        )

        logger.info(
            "Collected %d economic calendar events",
            len(events),
        )

        return events

    async def close(self):
        """
        Close the HTTP client.
        """

        await self.client.aclose()

        logger.info(
            "EconomicCalendarCollector closed"
        )