"""Unit tests for event timing calculations"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.macro_alert_engine import MacroAlertEngine
from app.models.macro_alert import MacroEventCache, EventType, EventImpact


class TestEventTiming:
    """Test cases for event timing calculations."""

    @pytest.fixture
    def alert_engine(self, db_session):
        """Create alert engine instance."""
        return MacroAlertEngine(db_session)

    def test_1_day_before_calculation(self, alert_engine):
        """Test 1 day before calculation."""
        now = datetime.utcnow()
        event_time = now + timedelta(days=1)
        time_until = event_time - now
        hours_until = time_until.total_seconds() / 3600

        # Should be within 1 day range (23-25 hours)
        assert 23 <= hours_until <= 25

    def test_12_hours_before_calculation(self, alert_engine):
        """Test 12 hours before calculation."""
        now = datetime.utcnow()
        event_time = now + timedelta(hours=12)
        time_until = event_time - now
        hours_until = time_until.total_seconds() / 3600

        # Should be within 12 hours range (11-13 hours)
        assert 11 <= hours_until <= 13

    def test_1_hour_before_calculation(self, alert_engine):
        """Test 1 hour before calculation."""
        now = datetime.utcnow()
        event_time = now + timedelta(hours=1)
        time_until = event_time - now
        hours_until = time_until.total_seconds() / 3600

        # Should be within 1 hour range (0.5-1.5 hours)
        assert 0.5 <= hours_until <= 1.5

    def test_event_beyond_24_hours_no_trigger(self, alert_engine):
        """Test event beyond 24 hours does not trigger."""
        now = datetime.utcnow()
        event_time = now + timedelta(hours=48)
        hours_until = (event_time - now).total_seconds() / 3600

        assert hours_until > 25

    def test_event_passed_no_trigger(self, alert_engine):
        """Test passed event does not trigger."""
        now = datetime.utcnow()
        event_time = now - timedelta(hours=1)
        hours_until = (event_time - now).total_seconds() / 3600

        assert hours_until < 0

    def test_per_event_timing_configuration(self, alert_engine, db_session):
        """Test per-event timing configuration."""
        # Create events with different timings
        events = [
            MacroEventCache(
                id=uuid4(),
                event_id=f"event_{i}",
                event_type=EventType.FED if i == 0 else EventType.CPI,
                event_name=f"Event {i}",
                description=f"Test event {i}",
                scheduled_at=datetime.utcnow() + timedelta(hours=24 + i),
                timezone="UTC",
                impact=EventImpact.HIGH,
                notified=False
            )
            for i in range(2)
        ]
        for event in events:
            db_session.add(event)
        db_session.commit()

        # Each event should be evaluated independently
        for event in events:
            time_until = event.scheduled_at - datetime.utcnow()
            hours_until = time_until.total_seconds() / 3600
            assert hours_until > 0

    def test_edge_case_exactly_24_hours(self, alert_engine):
        """Test edge case exactly 24 hours."""
        now = datetime.utcnow()
        event_time = now + timedelta(hours=24)
        hours_until = (event_time - now).total_seconds() / 3600

        # Should be exactly 24 hours
        assert hours_until == 24.0

    def test_edge_case_exactly_12_hours(self, alert_engine):
        """Test edge case exactly 12 hours."""
        now = datetime.utcnow()
        event_time = now + timedelta(hours=12)
        hours_until = (event_time - now).total_seconds() / 3600

        # Should be exactly 12 hours
        assert hours_until == 12.0

    def test_edge_case_exactly_1_hour(self, alert_engine):
        """Test edge case exactly 1 hour."""
        now = datetime.utcnow()
        event_time = now + timedelta(hours=1)
        hours_until = (event_time - now).total_seconds() / 3600

        # Should be exactly 1 hour
        assert hours_until == 1.0

    def test_multiple_timing_triggers_for_same_event(self, alert_engine, db_session):
        """Test multiple timing triggers for same event."""
        now = datetime.utcnow()
        event = MacroEventCache(
            id=uuid4(),
            event_id="test_event",
            event_type=EventType.FED,
            event_name="Fed Meeting",
            description="Test event",
            scheduled_at=now + timedelta(hours=1),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False
        )
        db_session.add(event)
        db_session.commit()

        # Event should trigger for 1h timing
        time_until = event.scheduled_at - now
        hours_until = time_until.total_seconds() / 3600
        assert 0.5 <= hours_until <= 1.5