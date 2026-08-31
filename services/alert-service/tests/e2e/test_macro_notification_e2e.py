"""End-to-end tests for the macro event subscription-to-notification flow."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.macro_routes import get_db
from app.models.macro_alert import (
    EventImpact,
    EventType,
    MacroAlertStatus,
    MacroEventAlert,
    MacroEventCache,
    MacroEventNotification,
    MacroEventSubscription,
)
from app.services.macro_alert_engine import MacroAlertEngine


class TestMacroNotificationE2E:
    """End-to-end tests for the complete macro notification flow."""

    @pytest.fixture
    def client(self, db_session):
        """Create FastAPI test client using the test database session."""

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()

    @pytest.fixture
    def test_user_id(self):
        """Create a unique test user ID."""
        return uuid4()

    @pytest.fixture
    def sample_event(
        self,
        db_session: Session,
    ):
        """
        Create a macro event that falls inside the 1-day alert window.

        The engine checks for events approximately 23-25 hours before
        their scheduled time.
        """
        now = datetime.now(timezone.utc)

        event = MacroEventCache(
            id=uuid4(),
            event_id=f"e2e_event_{uuid4()}",
            event_type=EventType.FED,
            event_name="E2E Federal Reserve Meeting",
            description="E2E test Federal Reserve interest rate decision.",
            scheduled_at=now + timedelta(hours=24),
            timezone="UTC",
            impact=EventImpact.HIGH,
            actual_value=None,
            expected_value=None,
            previous_value=None,
            source="E2E Test",
            url="https://example.com/e2e-event",
            notified=False,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        return event

    @pytest.fixture
    def sample_subscription(
        self,
        db_session: Session,
        test_user_id,
    ):
        """Create an active high-impact Fed subscription."""
        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=test_user_id,
            event_type=EventType.FED,
            subscribed=True,
            impact_filter=EventImpact.HIGH,
        )

        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)

        return subscription

    def test_subscription_to_notification_flow(
        self,
        client,
        db_session,
        test_user_id,
        sample_event,
        sample_subscription,
    ):
        """
        Test the complete subscription -> alert -> notification flow.

        Flow:
            1. User subscribes to Fed events.
            2. Upcoming Fed event exists.
            3. MacroAlertEngine detects the event.
            4. MacroEventAlert is created.
            5. MacroEventNotification is created.
            6. Notification appears in all-notifications API.
            7. Notification appears in unread API.
            8. Read-all marks it as read.
            9. Notification disappears from unread API.
        """

        # ============================================================
        # 1. VERIFY SUBSCRIPTION
        # ============================================================

        subscription = (
            db_session.query(MacroEventSubscription)
            .filter(
                MacroEventSubscription.user_id == test_user_id,
                MacroEventSubscription.event_type == EventType.FED,
            )
            .first()
        )

        assert subscription is not None
        assert subscription.subscribed is True
        assert subscription.impact_filter == EventImpact.HIGH

        # ============================================================
        # 2. VERIFY UPCOMING EVENT
        # ============================================================

        assert sample_event.notified is False
        assert sample_event.event_type == EventType.FED
        assert sample_event.impact == EventImpact.HIGH

        now = datetime.now(timezone.utc)

        scheduled_at = (
            sample_event.scheduled_at
            if sample_event.scheduled_at.tzinfo
            else sample_event.scheduled_at.replace(tzinfo=timezone.utc)
        )

        hours_until = (
            scheduled_at - now
        ).total_seconds() / 3600

        assert 23 <= hours_until <= 25

        # ============================================================
        # 3. RUN MACRO ALERT ENGINE
        # ============================================================

        engine = MacroAlertEngine(db_session)

        triggered_events = engine.check_upcoming_events()

        assert len(triggered_events) == 1

        triggered_event = triggered_events[0]

        assert triggered_event["event"].id == sample_event.id
        assert triggered_event["timing"] == "1d"

        # ============================================================
        # 4. VERIFY MACRO ALERT WAS CREATED
        # ============================================================

        alert = (
            db_session.query(MacroEventAlert)
            .filter(
                MacroEventAlert.user_id == test_user_id,
                MacroEventAlert.event_id == sample_event.id,
            )
            .first()
        )

        assert alert is not None
        assert alert.user_id == test_user_id
        assert alert.event_id == sample_event.id
        assert alert.event_type == EventType.FED
        assert alert.timing.value == "1d"
        assert alert.impact_filter == EventImpact.HIGH
        assert alert.status == MacroAlertStatus.TRIGGERED
        assert alert.triggered_at is not None

        # ============================================================
        # 5. VERIFY MACRO NOTIFICATION WAS CREATED
        # ============================================================

        notification = (
            db_session.query(MacroEventNotification)
            .filter(
                MacroEventNotification.user_id == test_user_id,
                MacroEventNotification.alert_id == alert.id,
            )
            .first()
        )

        assert notification is not None

        assert notification.user_id == test_user_id
        assert notification.alert_id == alert.id
        assert notification.event_name == sample_event.event_name
        assert notification.event_type == "fed"
        assert notification.timing == "1d"
        assert notification.impact == "high"
        assert notification.read is False
        assert notification.is_archived is False
        assert notification.sent_at is not None

        # Verify notification payload contains the alert/event IDs.
        assert notification.data is not None
        assert notification.data["alert_id"] == str(alert.id)
        assert notification.data["event_name"] == sample_event.event_name
        assert notification.data["event_type"] == "fed"
        assert notification.data["timing"] == "1d"
        assert notification.data["impact"] == "high"

        # ============================================================
        # 6. VERIFY ALL-NOTIFICATIONS API
        # ============================================================

        response = client.get(
            "/api/v1/macro/notifications"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["notifications"]) == 1

        api_notification = data["notifications"][0]

        assert api_notification["id"] == str(notification.id)
        assert api_notification["user_id"] == str(test_user_id)
        assert api_notification["alert_id"] == str(alert.id)

        assert api_notification["event_name"] == sample_event.event_name
        assert api_notification["event_type"] == "fed"
        assert api_notification["timing"] == "1d"
        assert api_notification["impact"] == "high"

        assert api_notification["read"] is False
        assert api_notification["is_archived"] is False

        # ============================================================
        # 7. VERIFY UNREAD-NOTIFICATIONS API
        # ============================================================

        response = client.get(
            "/api/v1/macro/notifications/unread"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert len(data["notifications"]) == 1

        unread_notification = data["notifications"][0]

        assert unread_notification["id"] == str(notification.id)
        assert unread_notification["alert_id"] == str(alert.id)
        assert unread_notification["read"] is False

        # ============================================================
        # 8. MARK ALL NOTIFICATIONS AS READ
        # ============================================================

        response = client.post(
            "/api/v1/macro/notifications/read-all"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "success"
        assert data["message"] == "All notifications marked as read"
        assert data["count"] == 1

        # ============================================================
        # 9. VERIFY DATABASE STATE AFTER READ-ALL
        # ============================================================

        db_session.expire_all()

        notification = (
            db_session.query(MacroEventNotification)
            .filter(
                MacroEventNotification.id == notification.id
            )
            .first()
        )

        assert notification is not None
        assert notification.read is True
        assert notification.read_at is not None

        # ============================================================
        # 10. VERIFY UNREAD API IS NOW EMPTY
        # ============================================================

        response = client.get(
            "/api/v1/macro/notifications/unread"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 0
        assert data["notifications"] == []

        # ============================================================
        # 11. VERIFY ALL-NOTIFICATIONS STILL CONTAINS IT
        # ============================================================

        response = client.get(
            "/api/v1/macro/notifications"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["id"] == str(notification.id)
        assert data["notifications"][0]["read"] is True

    def test_subscription_does_not_receive_lower_impact_event(
        self,
        db_session,
        test_user_id,
    ):
        """
        Verify a HIGH-impact subscription does not receive a LOW-impact
        macro event.
        """

        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=test_user_id,
            event_type=EventType.FED,
            subscribed=True,
            impact_filter=EventImpact.HIGH,
        )

        event = MacroEventCache(
            id=uuid4(),
            event_id=f"e2e_low_event_{uuid4()}",
            event_type=EventType.FED,
            event_name="Low Impact Fed Event",
            description="Low impact test event.",
            scheduled_at=datetime.now(timezone.utc) + timedelta(hours=24),
            timezone="UTC",
            impact=EventImpact.LOW,
            notified=False,
        )

        db_session.add(subscription)
        db_session.add(event)
        db_session.commit()

        engine = MacroAlertEngine(db_session)

        triggered_events = engine.check_upcoming_events()

        assert triggered_events == []

        alert = (
            db_session.query(MacroEventAlert)
            .filter(
                MacroEventAlert.user_id == test_user_id,
                MacroEventAlert.event_id == event.id,
            )
            .first()
        )

        assert alert is None

        notification = (
            db_session.query(MacroEventNotification)
            .filter(
                MacroEventNotification.user_id == test_user_id,
            )
            .first()
        )

        assert notification is None

    def test_unsubscribed_user_does_not_receive_notification(
        self,
        db_session,
        test_user_id,
    ):
        """
        Verify an unsubscribed user does not receive macro notifications.
        """

        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=test_user_id,
            event_type=EventType.FED,
            subscribed=False,
            impact_filter=EventImpact.HIGH,
        )

        event = MacroEventCache(
            id=uuid4(),
            event_id=f"e2e_unsubscribed_event_{uuid4()}",
            event_type=EventType.FED,
            event_name="Unsubscribed Fed Event",
            description="Unsubscribed user test event.",
            scheduled_at=datetime.now(timezone.utc) + timedelta(hours=24),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(subscription)
        db_session.add(event)
        db_session.commit()

        engine = MacroAlertEngine(db_session)

        triggered_events = engine.check_upcoming_events()

        assert triggered_events == []

        alert = (
            db_session.query(MacroEventAlert)
            .filter(
                MacroEventAlert.user_id == test_user_id,
                MacroEventAlert.event_id == event.id,
            )
            .first()
        )

        assert alert is None

        notification = (
            db_session.query(MacroEventNotification)
            .filter(
                MacroEventNotification.user_id == test_user_id,
            )
            .first()
        )

        assert notification is None

