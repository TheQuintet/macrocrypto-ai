"""Macro event alert engine"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.macro_alert import (
    MacroEventAlert,
    MacroEventSubscription,
    MacroEventNotification,
    MacroEventCache,
    EventType,
    EventTiming,
    EventImpact,
    MacroAlertStatus
)
from app.services.notification_service import NotificationService
from app.rabbitmq.producer import RabbitMQProducer

logger = logging.getLogger(__name__)


class MacroAlertEngine:
    """Core macro event alert engine"""

    def __init__(self, db: Session, producer: Optional[RabbitMQProducer] = None):
        self.db = db
        self.producer = producer
        self.notification_service = NotificationService(db)

    def check_upcoming_events(self) -> List[Dict[str, Any]]:
        """
        Check for upcoming events and trigger alerts.
        Called by scheduled job.
        """
        logger.info("🔍 Checking upcoming macro events")
        
        triggered_events = []
        now = datetime.utcnow()
        
        # Get events that need alerts (not yet notified)
        events = self.db.query(MacroEventCache).filter(
            MacroEventCache.notified == False,
            MacroEventCache.scheduled_at > now
        ).all()
        
        logger.info(f"📊 Found {len(events)} upcoming events")
        
        for event in events:
            # Check if event needs alert
            time_until = event.scheduled_at - now
            hours_until = time_until.total_seconds() / 3600
            
            # Determine which alerts to send based on timing
            timings_to_check = []
            
            if 23 <= hours_until <= 25:
                timings_to_check.append("1d")
            if 11 <= hours_until <= 13:
                timings_to_check.append("12h")
            if 0.5 <= hours_until <= 1.5:
                timings_to_check.append("1h")
            
            if timings_to_check:
                for timing in timings_to_check:
                    triggered = self._trigger_alerts_for_event(event, timing)
                    if triggered:
                        triggered_events.append({
                            "event": event,
                            "timing": timing
                        })
                
                # Mark event as notified if all timing alerts sent
                # (We mark after 1h alert, or if only one timing exists)
                if "1h" in timings_to_check or len(timings_to_check) == 1:
                    event.notified = True
                    event.notified_at = now
                    self.db.commit()
        
        return triggered_events

    def _trigger_alerts_for_event(self, event: MacroEventCache, timing: str) -> bool:
        """Trigger alerts for a specific event and timing."""
        logger.info(f"🔔 Triggering alerts for {event.event_name} ({timing})")
        
        # Get subscribed users for this event type and impact level
        subscribers = self.db.query(MacroEventSubscription).filter(
            MacroEventSubscription.event_type == event.event_type,
            MacroEventSubscription.subscribed == True,
            MacroEventSubscription.impact_filter <= event.impact
        ).all()
        
        if not subscribers:
            logger.info(f"No subscribers for {event.event_name}")
            return False
        
        logger.info(f"Found {len(subscribers)} subscribers")
        
        for subscription in subscribers:
            # Create or get user's alert
            alert = self._get_or_create_alert(subscription.user_id, event, timing)
            
            if alert and alert.status == MacroAlertStatus.ACTIVE:
                self._send_notification(alert, event, timing)
        
        return True

    def _get_or_create_alert(
        self,
        user_id: UUID,
        event: MacroEventCache,
        timing: str
    ) -> Optional[MacroEventAlert]:
        """Get existing alert or create a new one."""
        alert = self.db.query(MacroEventAlert).filter(
            MacroEventAlert.user_id == user_id,
            MacroEventAlert.event_type == event.event_type,
            MacroEventAlert.timing == timing
        ).first()
        
        if not alert:
            alert = MacroEventAlert(
                user_id=user_id,
                event_type=event.event_type,
                timing=timing,
                impact_filter=event.impact,
                status=MacroAlertStatus.ACTIVE,
                notify_in_app=True,
                notify_email=True
            )
            self.db.add(alert)
            self.db.commit()
            self.db.refresh(alert)
        
        return alert

    def _send_notification(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str
    ):
        """Send notification for a macro event."""
        # Create in-app notification
        if alert.notify_in_app:
            self._create_in_app_notification(alert, event, timing)
        
        # Queue email notification
        if alert.notify_email:
            self._queue_email_notification(alert, event, timing)
        
        # Update alert
        alert.status = MacroAlertStatus.TRIGGERED
        alert.triggered_at = datetime.utcnow()
        self.db.commit()

    def _create_in_app_notification(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str
    ):
        """Create in-app notification for macro event."""
        timing_labels = {
            "1d": "1 day before",
            "12h": "12 hours before",
            "1h": "1 hour before"
        }
        
        impact_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }
        
        event_type_labels = {
            "fed": "Fed Meeting",
            "cpi": "CPI Release",
            "gdp": "GDP Release",
            "employment": "Employment Report",
            "other": "Economic Event"
        }
        
        event_label = event_type_labels.get(
            event.event_type.value if event.event_type else "other",
            event.event_name
        )
        
        title = f"📅 Macro Event Alert: {event_label}"
        message = (
            f"⚠️ {event.event_name} in {timing_labels.get(timing, timing)}\n\n"
            f"📅 Date: {event.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"📊 Impact: {impact_emoji.get(event.impact.value, '')} {event.impact.value.upper()}\n"
            f"📝 {event.description or 'Major economic event that may affect BTC'}"
        )
        
        self.notification_service.create_notification(
            user_id=alert.user_id,
            alert_id=alert.id,
            title=title,
            message=message,
            notification_type="macro_alert",
            data={
                "alert_id": str(alert.id),
                "event_name": event.event_name,
                "event_type": event.event_type.value if event.event_type else None,
                "event_date": event.scheduled_at.isoformat(),
                "timing": timing,
                "impact": event.impact.value if event.impact else None,
                "description": event.description
            },
            action_url=f"/alerts/macro/{alert.id}"
        )
        logger.debug(f"📱 In-app notification created for macro alert {alert.id}")

    def _queue_email_notification(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str
    ):
        """Queue email notification for macro event."""
        # Placeholder - will be implemented in T9.5
        logger.info(f"📧 Email notification queued for macro alert {alert.id}")

    def get_events_needing_notification(self) -> List[MacroEventCache]:
        """Get events that need notification."""
        now = datetime.utcnow()
        return self.db.query(MacroEventCache).filter(
            MacroEventCache.notified == False,
            MacroEventCache.scheduled_at > now
        ).all()

    def get_user_subscriptions(self, user_id: UUID) -> List[MacroEventSubscription]:
        """Get all subscriptions for a user."""
        return self.db.query(MacroEventSubscription).filter(
            MacroEventSubscription.user_id == user_id
        ).all()