"""Integration tests for global macro notification APIs."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.macro_routes import get_db
from app.models.alert import (
    PriceAlert,
    AlertType,
    AlertStatus,
)
from app.models.macro_alert import (
    MacroEventAlert,
    MacroEventCache,
    MacroEventNotification,
    EventType,
    EventTiming,
    EventImpact,
    MacroAlertStatus,
)


class TestMacroNotificationAPI:
    """Test cases for global macro notification APIs."""

    @pytest.fixture
    def client(self, db_session: Session):
        """
        Create a FastAPI test client using the same database session
        as the test fixtures.

        This ensures that records created by db_session are visible
        to the API endpoints during the test.
        """

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)

        yield client

        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_price_alert(self, db_session: Session):
        """
        Create the parent PriceAlert required by MacroEventAlert.

        MacroEventAlert.id references PriceAlert.id, so the parent
        PriceAlert must exist first.
        """
        user_id = uuid4()

        alert = PriceAlert(
            id=uuid4(),
            user_id=user_id,
            threshold_price=85000.00,
            alert_type=AlertType.REACHES,
            asset="BTC/USD",
            status=AlertStatus.ACTIVE,
            one_time=True,
            notify_in_app=True,
            notify_email=True,
        )

        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        return alert

    @pytest.fixture
    def sample_macro_event(
        self,
        db_session: Session,
        sample_price_alert: PriceAlert,
    ):
        """
        Create a macro event cache entry.

        The event is created independently of the PriceAlert, while
        MacroEventAlert.event_id references this event.
        """
        event = MacroEventCache(
            id=uuid4(),
            event_id="test_event_001",
            event_type=EventType.FED.value,
            event_name="Federal Reserve Meeting",
            description="FOMC interest rate decision and economic projections",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        return event

    @pytest.fixture
    def sample_macro_alert(
        self,
        db_session: Session,
        sample_price_alert: PriceAlert,
        sample_macro_event: MacroEventCache,
    ):
        """
        Create a macro event alert with valid FK relationships.

        MacroEventAlert.event_id references MacroEventCache.id.
        """
        alert = MacroEventAlert(
            id=uuid4(),
            user_id=sample_price_alert.user_id,
            event_id=sample_macro_event.id,
            event_type=EventType.FED,
            timing=EventTiming.ONE_DAY,
            impact_filter=EventImpact.HIGH,
            status=MacroAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True,
        )

        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        return alert

    @pytest.fixture
    def sample_notifications(
        self,
        db_session: Session,
        sample_macro_alert: MacroEventAlert,
        sample_macro_event: MacroEventCache,
    ):
        """
        Create macro notifications using the actual macro alert ID.
        """
        notification = MacroEventNotification(
            id=uuid4(),
            user_id=sample_macro_alert.user_id,
            alert_id=sample_macro_alert.id,
            event_name=sample_macro_event.event_name,
            event_type=sample_macro_event.event_type.value,
            event_date=sample_macro_event.scheduled_at,
            timing=EventTiming.ONE_DAY.value,
            impact=sample_macro_event.impact.value,
            description=sample_macro_event.description,
            data={
                "alert_id": str(sample_macro_alert.id),
                "event_name": sample_macro_event.event_name,
                "event_type": sample_macro_event.event_type.value,
                "event_date": (
                    sample_macro_event.scheduled_at.isoformat()
                ),
                "timing": EventTiming.ONE_DAY.value,
                "impact": sample_macro_event.impact.value,
                "description": sample_macro_event.description,
            },
            action_url=f"/alerts/macro/{sample_macro_alert.id}",
            read=False,
            is_archived=False,
            sent_at=datetime.utcnow(),
        )

        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        return [notification]

    @pytest.fixture
    def archived_notification(
        self,
        db_session: Session,
        sample_macro_alert: MacroEventAlert,
        sample_macro_event: MacroEventCache,
    ):
        """Create an archived notification that should not be returned."""

        notification = MacroEventNotification(
            id=uuid4(),
            user_id=sample_macro_alert.user_id,
            alert_id=sample_macro_alert.id,
            event_name="Archived Event",
            event_type=EventType.GDP.value,
            event_date=sample_macro_event.scheduled_at,
            timing=EventTiming.ONE_DAY.value,
            impact=EventImpact.MEDIUM.value,
            description="Archived macro event",
            data={},
            action_url=f"/alerts/macro/{sample_macro_alert.id}",
            read=False,
            is_archived=True,
            sent_at=datetime.utcnow(),
        )

        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        return notification

    # ============================================
    # GET ALL NOTIFICATIONS
    # ============================================

    def test_get_all_macro_notifications(
        self,
        client,
        sample_notifications,
    ):
        """Test GET /api/v1/macro/notifications."""

        response = client.get(
            "/api/v1/macro/notifications"
        )

        assert response.status_code == 200

        data = response.json()

        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "notifications" in data

        assert data["total"] == 1
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["notifications"]) == 1

        notification = data["notifications"][0]

        assert notification["event_name"] == "Federal Reserve Meeting"
        assert notification["event_type"] == "fed"
        assert notification["timing"] == "1d"
        assert notification["impact"] == "high"
        assert notification["read"] is False
        assert notification["is_archived"] is False

    def test_get_all_macro_notifications_with_pagination(
        self,
        client,
        sample_notifications,
    ):
        """Test pagination for GET /api/v1/macro/notifications."""

        response = client.get(
            "/api/v1/macro/notifications",
            params={
                "limit": 1,
                "offset": 0,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["limit"] == 1
        assert data["offset"] == 0
        assert len(data["notifications"]) == 1

    # ============================================
    # GET UNREAD NOTIFICATIONS
    # ============================================

    def test_get_unread_macro_notifications(
        self,
        client,
        sample_notifications,
    ):
        """Test GET /api/v1/macro/notifications/unread."""

        response = client.get(
            "/api/v1/macro/notifications/unread"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert len(data["notifications"]) == 1

        notification = data["notifications"][0]

        assert notification["event_name"] == "Federal Reserve Meeting"
        assert notification["event_type"] == "fed"
        assert notification["timing"] == "1d"
        assert notification["impact"] == "high"
        assert notification["read"] is False
        assert notification["is_archived"] is False

    def test_unread_notifications_exclude_read_notifications(
        self,
        client,
        db_session,
        sample_notifications,
    ):
        """Test that unread endpoint excludes read notifications."""

        notification = sample_notifications[0]

        notification.read = True
        notification.read_at = datetime.utcnow()

        db_session.commit()

        response = client.get(
            "/api/v1/macro/notifications/unread"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 0
        assert data["notifications"] == []

    # ============================================
    # ARCHIVED NOTIFICATIONS
    # ============================================

    def test_notifications_exclude_archived_notifications(
        self,
        client,
        sample_notifications,
        archived_notification,
    ):
        """Test that archived notifications are excluded."""

        response = client.get(
            "/api/v1/macro/notifications"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert len(data["notifications"]) == 1

        notification_names = [
            notification["event_name"]
            for notification in data["notifications"]
        ]

        assert "Federal Reserve Meeting" in notification_names
        assert "Archived Event" not in notification_names

    def test_unread_notifications_exclude_archived_notifications(
        self,
        client,
        sample_notifications,
        archived_notification,
    ):
        """Test that archived notifications are excluded from unread results."""

        response = client.get(
            "/api/v1/macro/notifications/unread"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1

        notification_names = [
            notification["event_name"]
            for notification in data["notifications"]
        ]

        assert "Federal Reserve Meeting" in notification_names
        assert "Archived Event" not in notification_names

    # ============================================
    # READ ALL
    # ============================================

    def test_mark_all_macro_notifications_as_read(
        self,
        client,
        db_session,
        sample_notifications,
    ):
        """Test POST /api/v1/macro/notifications/read-all."""

        response = client.post(
            "/api/v1/macro/notifications/read-all"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "success"
        assert data["message"] == "All notifications marked as read"
        assert data["count"] == 1

        notification = sample_notifications[0]

        db_session.refresh(notification)

        assert notification.read is True
        assert notification.read_at is not None

    def test_mark_all_notifications_when_none_are_unread(
        self,
        client,
        db_session,
        sample_notifications,
    ):
        """Test read-all when all notifications are already read."""

        notification = sample_notifications[0]

        notification.read = True
        notification.read_at = datetime.utcnow()

        db_session.commit()

        response = client.post(
            "/api/v1/macro/notifications/read-all"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "success"
        assert data["count"] == 0

    def test_mark_all_notifications_does_not_modify_archived(
        self,
        client,
        db_session,
        sample_notifications,
        archived_notification,
    ):
        """Test that read-all does not modify archived notifications."""

        archived_notification.read = False
        db_session.commit()

        response = client.post(
            "/api/v1/macro/notifications/read-all"
        )

        assert response.status_code == 200

        db_session.refresh(archived_notification)

        assert archived_notification.read is False
        assert archived_notification.read_at is None

    # ============================================
    # PAGINATION
    # ============================================

    def test_notification_pagination_offset(
        self,
        client,
        sample_notifications,
    ):
        """Test notification pagination using offset."""

        response = client.get(
            "/api/v1/macro/notifications",
            params={
                "limit": 1,
                "offset": 1,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["limit"] == 1
        assert data["offset"] == 1
        assert len(data["notifications"]) == 0

    def test_unread_notification_pagination(
        self,
        client,
        sample_notifications,
    ):
        """Test pagination for unread notifications."""

        response = client.get(
            "/api/v1/macro/notifications/unread",
            params={
                "limit": 1,
                "offset": 0,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["limit"] == 1
        assert data["offset"] == 0
        assert len(data["notifications"]) == 1

    # ============================================
    # VALIDATION
    # ============================================

    def test_invalid_limit(
        self,
        client,
        sample_notifications,
    ):
        """Test validation for invalid notification limit."""

        response = client.get(
            "/api/v1/macro/notifications",
            params={
                "limit": 0,
            },
        )

        assert response.status_code == 422

    def test_limit_above_maximum(
        self,
        client,
        sample_notifications,
    ):
        """Test validation when notification limit exceeds maximum."""

        response = client.get(
            "/api/v1/macro/notifications",
            params={
                "limit": 101,
            },
        )

        assert response.status_code == 422

    def test_negative_offset(
        self,
        client,
        sample_notifications,
    ):
        """Test validation for negative notification offset."""

        response = client.get(
            "/api/v1/macro/notifications",
            params={
                "offset": -1,
            },
        )

        assert response.status_code == 422

