"""Tests for macro scheduled jobs."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.alert import (
    AlertStatus,
    AlertType,
    PriceAlert,
)
from app.models.macro_alert import (
    EventImpact,
    EventTiming,
    EventType,
    MacroAlertStatus,
    MacroEventAlert,
    MacroEventCache,
    MacroEventSubscription,
)
from app.scheduler.macro_jobs import (
    _fetch_economic_calendar_events,
    _update_event_cache,
    check_macro_events_job,
    cleanup_old_events_job,
)


class TestMacroJobs:
    """Test cases for macro scheduled jobs."""

    # ============================================================
    # FIXTURES
    # ============================================================

    @pytest.fixture
    def sample_alert(
        self,
        db_session: Session,
    ):
        """Create a sample price alert for testing."""

        alert = PriceAlert(
            id=uuid4(),
            user_id=uuid4(),
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
    def sample_subscription(
        self,
        db_session: Session,
        sample_alert,
    ):
        """Create a sample macro event subscription."""

        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=uuid4(),
            event_type=EventType.FED,
            subscribed=True,
            impact_filter=EventImpact.HIGH,
        )

        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)

        return subscription

    # ============================================================
    # FETCH EVENTS
    # ============================================================

    def test_fetch_economic_calendar_events(self):
        """Test fetching economic calendar events."""

        events = _fetch_economic_calendar_events()

        assert len(events) == 3

        assert events[0]["event_type"] == "fed"
        assert events[1]["event_type"] == "cpi"
        assert events[2]["event_type"] == "gdp"

        assert "event_id" in events[0]
        assert "event_name" in events[0]
        assert "scheduled_at" in events[0]
        assert "impact" in events[0]

    # ============================================================
    # EVENT CACHE
    # ============================================================

    def test_update_event_cache_new_event(
        self,
        db_session,
    ):
        """Test inserting a new event into the cache."""

        event_data = {
            "event_id": "test_001",
            "event_type": "fed",
            "event_name": "Test Event",
            "description": "Test description",
            "scheduled_at": (
                datetime.utcnow()
                + timedelta(days=1)
            ).isoformat(),
            "timezone": "UTC",
            "impact": "high",
            "source": "Test Source",
            "url": "https://test.com",
        }

        _update_event_cache(
            db_session,
            event_data,
        )

        event = (
            db_session.query(MacroEventCache)
            .filter(
                MacroEventCache.event_id == "test_001"
            )
            .first()
        )

        assert event is not None
        assert event.event_name == "Test Event"
        assert event.impact == EventImpact.HIGH

    def test_update_event_cache_existing_event(
        self,
        db_session,
        sample_alert,
    ):
        """Test updating an existing cached event."""

        existing = MacroEventCache(
            id=uuid4(),
            event_id="test_001",
            event_type=EventType.FED,
            event_name="Old Name",
            description="Old description",
            scheduled_at=(
                datetime.utcnow()
                + timedelta(days=1)
            ),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(existing)
        db_session.commit()

        event_data = {
            "event_id": "test_001",
            "event_type": "fed",
            "event_name": "New Name",
            "description": "New description",
            "scheduled_at": (
                datetime.utcnow()
                + timedelta(days=2)
            ).isoformat(),
            "timezone": "America/New_York",
            "impact": "medium",
            "source": "New Source",
            "url": "https://newtest.com",
        }

        _update_event_cache(
            db_session,
            event_data,
        )

        db_session.refresh(existing)

        assert existing.event_name == "New Name"
        assert existing.description == "New description"
        assert existing.timezone == "America/New_York"
        assert existing.impact == EventImpact.MEDIUM

    # ============================================================
    # CHECK MACRO EVENTS JOB
    # ============================================================
    @patch(
        "app.scheduler.macro_jobs._fetch_economic_calendar_events"
    )
    @patch(
        "app.scheduler.macro_jobs.MacroAlertEngine"
    )
    @patch(
        "app.scheduler.macro_jobs.MacroEmailService"
    )
    @patch(
        "app.scheduler.macro_jobs.RabbitMQProducer"
    )
    @patch(
        "app.scheduler.macro_jobs.SessionLocal"
    )
    def test_check_macro_events_job_triggers_alerts(
        self,
        mock_session_local,
        mock_producer_class,
        mock_email_service_class,
        mock_engine_class,
        mock_fetch,
        db_session,
        sample_subscription,
    ):
        """
        Test that check_macro_events_job invokes the macro alert
        engine and processes the expected alert.

        The scheduler creates its own SessionLocal in production, so
        this test redirects it to the pytest-managed session.
        """

        # ---------------------------------------------------------
        # Use the pytest-managed session inside the scheduler.
        # Prevent the scheduler from creating another DB session.
        # ---------------------------------------------------------

        class SessionProxy:
            """Proxy the pytest session without closing it."""

            def __init__(self, session):
                self._session = session

            def __getattr__(self, name):
                return getattr(self._session, name)

            def close(self):
                """Do not close pytest-managed session."""
                pass

        mock_session_local.return_value = SessionProxy(db_session)

        # ---------------------------------------------------------
        # Capture primitive value before session activity.
        # ---------------------------------------------------------

        subscription_user_id = sample_subscription.user_id

        # ---------------------------------------------------------
        # Mock economic calendar event.
        # ---------------------------------------------------------

        mock_fetch.return_value = [
            {
                "event_id": "test_001",
                "event_type": "fed",
                "event_name": "Test Event",
                "description": "Test description",
                "scheduled_at": (
                    datetime.utcnow()
                    + timedelta(hours=24)
                ).isoformat(),
                "timezone": "UTC",
                "impact": "high",
                "source": "Test",
                "url": "https://test.com",
            }
        ]

        # ---------------------------------------------------------
        # Verify fixture data.
        # ---------------------------------------------------------

        subscription = (
            db_session.query(MacroEventSubscription)
            .filter(
                MacroEventSubscription.user_id
                == subscription_user_id
            )
            .first()
        )

        assert subscription is not None
        assert subscription.event_type == EventType.FED
        assert subscription.subscribed is True
        assert subscription.impact_filter == EventImpact.HIGH

        # ---------------------------------------------------------
        # Create the cached event that the triggered alert refers to.
        #
        # This is important because MacroEventAlert.event_id is a
        # required foreign key.
        # ---------------------------------------------------------

        event = MacroEventCache(
            id=uuid4(),
            event_id="test_001",
            event_type=EventType.FED,
            event_name="Test Event",
            description="Test description",
            scheduled_at=(
                datetime.utcnow()
                + timedelta(hours=24)
            ),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        # ---------------------------------------------------------
        # Create the alert represented by the mocked engine.
        # ---------------------------------------------------------

        expected_alert = MacroEventAlert(
            id=uuid4(),
            user_id=subscription_user_id,
            event_id=event.id,
            event_type=EventType.FED,
            timing="1d",
            status=MacroAlertStatus.TRIGGERED,
        )

        db_session.add(expected_alert)
        db_session.commit()
        db_session.refresh(expected_alert)

        # Make sure SQLAlchemy has the event relationship available.
        expected_alert.event = event

        # ---------------------------------------------------------
        # Configure mocked MacroAlertEngine.
        # ---------------------------------------------------------

        mock_engine = MagicMock()

        mock_engine.check_upcoming_events.return_value = [
            expected_alert
        ]

        mock_engine_class.return_value = mock_engine

        # ---------------------------------------------------------
        # Configure mocked RabbitMQ producer.
        # ---------------------------------------------------------

        mock_producer = MagicMock()

        mock_producer.connect.return_value = True
        mock_producer.close.return_value = None

        mock_producer_class.return_value = mock_producer

        # ---------------------------------------------------------
        # Configure mocked email service.
        #
        # This prevents the scheduler test from entering any real
        # email/queue implementation.
        # ---------------------------------------------------------

        mock_email_service = MagicMock()

        mock_email_service_class.return_value = mock_email_service

        # ---------------------------------------------------------
        # Run the scheduler job.
        # ---------------------------------------------------------

        check_macro_events_job()

        # ---------------------------------------------------------
        # Verify SessionLocal was replaced with the test session.
        # ---------------------------------------------------------

        mock_session_local.assert_called_once()

        # ---------------------------------------------------------
        # Verify producer lifecycle.
        # ---------------------------------------------------------

        mock_producer_class.assert_called_once()
        mock_producer.connect.assert_called_once()
        mock_producer.close.assert_called_once()

        # ---------------------------------------------------------
        # Verify engine instantiation.
        # ---------------------------------------------------------

        mock_engine_class.assert_called_once_with(
            mock_session_local.return_value,
            mock_producer,
        )

        # ---------------------------------------------------------
        # Verify engine execution.
        # ---------------------------------------------------------

        mock_engine.check_upcoming_events.assert_called_once()

        # ---------------------------------------------------------
        # Verify email service was created.
        # ---------------------------------------------------------

        mock_email_service_class.assert_called_once_with(
            mock_session_local.return_value
        )

        # ---------------------------------------------------------
        # Verify the alert email was queued.
        # ---------------------------------------------------------

        mock_email_service.queue_macro_alert_email.assert_called_once()

        email_call = (
            mock_email_service
            .queue_macro_alert_email
            .call_args
        )

        assert email_call.kwargs["alert"] == expected_alert
        assert email_call.kwargs["event"] == event
        assert email_call.kwargs["timing"] == expected_alert.timing
        assert (
            email_call.kwargs["user_email"]
            == f"user_{subscription_user_id}@example.com"
        )

        # ---------------------------------------------------------
        # Verify alert exists in the test database.
        # ---------------------------------------------------------

        alert = (
            db_session.query(MacroEventAlert)
            .filter(
                MacroEventAlert.user_id
                == subscription_user_id
            )
            .first()
        )

        assert alert is not None
        assert alert.event_type == EventType.FED

        # timing is an EventTiming enum.
        assert alert.timing.value == "1d"

        assert (
            alert.status
            == MacroAlertStatus.TRIGGERED
        )
    # ============================================================
    # NO EVENTS
    # ============================================================

    @patch(
        "app.scheduler.macro_jobs._fetch_economic_calendar_events"
    )
    def test_check_macro_events_job_no_events(
        self,
        mock_fetch,
        db_session,
    ):
        """Test macro events job when no events are returned."""

        mock_fetch.return_value = []

        with patch(
            "app.scheduler.macro_jobs.RabbitMQProducer"
        ) as mock_producer_class:

            mock_producer = MagicMock()
            mock_producer_class.return_value = (
                mock_producer
            )

            check_macro_events_job()

        alerts = (
            db_session.query(MacroEventAlert)
            .all()
        )

        assert len(alerts) == 0

        mock_producer.connect.assert_called_once()
        mock_producer.close.assert_called_once()

    # ============================================================
    # ERROR HANDLING
    # ============================================================

    @patch(
        "app.scheduler.macro_jobs._fetch_economic_calendar_events"
    )
    def test_check_macro_events_job_error_handling(
        self,
        mock_fetch,
        db_session,
    ):
        """Test scheduler handles event-fetch errors gracefully."""

        mock_fetch.side_effect = Exception(
            "Failed to fetch events"
        )

        with patch(
            "app.scheduler.macro_jobs.RabbitMQProducer"
        ) as mock_producer_class:

            mock_producer = MagicMock()
            mock_producer_class.return_value = (
                mock_producer
            )

            # The scheduler must swallow and log the exception.
            check_macro_events_job()

        mock_producer.connect.assert_called_once()
        mock_producer.close.assert_called_once()

    # ============================================================
    # CLEANUP
    # ============================================================

    @patch("app.scheduler.macro_jobs.SessionLocal")
    def test_cleanup_old_events_job(
        self,
        mock_session_local,
        db_session,
    ):
        """Test cleanup of events older than seven days."""

        # ---------------------------------------------------------
        # Use the pytest-managed session inside the scheduler.
        #
        # The production job creates its own SessionLocal session,
        # so proxy it to the test session.
        # ---------------------------------------------------------

        class SessionProxy:
            """Proxy the pytest session without closing it."""

            def __init__(self, session):
                self._session = session

            def __getattr__(self, name):
                return getattr(self._session, name)

            def close(self):
                """Do not close pytest-managed session."""
                pass

        mock_session_local.return_value = SessionProxy(
            db_session
        )

        # ---------------------------------------------------------
        # Isolate this test from any MacroEventCache records
        # created by fixtures or other setup.
        # ---------------------------------------------------------

        db_session.query(MacroEventCache).delete(
            synchronize_session=False
        )
        db_session.commit()

        # ---------------------------------------------------------
        # Create old events.
        # ---------------------------------------------------------

        for i in range(3):
            event = MacroEventCache(
                id=uuid4(),
                event_id=f"old_event_{i}",
                event_type=EventType.FED,
                event_name=f"Old Event {i}",
                description="Old event",
                scheduled_at=(
                    datetime.utcnow()
                    - timedelta(days=10 + i)
                ),
                timezone="UTC",
                impact=EventImpact.HIGH,
                notified=True,
                notified_at=(
                    datetime.utcnow()
                    - timedelta(days=9 + i)
                ),
            )

            db_session.add(event)

        # ---------------------------------------------------------
        # Create recent event.
        # ---------------------------------------------------------

        recent = MacroEventCache(
            id=uuid4(),
            event_id="recent_event",
            event_type=EventType.FED,
            event_name="Recent Event",
            description="Recent event",
            scheduled_at=(
                datetime.utcnow()
                + timedelta(days=1)
            ),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(recent)
        db_session.commit()

        # ---------------------------------------------------------
        # Run cleanup.
        # ---------------------------------------------------------

        cleanup_old_events_job()

        # ---------------------------------------------------------
        # Verify only recent event remains.
        # ---------------------------------------------------------

        remaining = (
            db_session.query(MacroEventCache)
            .all()
        )

        assert len(remaining) == 1
        assert remaining[0].event_id == "recent_event"