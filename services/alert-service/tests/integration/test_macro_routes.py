"""Tests for macro alert API routes."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.macro_routes import (
    _apply_subscription_preferences,
    subscribe_to_event,
    unsubscribe_from_event,
    get_subscriptions,
    subscribe_to_all_events,
    unsubscribe_from_all_events,
    create_macro_alert,
    get_macro_alerts,
    delete_macro_alert,
    get_all_notifications,
    get_unread_notifications,
    mark_all_notifications_as_read,
    get_macro_notifications,
    mark_macro_notification_read,
    get_upcoming_events,
)
from app.models.macro_alert import (
    EventType,
    EventTiming,
    EventImpact,
    MacroAlertStatus,
)


def enum_value(enum_class):
    """Return a valid enum value without hard-coding project values."""
    return next(iter(enum_class)).value


@pytest.fixture
def db():
    """Create a mocked database session."""
    return MagicMock()


@pytest.fixture
def user_id():
    """Return a test user UUID."""
    return uuid4()


@pytest.fixture
def subscription_data(user_id):
    """Create mocked subscription request data."""
    return SimpleNamespace(
        user_id=user_id,
        event_type="fed",
        subscribed=True,
        impact_filter=enum_value(EventImpact),
        timing=enum_value(EventTiming),
        one_time=False,
        notify_in_app=True,
        notify_email=False,
    )


@pytest.fixture
def alert_data(user_id):
    """Create mocked macro alert request data."""
    return SimpleNamespace(
        user_id=user_id,
        event_id=uuid4(),
        event_type=enum_value(EventType),
        timing=enum_value(EventTiming),
        impact_filter=enum_value(EventImpact),
        name="Test Alert",
        description="Test macro alert",
        notify_in_app=True,
        notify_email=False,
    )


class TestApplySubscriptionPreferences:
    """Test subscription preference application."""

    def test_applies_all_preferences(self, subscription_data):
        """Test all subscription preferences are copied."""
        subscription = MagicMock()

        _apply_subscription_preferences(
            subscription,
            subscription_data,
        )

        assert subscription.subscribed is True
        assert subscription.impact_filter == subscription_data.impact_filter
        assert subscription.timing == EventTiming(
            subscription_data.timing
        )
        assert subscription.one_time is False
        assert subscription.notify_in_app is True
        assert subscription.notify_email is False
        assert isinstance(subscription.updated_at, datetime)


class TestSubscribeToEvent:
    """Test event subscription endpoint."""

    @pytest.mark.asyncio
    async def test_create_new_subscription(
        self,
        db,
        subscription_data,
    ):
        """Test creating a new subscription."""
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = None

        db.query.return_value = query

        subscription = MagicMock()
        subscription.to_dict.return_value = {
            "event_type": "fed",
            "subscribed": True,
        }

        with patch(
            "app.api.macro_routes.MacroEventSubscription",
            return_value=subscription,
        ) as model:
            result = await subscribe_to_event(
                subscription_data,
                db,
            )

        model.assert_called_once()
        db.add.assert_called_once_with(subscription)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(subscription)
        subscription.to_dict.assert_called_once()

        assert result == {
            "event_type": "fed",
            "subscribed": True,
        }

    @pytest.mark.asyncio
    async def test_update_existing_subscription(
        self,
        db,
        subscription_data,
    ):
        """Test updating an existing subscription."""
        existing = MagicMock()
        existing.to_dict.return_value = {
            "event_type": "fed",
            "subscribed": True,
        }

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = existing

        db.query.return_value = query

        result = await subscribe_to_event(
            subscription_data,
            db,
        )

        assert result == existing.to_dict.return_value
        db.add.assert_not_called()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(existing)


class TestUnsubscribeFromEvent:
    """Test event unsubscription endpoint."""

    @pytest.mark.asyncio
    async def test_unsubscribe_success(
        self,
        db,
        user_id,
    ):
        """Test successful subscription deletion."""
        subscription = MagicMock()

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = subscription

        db.query.return_value = query

        result = await unsubscribe_from_event(
            user_id,
            " FED ",
            db,
        )

        db.delete.assert_called_once_with(subscription)
        db.commit.assert_called_once()

        assert result == {
            "status": "unsubscribed",
            "event_type": " FED ",
        }

    @pytest.mark.asyncio
    async def test_unsubscribe_not_found(
        self,
        db,
        user_id,
    ):
        """Test unsubscription when no subscription exists."""
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = None

        db.query.return_value = query

        with pytest.raises(HTTPException) as exc:
            await unsubscribe_from_event(
                user_id,
                "fed",
                db,
            )

        assert exc.value.status_code == 404
        assert "Subscription for fed not found" in exc.value.detail


class TestGetSubscriptions:
    """Test subscription retrieval."""

    @pytest.mark.asyncio
    async def test_get_subscriptions(
        self,
        db,
        user_id,
    ):
        """Test retrieving all subscriptions."""
        subscription_1 = MagicMock()
        subscription_1.to_dict.return_value = {
            "event_type": "fed"
        }

        subscription_2 = MagicMock()
        subscription_2.to_dict.return_value = {
            "event_type": "cpi"
        }

        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = [
            subscription_1,
            subscription_2,
        ]

        db.query.return_value = query

        result = await get_subscriptions(
            user_id,
            db,
        )

        assert result["user_id"] == str(user_id)
        assert result["subscriptions"] == [
            {"event_type": "fed"},
            {"event_type": "cpi"},
        ]


class TestSubscribeToAllEvents:
    """Test subscribe-all endpoint."""

    @pytest.mark.asyncio
    async def test_subscribe_all_with_existing_subscription(
        self,
        db,
        user_id,
    ):
        """Test updating an existing subscription and creating the rest."""
        existing = MagicMock()

        query = MagicMock()
        query.filter.return_value = query
        query.first.side_effect = [
            existing,
            None,
            None,
            None,
            None,
        ]

        db.query.return_value = query

        with patch(
            "app.api.macro_routes.MacroEventSubscription"
        ) as model:
            result = await subscribe_to_all_events(
                user_id,
                db,
            )

        assert result == {
            "status": "subscribed_to_all",
            "event_types": [
                "fed",
                "cpi",
                "gdp",
                "employment",
                "other",
            ],
        }

        assert existing.subscribed is True
        assert isinstance(existing.updated_at, datetime)

        assert model.call_count == 4
        assert db.add.call_count == 4
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_all_with_no_existing_subscriptions(
        self,
        db,
        user_id,
    ):
        """Test creation of all subscriptions when none exist."""
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = None

        db.query.return_value = query

        with patch(
            "app.api.macro_routes.MacroEventSubscription"
        ) as model:
            result = await subscribe_to_all_events(
                user_id,
                db,
            )

        assert result["status"] == "subscribed_to_all"
        assert len(result["event_types"]) == 5
        assert model.call_count == 5
        assert db.add.call_count == 5
        db.commit.assert_called_once()


class TestUnsubscribeFromAllEvents:
    """Test unsubscribe-all endpoint."""

    @pytest.mark.asyncio
    async def test_unsubscribe_all(
        self,
        db,
        user_id,
    ):
        """Test marking all user subscriptions as unsubscribed."""
        query = MagicMock()
        query.filter.return_value = query

        db.query.return_value = query

        result = await unsubscribe_from_all_events(
            user_id,
            db,
        )

        query.update.assert_called_once()
        db.commit.assert_called_once()

        update_values = query.update.call_args.args[0]

        assert update_values["subscribed"] is False
        assert isinstance(update_values["updated_at"], datetime)

        assert result == {
            "status": "unsubscribed_from_all"
        }


class TestCreateMacroAlert:
    """Test macro alert creation."""

    @pytest.mark.asyncio
    async def test_create_alert_success(
        self,
        db,
        alert_data,
    ):
        """Test successful macro alert creation."""
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 0

        db.query.return_value = query

        alert = MagicMock()
        alert.to_dict.return_value = {
            "name": "Test Alert",
            "status": "active",
        }

        with patch(
            "app.api.macro_routes.MacroEventAlert",
            return_value=alert,
        ) as model:
            result = await create_macro_alert(
                alert_data,
                db,
            )

        model.assert_called_once()
        db.add.assert_called_once_with(alert)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(alert)

        assert result == {
            "name": "Test Alert",
            "status": "active",
        }

    @pytest.mark.asyncio
    async def test_create_alert_limit_exceeded(
        self,
        db,
        alert_data,
    ):
        """Test maximum alert limit enforcement."""
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 999

        db.query.return_value = query

        with patch(
            "app.api.macro_routes.settings.MAX_ALERTS_PER_USER",
            5,
        ):
            with pytest.raises(HTTPException) as exc:
                await create_macro_alert(
                    alert_data,
                    db,
                )

        assert exc.value.status_code == 400
        assert "Maximum alerts per user" in exc.value.detail


class TestGetMacroAlerts:
    """Test macro alert retrieval."""

    @pytest.mark.asyncio
    async def test_get_alerts_default_filters(
        self,
        db,
        user_id,
    ):
        """Test retrieving alerts without optional filters."""
        alert_1 = MagicMock()
        alert_1.to_dict.return_value = {"id": "1"}

        alert_2 = MagicMock()
        alert_2.to_dict.return_value = {"id": "2"}

        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 2
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = [
            alert_1,
            alert_2,
        ]

        db.query.return_value = query

        result = await get_macro_alerts(
            user_id,
            status=None,
            event_type=None,
            limit=50,
            offset=0,
            db=db,
        )

        assert result["total"] == 2
        assert result["limit"] == 50
        assert result["offset"] == 0
        assert result["alerts"] == [
            {"id": "1"},
            {"id": "2"},
        ]

    @pytest.mark.asyncio
    async def test_get_alerts_with_valid_status(
        self,
        db,
        user_id,
    ):
        """Test filtering alerts by valid status."""
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 0
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        db.query.return_value = query

        valid_status = enum_value(MacroAlertStatus)

        result = await get_macro_alerts(
            user_id,
            status=valid_status,
            event_type=None,
            limit=50,
            offset=0,
            db=db,
        )

        assert result["total"] == 0
        assert result["alerts"] == []
        assert query.filter.call_count >= 2

  
    @pytest.mark.asyncio
    async def test_get_alerts_with_valid_event_type(
        self,
        db,
        user_id,
    ):
        """Test filtering alerts by valid event type."""
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 0
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        db.query.return_value = query

        valid_event_type = enum_value(EventType)

        result = await get_macro_alerts(
            user_id,
            status=None,
            event_type=valid_event_type,
            limit=50,
            offset=0,
            db=db,
        )

        assert result["total"] == 0
        assert result["alerts"] == []

  
    @pytest.mark.asyncio
    async def test_get_alerts_pagination(
        self,
        db,
        user_id,
    ):
        """Test custom pagination values."""
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 10
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        db.query.return_value = query

        result = await get_macro_alerts(
            user_id,
            status=None,
            event_type=None,
            limit=10,
            offset=20,
            db=db,
        )

        assert result["total"] == 10
        assert result["limit"] == 10
        assert result["offset"] == 20

        query.offset.assert_called_once_with(20)
        query.limit.assert_called_once_with(10)


class TestDeleteMacroAlert:
    """Test macro alert deletion."""

    @pytest.mark.asyncio
    async def test_delete_alert_success(self, db):
        """Test disabling an existing macro alert."""
        alert_id = uuid4()
        alert = MagicMock()

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = alert

        db.query.return_value = query

        result = await delete_macro_alert(
            alert_id,
            db,
        )

        assert result is None
        assert alert.status == MacroAlertStatus.DISABLED
        assert isinstance(alert.updated_at, datetime)

        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_alert_not_found(self, db):
        """Test deleting a nonexistent alert."""
        alert_id = uuid4()

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = None

        db.query.return_value = query

        with pytest.raises(HTTPException) as exc:
            await delete_macro_alert(
                alert_id,
                db,
            )

        assert exc.value.status_code == 404
        assert str(alert_id) in exc.value.detail


class TestGetAllNotifications:
    """Test global macro notification retrieval."""

    @pytest.mark.asyncio
    async def test_get_all_notifications(self, db):
        """Test retrieving all notifications."""
        notification_1 = MagicMock()
        notification_1.to_dict.return_value = {"id": "1"}

        notification_2 = MagicMock()
        notification_2.to_dict.return_value = {"id": "2"}

        service = MagicMock()
        service.get_all_notifications.return_value = (
            2,
            [
                notification_1,
                notification_2,
            ],
        )

        with patch(
            "app.api.macro_routes.MacroNotificationService",
            return_value=service,
        ):
            result = await get_all_notifications(
                limit=20,
                offset=5,
                db=db,
            )

        service.get_all_notifications.assert_called_once_with(
            unread_only=False,
            limit=20,
            offset=5,
        )

        assert result == {
            "total": 2,
            "limit": 20,
            "offset": 5,
            "notifications": [
                {"id": "1"},
                {"id": "2"},
            ],
        }


class TestGetUnreadNotifications:
    """Test unread notification retrieval."""

    @pytest.mark.asyncio
    async def test_get_unread_notifications(self, db):
        """Test retrieving unread notifications."""
        notification = MagicMock()
        notification.to_dict.return_value = {
            "id": "unread-1"
        }

        service = MagicMock()
        service.get_all_notifications.return_value = (
            1,
            [notification],
        )

        with patch(
            "app.api.macro_routes.MacroNotificationService",
            return_value=service,
        ):
            result = await get_unread_notifications(
                limit=10,
                offset=2,
                db=db,
            )

        service.get_all_notifications.assert_called_once_with(
            unread_only=True,
            limit=10,
            offset=2,
        )

        assert result["total"] == 1
        assert result["limit"] == 10
        assert result["offset"] == 2
        assert result["notifications"] == [
            {"id": "unread-1"}
        ]


class TestMarkAllNotificationsAsRead:
    """Test marking all notifications as read."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, db):
        """Test marking all notifications as read."""
        service = MagicMock()
        service.mark_all_notifications_as_read.return_value = 7

        with patch(
            "app.api.macro_routes.MacroNotificationService",
            return_value=service,
        ):
            result = await mark_all_notifications_as_read(db)

        service.mark_all_notifications_as_read.assert_called_once()

        assert result == {
            "status": "success",
            "message": "All notifications marked as read",
            "count": 7,
        }


class TestGetMacroNotifications:
    """Test user-specific macro notifications."""

    @pytest.mark.asyncio
    async def test_get_notifications(
        self,
        db,
        user_id,
    ):
        """Test retrieving user notifications."""
        notification = MagicMock()
        notification.to_dict.return_value = {
            "id": "notification-1"
        }

        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 1
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = [notification]

        db.query.return_value = query

        result = await get_macro_notifications(
            user_id,
            unread_only=False,
            limit=50,
            offset=0,
            db=db,
        )

        assert result["total"] == 1
        assert result["limit"] == 50
        assert result["offset"] == 0
        assert result["notifications"] == [
            {"id": "notification-1"}
        ]

    @pytest.mark.asyncio
    async def test_get_unread_notifications_for_user(
        self,
        db,
        user_id,
    ):
        """Test unread-only user notification filtering."""
        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 0
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        db.query.return_value = query

        result = await get_macro_notifications(
            user_id,
            unread_only=True,
            limit=10,
            offset=3,
            db=db,
        )

        assert result["total"] == 0
        assert result["limit"] == 10
        assert result["offset"] == 3
        assert result["notifications"] == []

        assert query.filter.call_count >= 2


class TestMarkMacroNotificationRead:
    """Test marking individual notifications as read."""

    @pytest.mark.asyncio
    async def test_mark_notification_read(self, db):
        """Test successfully marking a notification as read."""
        notification_id = uuid4()

        notification = MagicMock()
        notification.read = False

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = notification

        db.query.return_value = query

        result = await mark_macro_notification_read(
            notification_id,
            db,
        )

        assert notification.read is True
        assert isinstance(notification.read_at, datetime)

        db.commit.assert_called_once()

        assert result == {
            "status": "success",
            "message": "Notification marked as read",
        }

    @pytest.mark.asyncio
    async def test_mark_notification_read_not_found(self, db):
        """Test marking a nonexistent notification."""
        notification_id = uuid4()

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = None

        db.query.return_value = query

        with pytest.raises(HTTPException) as exc:
            await mark_macro_notification_read(
                notification_id,
                db,
            )

        assert exc.value.status_code == 404
        assert str(notification_id) in exc.value.detail


class TestGetUpcomingEvents:
    """Test upcoming macro event retrieval."""

    @pytest.mark.asyncio
    async def test_get_upcoming_events(self, db):
        """Test retrieving upcoming events."""
        event_1 = MagicMock()
        event_1.to_dict.return_value = {"id": "event-1"}

        event_2 = MagicMock()
        event_2.to_dict.return_value = {"id": "event-2"}

        query = MagicMock()
        query.filter.return_value = query
        query.order_by.return_value = query
        query.limit.return_value = query
        query.all.return_value = [
            event_1,
            event_2,
        ]

        db.query.return_value = query

        result = await get_upcoming_events(
            limit=5,
            db=db,
        )

        query.limit.assert_called_once_with(5)

        assert result == {
            "total": 2,
            "events": [
                {"id": "event-1"},
                {"id": "event-2"},
            ],
        }

    @pytest.mark.asyncio
    async def test_get_upcoming_events_empty(self, db):
        """Test upcoming events when no events exist."""
        query = MagicMock()
        query.filter.return_value = query
        query.order_by.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        db.query.return_value = query

        result = await get_upcoming_events(
            limit=10,
            db=db,
        )

        assert result == {
            "total": 0,
            "events": [],
        }

