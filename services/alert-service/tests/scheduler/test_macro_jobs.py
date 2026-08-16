"""Tests for macro scheduled jobs"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.scheduler.macro_jobs import (
    check_macro_events_job,
    cleanup_old_events_job,
    _fetch_economic_calendar_events,
    _update_event_cache
)
from app.models.macro_alert import (
    MacroEventCache,
    MacroEventSubscription,
    MacroEventAlert,
    EventType,
    EventImpact,
    MacroAlertStatus
)


class TestMacroJobs:
    """Test cases for macro scheduled jobs."""

    @pytest.fixture
    def sample_subscription(self, db_session):
        """Create a sample subscription for testing."""
        subscription = MacroEventSubscription(
            id=uuid4(),
            user_id=uuid4(),
            event_type=EventType.FED,
            subscribed=True,
            impact_filter=EventImpact.HIGH
        )
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        return subscription

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

    def test_update_event_cache_new_event(self, db_session):
        """Test updating event cache with new event."""
        event_data = {
            "event_id": "test_001",
            "event_type": "fed",
            "event_name": "Test Event",
            "description": "Test description",
            "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "timezone": "UTC",
            "impact": "high",
            "source": "Test Source",
            "url": "https://test.com"
        }

        _update_event_cache(db_session, event_data)

        event = db_session.query(MacroEventCache).filter(
            MacroEventCache.event_id == "test_001"
        ).first()

        assert event is not None
        assert event.event_name == "Test Event"
        assert event.impact == EventImpact.HIGH

    def test_update_event_cache_existing_event(self, db_session):
        """Test updating event cache with existing event."""
        # Create existing event
        existing = MacroEventCache(
            id=uuid4(),
            event_id="test_001",
            event_type=EventType.FED,
            event_name="Old Name",
            description="Old description",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False
        )
        db_session.add(existing)
        db_session.commit()

        # Update with new data
        event_data = {
            "event_id": "test_001",
            "event_type": "fed",
            "event_name": "New Name",
            "description": "New description",
            "scheduled_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "timezone": "America/New_York",
            "impact": "medium",
            "source": "New Source",
            "url": "https://newtest.com"
        }

        _update_event_cache(db_session, event_data)

        db_session.refresh(existing)
        assert existing.event_name == "New Name"
        assert existing.description == "New description"
        assert existing.timezone == "America/New_York"
        assert existing.impact == EventImpact.MEDIUM

    @patch('app.scheduler.macro_jobs._fetch_economic_calendar_events')
    def test_check_macro_events_job_triggers_alerts(
        self, mock_fetch, db_session, sample_subscription
    ):
        """Test macro events job triggers alerts."""
        # Mock events
        mock_fetch.return_value = [{
            "event_id": "test_001",
            "event_type": "fed",
            "event_name": "Test Event",
            "description": "Test description",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "timezone": "UTC",
            "impact": "high",
            "source": "Test",
            "url": "https://test.com"
        }]

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            with patch('app.rabbitmq.producer.RabbitMQProducer.publish_alert_triggered', return_value=True):
                check_macro_events_job()

        # Check alert was created
        alert = db_session.query(MacroEventAlert).filter(
            MacroEventAlert.user_id == sample_subscription.user_id
        ).first()

        assert alert is not None
        assert alert.event_type == EventType.FED
        assert alert.status == MacroAlertStatus.TRIGGERED

    @patch('app.scheduler.macro_jobs._fetch_economic_calendar_events')
    def test_check_macro_events_job_no_events(
        self, mock_fetch, db_session
    ):
        """Test macro events job with no events."""
        mock_fetch.return_value = []

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            check_macro_events_job()

        # No alerts should be created
        alerts = db_session.query(MacroEventAlert).all()
        assert len(alerts) == 0

    @patch('app.scheduler.macro_jobs._fetch_economic_calendar_events')
    def test_check_macro_events_job_error_handling(
        self, mock_fetch, db_session
    ):
        """Test macro events job handles errors gracefully."""
        mock_fetch.side_effect = Exception("Failed to fetch events")

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            # Should not raise exception
            check_macro_events_job()

        # Job should complete without error

    def test_cleanup_old_events_job(self, db_session):
        """Test cleanup of old events from cache."""
        # Create old events
        for i in range(3):
            event = MacroEventCache(
                id=uuid4(),
                event_id=f"old_event_{i}",
                event_type=EventType.FED,
                event_name=f"Old Event {i}",
                description="Old event",
                scheduled_at=datetime.utcnow() - timedelta(days=10 + i),
                timezone="UTC",
                impact=EventImpact.HIGH,
                notified=True,
                notified_at=datetime.utcnow() - timedelta(days=9 + i)
            )
            db_session.add(event)

        # Create recent event (should be kept)
        recent = MacroEventCache(
            id=uuid4(),
            event_id="recent_event",
            event_type=EventType.FED,
            event_name="Recent Event",
            description="Recent event",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False
        )
        db_session.add(recent)
        db_session.commit()

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            cleanup_old_events_job()

        # Old events should be deleted, recent should remain
        remaining = db_session.query(MacroEventCache).all()
        assert len(remaining) == 1
        assert remaining[0].event_id == "recent_event"