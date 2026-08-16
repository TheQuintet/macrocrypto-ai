"""Scheduled jobs for macro event monitoring"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.macro_alert_engine import MacroAlertEngine
from app.services.macro_email_service import MacroEmailService
from app.models.macro_alert import MacroEventCache
from app.rabbitmq.producer import RabbitMQProducer

logger = logging.getLogger(__name__)


def check_macro_events_job():
    """
    Scheduled job to check for upcoming macro events.
    Runs daily (or hourly for near-term events).
    """
    logger.info("🔄 Running check_macro_events_job")

    db = SessionLocal()
    producer = RabbitMQProducer()
    producer.connect()

    try:
        engine = MacroAlertEngine(db, producer)

        # Fetch events from economic calendar API
        # This would typically call the Data Service API
        events = _fetch_economic_calendar_events()

        if events:
            logger.info(f"📅 Retrieved {len(events)} economic events")

            # Update cache with new events
            for event_data in events:
                _update_event_cache(db, event_data)

            # Check for events that need alerts
            triggered = engine.check_upcoming_events()

            if triggered:
                logger.info(f"🔔 {len(triggered)} macro events triggered alerts")

                # Send emails for triggered events
                email_service = MacroEmailService(db)
                for item in triggered:
                    event = item.get("event")
                    timing = item.get("timing")
                    if event:
                        # Get subscribers for this event
                        subscribers = db.query(MacroEventSubscription).filter(
                            MacroEventSubscription.event_type == event.event_type,
                            MacroEventSubscription.subscribed == True
                        ).all()

                        for sub in subscribers:
                            # Fetch user email (placeholder - from user service)
                            user_email = f"user_{sub.user_id}@example.com"  # TODO: Fetch from user service
                            email_service.queue_macro_alert_email(
                                alert=alert,
                                event=event,
                                timing=timing,
                                user_email=user_email
                            )

        else:
            logger.info("No economic events retrieved")

        logger.info("✅ check_macro_events_job completed successfully")

    except Exception as e:
        logger.error(f"❌ Error in check_macro_events_job: {e}")
        db.rollback()

    finally:
        db.close()
        producer.close()


def _fetch_economic_calendar_events() -> list:
    """
    Fetch economic calendar events from Data Service.
    This is a placeholder - in production, this would call the Data Service API.
    """
    # Placeholder - in production, fetch from Data Service
    now = datetime.utcnow()
    return [
        {
            "event_id": "fed_2026_08_15",
            "event_type": "fed",
            "event_name": "Federal Reserve Meeting",
            "description": "FOMC interest rate decision and economic projections",
            "scheduled_at": (now + timedelta(days=2)).isoformat(),
            "timezone": "UTC",
            "impact": "high",
            "source": "Data Service",
            "url": "https://macrocrypto.ai/events/fed"
        },
        {
            "event_id": "cpi_2026_08_18",
            "event_type": "cpi",
            "event_name": "CPI Release",
            "description": "Consumer Price Index - Inflation data",
            "scheduled_at": (now + timedelta(days=5)).isoformat(),
            "timezone": "UTC",
            "impact": "high",
            "source": "Data Service",
            "url": "https://macrocrypto.ai/events/cpi"
        },
        {
            "event_id": "gdp_2026_08_20",
            "event_type": "gdp",
            "event_name": "GDP Release",
            "description": "Gross Domestic Product - Economic growth data",
            "scheduled_at": (now + timedelta(days=7)).isoformat(),
            "timezone": "UTC",
            "impact": "medium",
            "source": "Data Service",
            "url": "https://macrocrypto.ai/events/gdp"
        }
    ]


def _update_event_cache(db: Session, event_data: dict):
    """Update or create event in cache."""
    event_id = event_data.get("event_id")

    existing = db.query(MacroEventCache).filter(
        MacroEventCache.event_id == event_id
    ).first()

    if existing:
        # Update existing
        existing.event_name = event_data.get("event_name", existing.event_name)
        existing.description = event_data.get("description", existing.description)
        existing.scheduled_at = datetime.fromisoformat(event_data.get("scheduled_at"))
        existing.timezone = event_data.get("timezone", "UTC")
        existing.impact = event_data.get("impact", "medium")
        existing.source = event_data.get("source", existing.source)
        existing.url = event_data.get("url", existing.url)
        existing.updated_at = datetime.utcnow()
    else:
        # Create new
        new_event = MacroEventCache(
            event_id=event_id,
            event_type=event_data.get("event_type"),
            event_name=event_data.get("event_name"),
            description=event_data.get("description"),
            scheduled_at=datetime.fromisoformat(event_data.get("scheduled_at")),
            timezone=event_data.get("timezone", "UTC"),
            impact=event_data.get("impact", "medium"),
            source=event_data.get("source"),
            url=event_data.get("url"),
            notified=False
        )
        db.add(new_event)

    db.commit()


def cleanup_old_events_job():
    """
    Cleanup old events from cache.
    Runs daily.
    """
    logger.info("🔄 Running cleanup_old_events_job")

    db = SessionLocal()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        deleted = db.query(MacroEventCache).filter(
            MacroEventCache.scheduled_at < cutoff_date
        ).delete()

        db.commit()
        logger.info(f"✅ Deleted {deleted} old events from cache")

    except Exception as e:
        logger.error(f"❌ Error in cleanup_old_events_job: {e}")
        db.rollback()

    finally:
        db.close()