"""Macro event alert engine."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.macro_alert import (
    EventImpact,
    EventType,
    MacroAlertStatus,
    MacroEventAlert,
    MacroEventCache,
    MacroEventNotification,
    MacroEventSubscription,
)
from app.rabbitmq.producer import RabbitMQProducer
from app.models.alert import NotificationType
from app.services.macro_notification_service import MacroNotificationService
# from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


class MacroAlertEngine:
    """Core macro event alert engine."""

    def __init__(
        self,
        db: Session,
        producer: Optional[RabbitMQProducer] = None,
    ):
        self.db = db
        self.producer = producer
        self.notification_service = MacroNotificationService(db)

    def check_upcoming_events(self) -> List[Dict[str, Any]]:
        """
        Check for upcoming macro events and trigger alerts.

        Alert timings:
        - 1 day before: 23-25 hours
        - 12 hours before: 11-13 hours
        - 1 hour before: 0.5-1.5 hours
        """
        logger.info("🔍 Checking upcoming macro events")

        triggered_events: List[Dict[str, Any]] = []
        now = utc_now()

        events = (
            self.db.query(MacroEventCache)
            .filter(
                MacroEventCache.notified.is_(False),
                MacroEventCache.scheduled_at > now,
            )
            .all()
        )

        logger.info("📊 Found %d upcoming events", len(events))

        for event in events:
            scheduled_at = self._ensure_utc(event.scheduled_at)
            time_until = scheduled_at - now
            hours_until = time_until.total_seconds() / 3600

            logger.debug(
                "Event %s: %.2f hours until scheduled time",
                event.event_name,
                hours_until,
            )

            timings_to_check = self._get_timings(hours_until)

            if not timings_to_check:
                continue

            for timing in timings_to_check:
                triggered = self._trigger_alerts_for_event(
                    event=event,
                    timing=timing,
                )

                if triggered:
                    triggered_events.append(
                        {
                            "event": event,
                            "timing": timing,
                        }
                    )

            # Mark the event as notified after the final alert window.
            #
            # Note:
            # This preserves the existing behavior where an event is marked
            # notified after the 1h alert or when only one timing is matched.
            if "1h" in timings_to_check or len(timings_to_check) == 1:
                event.notified = True
                event.notified_at = now

                try:
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    logger.exception(
                        "Failed to mark event %s as notified",
                        event.event_name,
                    )

        return triggered_events

    @staticmethod
    def _get_timings(hours_until: float) -> List[str]:
        """Return alert timings applicable to the current time window."""
        timings: List[str] = []

        if 23 <= hours_until <= 25:
            timings.append("1d")

        if 11 <= hours_until <= 13:
            timings.append("12h")

        if 0.5 <= hours_until <= 1.5:
            timings.append("1h")

        return timings

    def _trigger_alerts_for_event(
        self,
        event: MacroEventCache,
        timing: str,
    ) -> bool:
        """Trigger alerts for subscribers of a specific event."""
        logger.info(
            "🔔 Triggering alerts for %s (%s)",
            event.event_name,
            timing,
        )

        logger.debug(
            "EVENT DEBUG: event_type=%r (%s), impact=%r (%s)",
            event.event_type,
            type(event.event_type).__name__,
            event.impact,
            type(event.impact).__name__,
        )

        # First filter by event type and subscription status.
        subscriptions = (
            self.db.query(MacroEventSubscription)
            .filter(
                MacroEventSubscription.event_type == event.event_type,
                MacroEventSubscription.subscribed.is_(True),
            )
            .all()
        )

        logger.debug(
            "Found %d subscriptions matching event type %r",
            len(subscriptions),
            event.event_type,
        )

        # Apply impact filtering in Python.
        #
        # This is intentional because comparing SQLAlchemy Enum columns
        # directly with <= is not reliable for enum values.
        subscribers = [
            subscription
            for subscription in subscriptions
            if self._impact_matches(subscription, event)
        ]

        if not subscribers:
            logger.info(
                "No subscribers for %s",
                event.event_name,
            )
            return False

        logger.info(
            "Found %d subscribers for %s",
            len(subscribers),
            event.event_name,
        )

        notification_sent = False

        for subscription in subscribers:
            subscription_timing = (
                subscription.timing.value
                if subscription.timing is not None
                else None
            )
            if subscription_timing and subscription_timing != timing:
                logger.debug(
                    "Skipping subscription %s: wants timing %s, window is %s",
                    subscription.user_id,
                    subscription_timing,
                    timing,
                )
                continue

            logger.info(
                            "PROCESSING subscription user=%s event=%s type=%s timing=%s",
                            subscription.user_id,
                            event.event_name,
                            event.event_type,
                            timing,
                        )
            alert = self._get_or_create_alert(
                subscription=subscription,
                event=event,
                timing=timing,
            )

            if alert is None:
                continue

            if alert.status != MacroAlertStatus.ACTIVE:
                logger.debug(
                    "Skipping alert %s because status is %s",
                    alert.id,
                    alert.status,
                )
                continue

            self._send_notification(
                alert=alert,
                event=event,
                timing=timing,
            )

            if subscription.one_time:
                subscription.subscribed = False
                subscription.updated_at = utc_now()

            notification_sent = True

        if notification_sent:
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.exception(
                    "Failed to persist subscription state after macro alert",
                )

        return notification_sent

    @staticmethod
    def _impact_matches(
        subscription: MacroEventSubscription,
        event: MacroEventCache,
    ) -> bool:
        """
        Determine whether an event's impact satisfies a subscription.

        Subscription examples:
        - LOW receives LOW, MEDIUM, HIGH
        - MEDIUM receives MEDIUM, HIGH
        - HIGH receives HIGH
        """
        impact_priority = {
            EventImpact.LOW: 1,
            EventImpact.MEDIUM: 2,
            EventImpact.HIGH: 3,
        }

        subscription_impact = MacroAlertEngine._normalize_impact(
            subscription.impact_filter
        )
        event_impact = MacroAlertEngine._normalize_impact(
            event.impact
        )

        if subscription_impact is None:
            logger.warning(
                "Invalid subscription impact_filter: %r",
                subscription.impact_filter,
            )
            return False

        if event_impact is None:
            logger.warning(
                "Invalid event impact: %r",
                event.impact,
            )
            return False

        return (
            impact_priority[subscription_impact]
            <= impact_priority[event_impact]
        )

    @staticmethod
    def _normalize_impact(
        impact: Any,
    ) -> Optional[EventImpact]:
        """Normalize an EventImpact enum or string into EventImpact."""
        if isinstance(impact, EventImpact):
            return impact

        if isinstance(impact, str):
            try:
                return EventImpact(impact.lower())
            except ValueError:
                return None

        return None

    @staticmethod
    def _normalize_event_type(
        event_type: Any,
    ) -> Optional[EventType]:
        """Normalize an EventType enum or string into EventType."""
        if isinstance(event_type, EventType):
            return event_type

        if isinstance(event_type, str):
            try:
                return EventType(event_type.lower())
            except ValueError:
                return None

        return None

    def _get_or_create_alert(
        self,
        subscription: MacroEventSubscription,
        event: MacroEventCache,
        timing: str,
    ) -> Optional[MacroEventAlert]:
        """Get an existing alert or create a new one."""
        user_id = subscription.user_id
        event_type = self._normalize_event_type(event.event_type)

        if event_type is None:
            logger.error(
                "Cannot create macro alert: invalid event type %r",
                event.event_type,
            )
            return None

        alert = (
            self.db.query(MacroEventAlert)
            .filter(
                MacroEventAlert.user_id == user_id,
                MacroEventAlert.event_id == event.id,
                MacroEventAlert.event_type == event_type,
                MacroEventAlert.timing == timing,
            )
            .first()
        )

        if alert:
            alert.notify_in_app = subscription.notify_in_app
            alert.notify_email = subscription.notify_email
            return alert

        impact = self._normalize_impact(event.impact)

        if impact is None:
            logger.error(
                "Cannot create macro alert: invalid impact %r",
                event.impact,
            )
            return None

        alert = MacroEventAlert(
            user_id=user_id,
            event_id=event.id, 
            event_type=event_type,
            timing=timing,
            impact_filter=impact,
            status=MacroAlertStatus.ACTIVE,
            notify_in_app=subscription.notify_in_app,
            notify_email=subscription.notify_email,
        )

        self.db.add(alert)

        try:
            self.db.commit()
            self.db.refresh(alert)
        except Exception:
            self.db.rollback()
            logger.exception(
                "Failed to create macro alert for user %s",
                user_id,
            )
            return None

        logger.info(
            "Created macro alert %s for user %s",
            alert.id,
            user_id,
        )

        return alert

    def _send_notification(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str,
    ) -> None:
        """Send notifications for a macro event alert."""
        try:
            if alert.notify_in_app:
                self._create_in_app_notification(
                    alert=alert,
                    event=event,
                    timing=timing,
                )

            if alert.notify_email:
                self._queue_email_notification(
                    alert=alert,
                    event=event,
                    timing=timing,
                )

            alert.status = MacroAlertStatus.TRIGGERED
            alert.triggered_at = utc_now()

            self.db.commit()

            logger.info(
                "✅ Macro alert %s triggered for user %s",
                alert.id,
                alert.user_id,
            )

        except Exception:
            self.db.rollback()
            logger.exception(
                "Failed to send notification for macro alert %s",
                alert.id,
            )

    def _create_in_app_notification(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str,
    ) -> None:
        """Create an in-app notification for a macro event."""
        timing_labels = {
            "1d": "1 day before",
            "12h": "12 hours before",
            "1h": "1 hour before",
        }

        impact_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }

        event_type_labels = {
            "fed": "Fed Meeting",
            "cpi": "CPI Release",
            "gdp": "GDP Release",
            "employment": "Employment Report",
            "other": "Economic Event",
        }

        event_type = self._normalize_event_type(event.event_type)
        impact = self._normalize_impact(event.impact)

        event_type_value = (
            event_type.value
            if event_type
            else "other"
        )

        impact_value = (
            impact.value
            if impact
            else "medium"
        )

        event_label = event_type_labels.get(
            event_type_value,
            event.event_name,
        )

        title = f"📅 Macro Event Alert: {event_label}"

        scheduled_at = self._ensure_utc(event.scheduled_at)

        message = (
            f"⚠️ {event.event_name} in "
            f"{timing_labels.get(timing, timing)}\n\n"
            f"📅 Date: "
            f"{scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"📊 Impact: "
            f"{impact_emoji.get(impact_value, '')} "
            f"{impact_value.upper()}\n"
            f"📝 "
            f"{event.description or 'Major economic event that may affect BTC'}"
        )

        self.notification_service.create_macro_notification(
            user_id=alert.user_id,
            alert_id=alert.id,
            event_name=event.event_name,
            event_type=event_type_value,
            event_date=scheduled_at,
            timing=timing,
            impact=impact_value,
            description=event.description,
            data={
                "alert_id": str(alert.id),
                "event_name": event.event_name,
                "event_type": event_type_value,
                "event_date": scheduled_at.isoformat(),
                "timing": timing,
                "impact": impact_value,
                "description": event.description,
            },
            action_url=f"/alerts/macro/{alert.id}",
        )

        logger.debug(
            "📱 In-app notification created for macro alert %s",
            alert.id,
        )

    def _queue_email_notification(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str,
    ) -> None:
        """
        Queue an email notification for a macro event.

        Email delivery is currently a placeholder until the macro
        email service is fully integrated.
        """
        logger.info(
            "📧 Email notification queued for macro alert %s",
            alert.id,
        )

    def get_events_needing_notification(
        self,
    ) -> List[MacroEventCache]:
        """Get upcoming events that have not yet been notified."""
        now = utc_now()

        return (
            self.db.query(MacroEventCache)
            .filter(
                MacroEventCache.notified.is_(False),
                MacroEventCache.scheduled_at > now,
            )
            .all()
        )

    def get_user_subscriptions(
        self,
        user_id: UUID,
    ) -> List[MacroEventSubscription]:
        """Get all macro event subscriptions for a user."""
        return (
            self.db.query(MacroEventSubscription)
            .filter(
                MacroEventSubscription.user_id == user_id,
            )
            .all()
        )

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        """
        Ensure a datetime is timezone-aware UTC.

        Handles both naive and timezone-aware datetimes because existing
        database records may contain naive UTC values.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)