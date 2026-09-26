"""End-to-end tests for macro alert notifications."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.macro_routes import get_db as macro_get_db
from app.api.notifications import get_db as notification_get_db
from app.main import app
from app.models.alert import InAppNotification
from app.models.macro_alert import (
    EventImpact,
    EventType,
    MacroEventAlert,
    MacroEventCache,
    MacroEventSubscription,
)
from app.services.macro_alert_engine import MacroAlertEngine


class TestMacroNotificationE2E:
    """End-to-end tests for macro alert notification flow."""

    @pytest.fixture
    def client(self, db_session):
        """Create a test client using the test database session."""

        def override_get_db():
            try:
                yield db_session
            finally:
                pass

        # Both APIs must use the same test database session.
        app.dependency_overrides[macro_get_db] = override_get_db
        app.dependency_overrides[notification_get_db] = override_get_db

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()

    def test_subscription_to_notification_flow(
        self,
        client,
        db_session,
    ):
        """Verify subscribed users receive unified macro notifications."""

        # ============================================================
        # 1. CREATE TEST USER
        # ============================================================

        test_user_id = uuid4()

        # ============================================================
        # 2. CREATE UPCOMING MACRO EVENT
        # ============================================================

        event_date = datetime.utcnow() + timedelta(days=1)

        sample_event = MacroEventCache(
            id=uuid4(),
            event_id=str(uuid4()),
            event_name="E2E Federal Reserve Meeting",
            event_type=EventType.FED,
            scheduled_at=event_date,
            description="Federal Reserve meeting scheduled for tomorrow.",
            impact=EventImpact.HIGH,
        )

        db_session.add(sample_event)
        db_session.commit()
        db_session.refresh(sample_event)

        # ============================================================
        # 3. CREATE USER SUBSCRIPTION
        # ============================================================

        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=test_user_id,
            event_type=EventType.FED,
            impact_filter=EventImpact.HIGH,
            subscribed=True,
        )

        db_session.add(subscription)
        db_session.commit()

        # ============================================================
        # 4. RUN MACRO ALERT ENGINE
        # ============================================================

        engine = MacroAlertEngine(db_session)

        engine.check_upcoming_events()

        # ============================================================
        # 5. VERIFY UNIFIED NOTIFICATION WAS CREATED
        # ============================================================

        alert = (
            engine.db.query(MacroEventAlert)
            .filter(
                MacroEventAlert.user_id == test_user_id,
                MacroEventAlert.event_id == sample_event.id,
            )
            .first()
        )

        assert alert is not None
        assert alert.user_id == test_user_id
        assert alert.event_id == sample_event.id

        notification = (
            db_session.query(InAppNotification)
            .filter(
                InAppNotification.user_id == test_user_id,
                InAppNotification.alert_id == alert.id,
                InAppNotification.notification_type == "macro_alert",
            )
            .first()
        )

        assert notification is not None

        assert notification.user_id == test_user_id
        assert notification.alert_id == alert.id
        assert notification.notification_type.value == "macro_alert"
        assert notification.read is False
        assert notification.is_archived is False
        assert notification.created_at is not None

        # Verify notification payload contains the alert/event data.
        assert notification.data is not None
        assert notification.data["alert_id"] == str(alert.id)
        assert notification.data["event_name"] == sample_event.event_name
        assert notification.data["event_type"] == "fed"
        assert notification.data["timing"] == "1d"
        assert notification.data["impact"] == "high"

        # ============================================================
        # 6. VERIFY UNIFIED ALL-NOTIFICATIONS API
        # ============================================================

        response = client.get(
            "/api/v1/notifications"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert len(data["notifications"]) == 1

        api_notification = data["notifications"][0]

        assert api_notification["id"] == str(notification.id)
        assert api_notification["user_id"] == str(test_user_id)
        assert api_notification["alert_id"] == str(alert.id)
        assert api_notification["notification_type"] == "macro_alert"
        assert api_notification["read"] is False
        assert api_notification["is_archived"] is False

        # ============================================================
        # 7. MARK ALL NOTIFICATIONS AS READ
        # ============================================================

        response = client.post(
            "/api/v1/notifications/read-all"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1

        # ============================================================
        # 8. VERIFY NOTIFICATION IS MARKED AS READ
        # ============================================================

        db_session.expire_all()

        notification = (
            db_session.query(InAppNotification)
            .filter(
                InAppNotification.id == notification.id,
            )
            .first()
        )

        assert notification is not None
        assert notification.read is True
        assert notification.read_at is not None

        # ============================================================
        # 9. VERIFY UNIFIED API RETURNS UPDATED READ STATE
        # ============================================================

        response = client.get(
            "/api/v1/notifications"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["read"] is True

    def test_subscription_does_not_receive_lower_impact_event(
        self,
        client,
        db_session,
    ):
        """Verify impact filtering prevents unwanted notifications."""

        test_user_id = uuid4()

        event_date = datetime.utcnow() + timedelta(days=1)

        sample_event = MacroEventCache(
            id=uuid4(),
            event_id=str(uuid4()),
            event_name="E2E Low Impact Event",
            event_type=EventType.FED,
            scheduled_at=event_date,
            description="Low impact Federal Reserve event.",
            impact=EventImpact.LOW,
        )

        db_session.add(sample_event)
        db_session.commit()
        db_session.refresh(sample_event)

        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=test_user_id,
            event_type=EventType.FED,
            impact_filter=EventImpact.HIGH,
            subscribed=True,
        )

        db_session.add(subscription)
        db_session.commit()

        engine = MacroAlertEngine(db_session)

        engine.check_upcoming_events()

        notification = (
            db_session.query(InAppNotification)
            .filter(
                InAppNotification.user_id == test_user_id,
                InAppNotification.notification_type == "macro_alert",
            )
            .first()
        )

        assert notification is None

    def test_unsubscribed_user_does_not_receive_notification(
        self,
        client,
        db_session,
    ):
        """Verify disabled subscriptions do not receive notifications."""

        test_user_id = uuid4()

        event_date = datetime.utcnow() + timedelta(days=1)

        sample_event = MacroEventCache(
            id=uuid4(),
            event_id=str(uuid4()),
            event_name="E2E Unsubscribed Event",
            event_type=EventType.FED,
            scheduled_at=event_date,
            description="Event for a disabled subscription.",
            impact=EventImpact.HIGH,
        )

        db_session.add(sample_event)
        db_session.commit()
        db_session.refresh(sample_event)

        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=test_user_id,
            event_type=EventType.FED,
            impact_filter=EventImpact.HIGH,
            subscribed=False,
        )

        db_session.add(subscription)
        db_session.commit()

        engine = MacroAlertEngine(db_session)

        engine.check_upcoming_events()

        notification = (
            db_session.query(InAppNotification)
            .filter(
                InAppNotification.user_id == test_user_id,
                InAppNotification.notification_type == "macro_alert",
            )
            .first()
        )

        assert notification is None

