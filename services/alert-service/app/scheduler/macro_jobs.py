"""Scheduled jobs for macro event monitoring."""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.macro_alert import (
    MacroEventAlert,
    MacroEventCache,
)
from app.rabbitmq.producer import RabbitMQProducer
from app.services.macro_alert_engine import (
    MacroAlertEngine,
    MacroEventSubscription,
)
from app.services.macro_email_service import MacroEmailService

logger = logging.getLogger(__name__)


def check_macro_events_job():
    """
    Scheduled job to check for upcoming macro events.

    Runs daily or hourly depending on scheduler configuration.
    """
    logger.info("🔄 Running check_macro_events_job")

    db = SessionLocal()
    producer = RabbitMQProducer()
    producer.connect()

    try:
        engine = MacroAlertEngine(db, producer)

        # Fetch events from economic calendar API.
        # In production this would typically call the Data Service.
        events = _fetch_economic_calendar_events()

        if events:
            logger.info(
                f"📅 Retrieved {len(events)} economic events"
            )

            # Update event cache.
            for event_data in events:
                _update_event_cache(db, event_data)

            # Check for events that need alerts.
            triggered = engine.check_upcoming_events()

            if triggered:
                logger.info(
                    f"🔔 {len(triggered)} macro events triggered alerts"
                )

                email_service = MacroEmailService(db)

                for alert in triggered:
                    # MacroAlertEngine returns MacroEventAlert ORM objects.
                    event = getattr(alert, "event", None)
                    timing = getattr(alert, "timing", None)

                    if not event:
                        logger.warning(
                            "Triggered macro alert has no associated event: %s",
                            alert,
                        )
                        continue

                    # Find subscribed users for this event type.
                    subscribers = (
                        db.query(MacroEventSubscription)
                        .filter(
                            MacroEventSubscription.event_type
                            == event.event_type,
                            MacroEventSubscription.subscribed.is_(True),
                        )
                        .all()
                    )

                    for subscription in subscribers:
                        # TODO: Replace this placeholder with the
                        # User Service lookup.
                        user_email = (
                            f"user_{subscription.user_id}@example.com"
                        )

                        email_service.queue_macro_alert_email(
                            alert=alert,
                            event=event,
                            timing=timing,
                            user_email=user_email,
                        )

        else:
            logger.info("No economic events retrieved")

        logger.info(
            "✅ check_macro_events_job completed successfully"
        )

    except Exception as exc:
        logger.error(
            f"❌ Error in check_macro_events_job: {exc}"
        )
        db.rollback()

    finally:
        db.close()
        producer.close()


def _fetch_economic_calendar_events() -> list:
    """
    Fetch economic calendar events from Data Service.

    This is currently a placeholder. In production this should
    call the Data Service API.
    """
    now = datetime.utcnow()

    return [
        {
            "event_id": "fed_2026_08_15",
            "event_type": "fed",
            "event_name": "Federal Reserve Meeting",
            "description": (
                "FOMC interest rate decision and economic projections"
            ),
            "scheduled_at": (
                now + timedelta(hours=24)
            ).isoformat(),
            "timezone": "UTC",
            "impact": "high",
            "source": "Data Service",
            "url": "https://macrocrypto.ai/events/fed",
        },
        {
            "event_id": "cpi_2026_08_18",
            "event_type": "cpi",
            "event_name": "CPI Release",
            "description": (
                "Consumer Price Index - Inflation data"
            ),
            "scheduled_at": (
                now + timedelta(days=5)
            ).isoformat(),
            "timezone": "UTC",
            "impact": "high",
            "source": "Data Service",
            "url": "https://macrocrypto.ai/events/cpi",
        },
        {
            "event_id": "gdp_2026_08_20",
            "event_type": "gdp",
            "event_name": "GDP Release",
            "description": (
                "Gross Domestic Product - Economic growth data"
            ),
            "scheduled_at": (
                now + timedelta(days=7)
            ).isoformat(),
            "timezone": "UTC",
            "impact": "medium",
            "source": "Data Service",
            "url": "https://macrocrypto.ai/events/gdp",
        },
    ]


def _update_event_cache(
    db: Session,
    event_data: dict,
):
    """
    Update an existing event in the cache or create a new one.
    """
    event_id = event_data.get("event_id")

    existing = (
        db.query(MacroEventCache)
        .filter(
            MacroEventCache.event_id == event_id
        )
        .first()
    )

    scheduled_at = datetime.fromisoformat(
        event_data["scheduled_at"]
    )

    if existing:
        existing.event_name = event_data.get(
            "event_name",
            existing.event_name,
        )

        existing.description = event_data.get(
            "description",
            existing.description,
        )

        existing.scheduled_at = scheduled_at

        existing.timezone = event_data.get(
            "timezone",
            "UTC",
        )

        existing.impact = event_data.get(
            "impact",
            "medium",
        )

        existing.source = event_data.get(
            "source",
            existing.source,
        )

        existing.url = event_data.get(
            "url",
            existing.url,
        )

        existing.updated_at = datetime.utcnow()

    else:
        new_event = MacroEventCache(
            event_id=event_id,
            event_type=event_data.get("event_type"),
            event_name=event_data.get("event_name"),
            description=event_data.get("description"),
            scheduled_at=scheduled_at,
            timezone=event_data.get(
                "timezone",
                "UTC",
            ),
            impact=event_data.get(
                "impact",
                "medium",
            ),
            source=event_data.get("source"),
            url=event_data.get("url"),
            notified=False,
        )

        db.add(new_event)

    db.commit()


def cleanup_old_events_job():
    """
    Cleanup macro events older than seven days from the cache.

    Runs daily.
    """
    logger.info("🔄 Running cleanup_old_events_job")

    db = SessionLocal()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        deleted = (
            db.query(MacroEventCache)
            .filter(
                MacroEventCache.scheduled_at < cutoff_date
            )
            .delete(
                synchronize_session=False
            )
        )

        db.commit()

        logger.info(
            f"✅ Deleted {deleted} old events from cache"
        )

    except Exception as exc:
        logger.error(
            f"❌ Error in cleanup_old_events_job: {exc}"
        )
        db.rollback()

    finally:
        db.close()