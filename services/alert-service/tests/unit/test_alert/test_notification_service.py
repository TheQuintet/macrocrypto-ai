"""Unit tests for notification service"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.services.notification_service import NotificationService
from app.models.alert import InAppNotification, NotificationType


class TestNotificationService:
    """Test cases for NotificationService."""

    @pytest.fixture
    def notification_service(self, db_session):
        """Create notification service instance."""
        return NotificationService(db_session)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid4()

    @pytest.fixture
    def sample_alert_id(self):
        """Sample alert ID for testing."""
        return uuid4()

    def test_create_notification(
        self, notification_service, db_session, sample_user_id, sample_alert_id
    ):
        """Test creating a notification."""
        notification = notification_service.create_notification(
            user_id=sample_user_id,
            alert_id=sample_alert_id,
            title="Test Alert",
            message="This is a test alert",
            notification_type=NotificationType.PRICE_ALERT,
            data={"price": 85000.00},
            action_url="/alerts/test"
        )

        assert notification is not None
        assert notification.user_id == sample_user_id
        assert notification.alert_id == sample_alert_id
        assert notification.title == "Test Alert"
        assert notification.message == "This is a test alert"
        assert notification.notification_type == NotificationType.PRICE_ALERT
        assert notification.read == False
        assert notification.is_archived == False

    def test_get_notifications(
        self, notification_service, db_session, sample_user_id, sample_alert_id
    ):
        """Test getting notifications for a user."""
        # Create multiple notifications
        for i in range(3):
            notification_service.create_notification(
                user_id=sample_user_id,
                alert_id=sample_alert_id,
                title=f"Alert {i}",
                message=f"Alert message {i}",
                notification_type=NotificationType.PRICE_ALERT
            )

        total, notifications = notification_service.get_notifications(
            user_id=sample_user_id,
            limit=10,
            offset=0
        )

        assert total == 3
        assert len(notifications) == 3

    def test_get_notifications_unread_only(
        self, notification_service, db_session, sample_user_id, sample_alert_id
    ):
        """Test getting only unread notifications."""
        # Create notifications
        for i in range(5):
            notification_service.create_notification(
                user_id=sample_user_id,
                alert_id=sample_alert_id,
                title=f"Alert {i}",
                message=f"Alert message {i}",
                notification_type=NotificationType.PRICE_ALERT
            )

        # Mark some as read
        total, notifications = notification_service.get_notifications(
            user_id=sample_user_id,
            limit=10,
            offset=0
        )
        for i, notif in enumerate(notifications[:2]):
            notification_service.mark_as_read(notif.id)

        total, unread = notification_service.get_notifications(
            user_id=sample_user_id,
            unread_only=True,
            limit=10,
            offset=0
        )

        assert total == 3  # 3 unread (5 total - 2 read)

    def test_mark_notification_as_read(
        self, notification_service, db_session, sample_user_id, sample_alert_id
    ):
        """Test marking a notification as read."""
        notification = notification_service.create_notification(
            user_id=sample_user_id,
            alert_id=sample_alert_id,
            title="Test Alert",
            message="Test message",
            notification_type=NotificationType.PRICE_ALERT
        )

        assert notification.read == False
        assert notification.read_at is None

        updated = notification_service.mark_as_read(notification.id)

        assert updated is not None
        assert updated.read == True
        assert updated.read_at is not None

    def test_mark_all_as_read(
        self, notification_service, db_session, sample_user_id, sample_alert_id
    ):
        """Test marking all notifications as read."""
        # Create multiple notifications
        for i in range(5):
            notification_service.create_notification(
                user_id=sample_user_id,
                alert_id=sample_alert_id,
                title=f"Alert {i}",
                message=f"Alert message {i}",
                notification_type=NotificationType.PRICE_ALERT
            )

        count = notification_service.mark_all_as_read(sample_user_id)

        assert count == 5

        # Verify all are read
        total, notifications = notification_service.get_notifications(
            user_id=sample_user_id,
            limit=10,
            offset=0
        )

        for notif in notifications:
            assert notif.read == True

    def test_get_unread_count(
        self, notification_service, db_session, sample_user_id, sample_alert_id
    ):
        """Test getting unread notification count."""
        # Create notifications
        for i in range(5):
            notification_service.create_notification(
                user_id=sample_user_id,
                alert_id=sample_alert_id,
                title=f"Alert {i}",
                message=f"Alert message {i}",
                notification_type=NotificationType.PRICE_ALERT
            )

        # Mark some as read
        total, notifications = notification_service.get_notifications(
            user_id=sample_user_id,
            limit=10,
            offset=0
        )
        for i, notif in enumerate(notifications[:2]):
            notification_service.mark_as_read(notif.id)

        unread_count = notification_service.get_unread_count(sample_user_id)

        assert unread_count == 3