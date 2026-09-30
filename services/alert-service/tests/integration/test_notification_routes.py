"""Tests for unified notification API routes."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.api.notifications import (
    get_db,
    get_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


@pytest.fixture
def db():
    """Provide a mocked database session."""
    return MagicMock()


@pytest.fixture
def notification():
    """Provide a mocked notification model."""
    item = MagicMock()
    item.to_dict.return_value = {
        "id": str(uuid4()),
        "title": "Test notification",
        "message": "Test message",
        "read": False,
    }
    return item


class TestGetNotifications:
    """Tests for GET /api/v1/notifications."""

    @pytest.mark.asyncio
    async def test_returns_notifications(self, db, notification):
        """Return total count and serialized notifications."""
        service = MagicMock()
        service.get_all_notifications.return_value = (
            1,
            [notification],
        )

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ) as service_class:
            result = await get_notifications(db=db)

        service_class.assert_called_once_with(db)
        service.get_all_notifications.assert_called_once_with()
        notification.to_dict.assert_called_once_with()

        assert result == {
            "total": 1,
            "notifications": [
                notification.to_dict.return_value,
            ],
        }

    @pytest.mark.asyncio
    async def test_returns_empty_notifications(self, db):
        """Return an empty list when there are no notifications."""
        service = MagicMock()
        service.get_all_notifications.return_value = (0, [])

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ):
            result = await get_notifications(db=db)

        assert result == {
            "total": 0,
            "notifications": [],
        }

    @pytest.mark.asyncio
    async def test_serializes_multiple_notifications(self, db):
        """Serialize every notification returned by the service."""
        first = MagicMock()
        first.to_dict.return_value = {"id": "first"}

        second = MagicMock()
        second.to_dict.return_value = {"id": "second"}

        service = MagicMock()
        service.get_all_notifications.return_value = (
            2,
            [first, second],
        )

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ):
            result = await get_notifications(db=db)

        assert result["total"] == 2
        assert result["notifications"] == [
            {"id": "first"},
            {"id": "second"},
        ]
        first.to_dict.assert_called_once_with()
        second.to_dict.assert_called_once_with()


class TestMarkNotificationAsRead:
    """Tests for PUT /api/v1/notifications/{notification_id}/read."""

    @pytest.mark.asyncio
    async def test_marks_notification_as_read(self, db, notification):
        """Return the serialized notification when found."""
        notification_id = uuid4()
        service = MagicMock()
        service.mark_as_read.return_value = notification

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ) as service_class:
            result = await mark_notification_as_read(
                notification_id=notification_id,
                db=db,
            )

        service_class.assert_called_once_with(db)
        service.mark_as_read.assert_called_once_with(
            notification_id
        )
        notification.to_dict.assert_called_once_with()

        assert result == {
            "success": True,
            "notification": notification.to_dict.return_value,
        }

    @pytest.mark.asyncio
    async def test_returns_not_found_when_notification_missing(self, db):
        """Return a failure response when no notification exists."""
        notification_id = uuid4()
        service = MagicMock()
        service.mark_as_read.return_value = None

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ):
            result = await mark_notification_as_read(
                notification_id=notification_id,
                db=db,
            )

        assert result == {
            "success": False,
            "message": "Notification not found",
        }

    @pytest.mark.asyncio
    async def test_passes_notification_id_to_service(self, db):
        """Pass the requested UUID to the service unchanged."""
        notification_id = uuid4()
        service = MagicMock()
        service.mark_as_read.return_value = None

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ):
            await mark_notification_as_read(
                notification_id=notification_id,
                db=db,
            )

        service.mark_as_read.assert_called_once_with(
            notification_id
        )


class TestMarkAllNotificationsAsRead:
    """Tests for POST /api/v1/notifications/read-all."""

    @pytest.mark.asyncio
    async def test_returns_updated_count(self, db):
        """Return the number of notifications marked as read."""
        service = MagicMock()
        service.mark_all_notifications_as_read.return_value = 5

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ) as service_class:
            result = await mark_all_notifications_as_read(db=db)

        service_class.assert_called_once_with(db)
        service.mark_all_notifications_as_read.assert_called_once_with()
        assert result == {"count": 5}

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_is_updated(self, db):
        """Return zero when no notifications need updating."""
        service = MagicMock()
        service.mark_all_notifications_as_read.return_value = 0

        with patch(
            "app.api.notifications.NotificationService",
            return_value=service,
        ):
            result = await mark_all_notifications_as_read(db=db)

        assert result == {"count": 0}


class TestGetDb:
    """Tests for the database dependency."""

    def test_yields_database_session(self):
        """Yield the session created by SessionLocal."""
        mock_db = MagicMock()

        with patch(
            "app.api.notifications.SessionLocal",
            return_value=mock_db,
        ) as session_local:
            generator = get_db()
            yielded_db = next(generator)

            assert yielded_db is mock_db
            session_local.assert_called_once_with()

            generator.close()

        mock_db.close.assert_called_once_with()

    def test_closes_session_when_generator_finishes(self):
        """Close the database session after normal completion."""
        mock_db = MagicMock()

        with patch(
            "app.api.notifications.SessionLocal",
            return_value=mock_db,
        ):
            generator = get_db()

            assert next(generator) is mock_db

            with pytest.raises(StopIteration):
                next(generator)

        mock_db.close.assert_called_once_with()