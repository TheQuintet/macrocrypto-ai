"""Tests for MacroNotificationService."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.macro_notification_service import (
    MacroNotificationService,
)


@pytest.fixture
def db():
    """Provide a mocked database session."""
    return MagicMock()


@pytest.fixture
def service(db):
    """Create a MacroNotificationService with a mocked database."""
    with patch(
        "app.services.macro_notification_service.NotificationService"
    ) as notification_service:
        instance = MacroNotificationService(db)
        instance.notification_service = notification_service.return_value
        return instance


@pytest.fixture
def user_id():
    """Provide a user UUID."""
    return uuid4()


@pytest.fixture
def alert_id():
    """Provide an alert UUID."""
    return uuid4()


@pytest.fixture
def notification():
    """Provide a mocked macro notification."""
    item = MagicMock()
    item.id = uuid4()
    item.read = False
    item.is_archived = False
    item.sent_at = datetime(2026, 1, 1)
    return item


def mock_query(
    db,
    result=None,
    count=0,
):
    """Configure a chainable mocked SQLAlchemy query."""
    query = MagicMock()

    db.query.return_value = query

    query.filter.return_value = query
    query.order_by.return_value = query
    query.offset.return_value = query
    query.limit.return_value = query

    query.count.return_value = count
    query.all.return_value = result or []
    query.first.return_value = result

    return query


class TestInit:
    """Tests for service initialization."""

    def test_initializes_database_and_notification_service(self, db):
        """Initialize the service with the database session."""
        with patch(
            "app.services.macro_notification_service.NotificationService"
        ) as notification_service:
            service = MacroNotificationService(db)

        assert service.db is db
        notification_service.assert_called_once_with(db)
        assert (
            service.notification_service
            is notification_service.return_value
        )


class TestCreateMacroNotification:
    """Tests for creating macro notifications."""

    def test_creates_notification_with_default_title_and_message(
        self,
        service,
        user_id,
        alert_id,
    ):
        """Use event name and description as defaults."""
        created_notification = MagicMock()
        created_notification.id = uuid4()

        service.notification_service.create_notification.return_value = (
            created_notification
        )

        event_date = datetime(2026, 10, 1, 12, 30)

        result = service.create_macro_notification(
            user_id=user_id,
            alert_id=alert_id,
            event_name="CPI Release",
            event_type="inflation",
            event_date=event_date,
            timing="upcoming",
            impact="high",
            description="CPI data will be released.",
        )

        assert result is created_notification

        service.notification_service.create_notification.assert_called_once_with(
            user_id=user_id,
            alert_id=alert_id,
            title="CPI Release",
            message="CPI data will be released.",
            notification_type="macro_alert",
            data={
                "event_name": "CPI Release",
                "event_type": "inflation",
                "event_date": event_date.isoformat(),
                "timing": "upcoming",
                "impact": "high",
                "description": "CPI data will be released.",
            },
            action_url=None,
        )

    def test_creates_notification_with_custom_title_and_message(
        self,
        service,
        user_id,
        alert_id,
    ):
        """Use explicitly supplied title and message."""
        created_notification = MagicMock()

        service.notification_service.create_notification.return_value = (
            created_notification
        )

        event_date = datetime(2026, 10, 1)

        result = service.create_macro_notification(
            user_id=user_id,
            alert_id=alert_id,
            event_name="Fed Meeting",
            event_type="monetary_policy",
            event_date=event_date,
            timing="tomorrow",
            impact="high",
            description="Federal Reserve meeting.",
            data={"rate": 5.0},
            action_url="/macro/fed",
            title="Important Fed Event",
            message="Fed meeting tomorrow.",
        )

        assert result is created_notification

        service.notification_service.create_notification.assert_called_once_with(
            user_id=user_id,
            alert_id=alert_id,
            title="Important Fed Event",
            message="Fed meeting tomorrow.",
            notification_type="macro_alert",
            data={
                "event_name": "Fed Meeting",
                "event_type": "monetary_policy",
                "event_date": event_date.isoformat(),
                "timing": "tomorrow",
                "impact": "high",
                "description": "Federal Reserve meeting.",
                "rate": 5.0,
            },
            action_url="/macro/fed",
        )

    def test_handles_missing_description_and_data(
        self,
        service,
        user_id,
        alert_id,
    ):
        """Handle optional description and data values."""
        created_notification = MagicMock()

        service.notification_service.create_notification.return_value = (
            created_notification
        )

        event_date = datetime(2026, 10, 1)

        service.create_macro_notification(
            user_id=user_id,
            alert_id=alert_id,
            event_name="GDP Release",
            event_type="economic",
            event_date=event_date,
            timing="today",
            impact="medium",
        )

        service.notification_service.create_notification.assert_called_once_with(
            user_id=user_id,
            alert_id=alert_id,
            title="GDP Release",
            message="GDP Release",
            notification_type="macro_alert",
            data={
                "event_name": "GDP Release",
                "event_type": "economic",
                "event_date": event_date.isoformat(),
                "timing": "today",
                "impact": "medium",
                "description": None,
            },
            action_url=None,
        )


class TestGetMacroNotifications:
    """Tests for user-scoped macro notifications."""

    def test_returns_notifications(
        self,
        service,
        user_id,
        notification,
    ):
        """Return notifications and total count."""
        query = mock_query(
            service.db,
            result=[notification],
            count=1,
        )

        total, notifications = service.get_macro_notifications(
            user_id=user_id,
        )

        assert total == 1
        assert notifications == [notification]

        query.count.assert_called_once_with()
        query.order_by.assert_called_once()
        query.offset.assert_called_once_with(0)
        query.limit.assert_called_once_with(50)
        query.all.assert_called_once_with()

    def test_returns_empty_notifications(
        self,
        service,
        user_id,
    ):
        """Return an empty result when there are no notifications."""
        mock_query(
            service.db,
            result=[],
            count=0,
        )

        total, notifications = service.get_macro_notifications(
            user_id=user_id,
        )

        assert total == 0
        assert notifications == []

    def test_filters_unread_notifications(
        self,
        service,
        user_id,
        notification,
    ):
        """Apply unread filter when requested."""
        query = mock_query(
            service.db,
            result=[notification],
            count=1,
        )

        service.get_macro_notifications(
            user_id=user_id,
            unread_only=True,
        )

        assert query.filter.call_count == 2

    def test_applies_pagination(
        self,
        service,
        user_id,
        notification,
    ):
        """Apply requested limit and offset."""
        query = mock_query(
            service.db,
            result=[notification],
            count=25,
        )

        total, notifications = service.get_macro_notifications(
            user_id=user_id,
            limit=10,
            offset=20,
        )

        assert total == 25
        assert notifications == [notification]

        query.offset.assert_called_once_with(20)
        query.limit.assert_called_once_with(10)


class TestMarkAsRead:
    """Tests for marking individual notifications as read."""

    def test_marks_unread_notification_as_read(
        self,
        service,
        notification,
    ):
        """Mark an unread notification as read."""
        notification.read = False

        mock_query(
            service.db,
            result=notification,
        )

        notification_id = notification.id

        result = service.mark_as_read(notification_id)

        assert result is notification
        assert notification.read is True
        assert isinstance(notification.read_at, datetime)

        service.db.commit.assert_called_once_with()
        service.db.refresh.assert_called_once_with(notification)

    def test_returns_already_read_notification_without_update(
        self,
        service,
        notification,
    ):
        """Do not update a notification that is already read."""
        notification.read = True

        mock_query(
            service.db,
            result=notification,
        )

        result = service.mark_as_read(notification.id)

        assert result is notification
        assert notification.read is True

        service.db.commit.assert_not_called()
        service.db.refresh.assert_not_called()

    def test_returns_none_when_notification_not_found(
        self,
        service,
    ):
        """Return None when the notification does not exist."""
        notification_id = uuid4()

        mock_query(
            service.db,
            result=None,
        )

        result = service.mark_as_read(notification_id)

        assert result is None
        service.db.commit.assert_not_called()
        service.db.refresh.assert_not_called()


class TestMarkAllAsRead:
    """Tests for marking user notifications as read."""

    def test_marks_all_unread_notifications_as_read(
        self,
        service,
        user_id,
    ):
        """Mark every matching notification as read."""
        first = MagicMock()
        first.read = False

        second = MagicMock()
        second.read = False

        mock_query(
            service.db,
            result=[first, second],
        )

        result = service.mark_all_as_read(user_id)

        assert result == 2

        assert first.read is True
        assert second.read is True

        assert isinstance(first.read_at, datetime)
        assert isinstance(second.read_at, datetime)

        service.db.commit.assert_called_once_with()

    def test_returns_zero_when_no_notifications(
        self,
        service,
        user_id,
    ):
        """Return zero when there are no matching notifications."""
        mock_query(
            service.db,
            result=[],
        )

        result = service.mark_all_as_read(user_id)

        assert result == 0
        service.db.commit.assert_called_once_with()


class TestGetUnreadCount:
    """Tests for unread notification counts."""

    def test_returns_unread_count(
        self,
        service,
        user_id,
    ):
        """Return the number of unread notifications."""
        query = mock_query(
            service.db,
            count=7,
        )

        result = service.get_unread_count(user_id)

        assert result == 7
        query.count.assert_called_once_with()

    def test_returns_zero_when_no_unread_notifications(
        self,
        service,
        user_id,
    ):
        """Return zero when there are no unread notifications."""
        mock_query(
            service.db,
            count=0,
        )

        result = service.get_unread_count(user_id)

        assert result == 0


class TestArchiveOldNotifications:
    """Tests for archiving old notifications."""

    def test_archives_old_notifications(
        self,
        service,
        user_id,
    ):
        """Archive all matching old notifications."""
        first = MagicMock()
        first.is_archived = False

        second = MagicMock()
        second.is_archived = False

        mock_query(
            service.db,
            result=[first, second],
        )

        result = service.archive_old_notifications(
            user_id=user_id,
            older_than_days=30,
        )

        assert result == 2
        assert first.is_archived is True
        assert second.is_archived is True

        service.db.commit.assert_called_once_with()

    def test_returns_zero_when_no_old_notifications(
        self,
        service,
        user_id,
    ):
        """Return zero when nothing needs archiving."""
        mock_query(
            service.db,
            result=[],
        )

        result = service.archive_old_notifications(
            user_id=user_id,
            older_than_days=30,
        )

        assert result == 0
        service.db.commit.assert_called_once_with()


class TestGetAllNotifications:
    """Tests for global notification retrieval."""

    def test_returns_all_notifications(
        self,
        service,
        notification,
    ):
        """Return non-archived notifications within history."""
        query = mock_query(
            service.db,
            result=[notification],
            count=1,
        )

        with patch(
            "app.services.macro_notification_service.settings.HISTORY_NOTIFICATION_DAYS",
            30,
        ):
            total, notifications = service.get_all_notifications()

        assert total == 1
        assert notifications == [notification]

        query.count.assert_called_once_with()
        query.order_by.assert_called_once()
        query.offset.assert_called_once_with(0)
        query.limit.assert_called_once_with(50)
        query.all.assert_called_once_with()

    def test_returns_empty_global_notifications(
        self,
        service,
    ):
        """Return empty results when no notifications exist."""
        mock_query(
            service.db,
            result=[],
            count=0,
        )

        with patch(
            "app.services.macro_notification_service.settings.HISTORY_NOTIFICATION_DAYS",
            30,
        ):
            total, notifications = service.get_all_notifications()

        assert total == 0
        assert notifications == []

    def test_filters_unread_global_notifications(
        self,
        service,
        notification,
    ):
        """Apply unread filtering to global notifications."""
        query = mock_query(
            service.db,
            result=[notification],
            count=1,
        )

        with patch(
            "app.services.macro_notification_service.settings.HISTORY_NOTIFICATION_DAYS",
            30,
        ):
            service.get_all_notifications(
                unread_only=True,
            )

        assert query.filter.call_count == 2

    def test_applies_global_pagination(
        self,
        service,
        notification,
    ):
        """Apply limit and offset to global notifications."""
        query = mock_query(
            service.db,
            result=[notification],
            count=15,
        )

        with patch(
            "app.services.macro_notification_service.settings.HISTORY_NOTIFICATION_DAYS",
            30,
        ):
            total, notifications = service.get_all_notifications(
                limit=5,
                offset=10,
            )

        assert total == 15
        assert notifications == [notification]

        query.offset.assert_called_once_with(10)
        query.limit.assert_called_once_with(5)


class TestMarkAllNotificationsAsRead:
    """Tests for globally marking notifications as read."""

    def test_marks_all_notifications_as_read(
        self,
        service,
    ):
        """Mark all matching global notifications as read."""
        first = MagicMock()
        first.read = False

        second = MagicMock()
        second.read = False

        mock_query(
            service.db,
            result=[first, second],
        )

        with patch(
            "app.services.macro_notification_service.settings.HISTORY_NOTIFICATION_DAYS",
            30,
        ):
            result = service.mark_all_notifications_as_read()

        assert result == 2

        assert first.read is True
        assert second.read is True

        assert isinstance(first.read_at, datetime)
        assert isinstance(second.read_at, datetime)

        service.db.commit.assert_called_once_with()

        assert first.read_at == second.read_at

    def test_returns_zero_when_no_global_notifications(
        self,
        service,
    ):
        """Return zero when no notifications need updating."""
        mock_query(
            service.db,
            result=[],
        )

        with patch(
            "app.services.macro_notification_service.settings.HISTORY_NOTIFICATION_DAYS",
            30,
        ):
            result = service.mark_all_notifications_as_read()

        assert result == 0
        service.db.commit.assert_called_once_with()