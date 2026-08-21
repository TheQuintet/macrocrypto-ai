"""Tests for prediction notification delivery"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.services.prediction_alert_engine import PredictionAlertEngine
from app.services.notification_service import NotificationService
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeHistory,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection
)
from app.models.alert import InAppNotification, NotificationType, PriceAlert, AlertType, AlertStatus


class TestPredictionNotification:
    """Test cases for prediction notification delivery."""

    @pytest.fixture
    def notification_service(self, db_session):
        """Create notification service instance."""
        return NotificationService(db_session)

    @pytest.fixture
    def sample_price_alert(self, db_session):
        """Create a sample price alert for FK reference."""
        alert = PriceAlert(
            id=uuid4(),
            user_id=uuid4(),
            threshold_price=85000.00,
            alert_type=AlertType.REACHES,
            asset="BTC/USD",
            status=AlertStatus.ACTIVE,
            one_time=True,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    @pytest.fixture
    def sample_alert(self, db_session, sample_price_alert):
        """Create a sample prediction alert for testing."""
        alert = PredictionChangeAlert(
            id=sample_price_alert.id,  # Reuse PriceAlert ID
            user_id=uuid4(),
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    def test_in_app_notification_created_on_trigger(
        self, notification_service, db_session, sample_alert
    ):
        """Test in-app notification is created when alert triggers."""
        # Create notification
        notification = notification_service.create_notification(
            user_id=sample_alert.user_id,
            alert_id=sample_alert.id,
            title="Prediction Change Alert",
            message="BTC prediction changed by 3.66%",
            notification_type=NotificationType.PREDICTION_ALERT,
            data={
                "previous_prediction": 82000.00,
                "new_prediction": 85000.00,
                "change_percent": 3.66
            },
            action_url=f"/alerts/prediction/{sample_alert.id}"
        )

        assert notification is not None
        assert notification.user_id == sample_alert.user_id
        assert notification.alert_id == sample_alert.id
        assert notification.title == "Prediction Change Alert"
        assert "3.66" in notification.message
        assert notification.notification_type == NotificationType.PREDICTION_ALERT
        assert notification.read is False

    def test_notification_read_status(
        self, notification_service, db_session, sample_alert
    ):
        """Test notification read status updates."""
        # Create notification
        notification = notification_service.create_notification(
            user_id=sample_alert.user_id,
            alert_id=sample_alert.id,
            title="Test Alert",
            message="Test message",
            notification_type=NotificationType.PREDICTION_ALERT
        )

        assert notification.read is False
        assert notification.read_at is None

        # Mark as read
        updated = notification_service.mark_as_read(notification.id)

        assert updated.read is True
        assert updated.read_at is not None

    def test_get_notifications_with_filtering(
        self, notification_service, db_session, sample_alert
    ):
        """Test getting notifications with filtering."""
        # Create multiple notifications
        for i in range(5):
            notification_service.create_notification(
                user_id=sample_alert.user_id,
                alert_id=sample_alert.id,
                title=f"Alert {i}",
                message=f"Message {i}",
                notification_type=NotificationType.PREDICTION_ALERT
            )

        # Get all notifications
        total, notifications = notification_service.get_notifications(
            user_id=sample_alert.user_id,
            limit=10,
            offset=0
        )

        assert total == 5
        assert len(notifications) == 5

        # Mark some as read
        for i, notif in enumerate(notifications[:2]):
            notification_service.mark_as_read(notif.id)

        # Get unread only
        total, unread = notification_service.get_notifications(
            user_id=sample_alert.user_id,
            unread_only=True,
            limit=10,
            offset=0
        )

        assert total == 3

    def test_unread_count(
        self, notification_service, db_session, sample_alert
    ):
        """Test getting unread notification count."""
        # Create notifications
        for i in range(5):
            notification_service.create_notification(
                user_id=sample_alert.user_id,
                alert_id=sample_alert.id,
                title=f"Alert {i}",
                message=f"Message {i}",
                notification_type=NotificationType.PREDICTION_ALERT
            )

        # Mark some as read
        total, notifications = notification_service.get_notifications(
            user_id=sample_alert.user_id,
            limit=10,
            offset=0
        )
        for notif in notifications[:2]:
            notification_service.mark_as_read(notif.id)

        unread_count = notification_service.get_unread_count(sample_alert.user_id)

        assert unread_count == 3

    def test_mark_all_notifications_read(
        self, notification_service, db_session, sample_alert
    ):
        """Test marking all notifications as read."""
        # Create notifications
        for i in range(5):
            notification_service.create_notification(
                user_id=sample_alert.user_id,
                alert_id=sample_alert.id,
                title=f"Alert {i}",
                message=f"Message {i}",
                notification_type=NotificationType.PREDICTION_ALERT
            )

        count = notification_service.mark_all_as_read(sample_alert.user_id)

        assert count == 5

        # Verify all are read
        total, notifications = notification_service.get_notifications(
            user_id=sample_alert.user_id,
            limit=10,
            offset=0
        )

        for notif in notifications:
            assert notif.read is True
            assert notif.read_at is not None

    def test_notification_storage_with_data(
        self, notification_service, db_session, sample_alert
    ):
        """Test notification storage with additional data."""
        notification = notification_service.create_notification(
            user_id=sample_alert.user_id,
            alert_id=sample_alert.id,
            title="Test Alert with Data",
            message="Alert with additional data",
            notification_type=NotificationType.PREDICTION_ALERT,
            data={
                "previous_prediction": 82000.00,
                "new_prediction": 85000.00,
                "change_percent": 3.66,
                "horizon": "24h"
            },
            action_url="/alerts/prediction/test"
        )

        assert notification.data is not None
        assert notification.data["previous_prediction"] == 82000.00
        assert notification.data["new_prediction"] == 85000.00
        assert notification.data["change_percent"] == 3.66
        assert notification.data["horizon"] == "24h"
        assert notification.action_url == "/alerts/prediction/test"