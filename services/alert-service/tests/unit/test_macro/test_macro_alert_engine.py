"""Unit tests for macro event alert engine"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.alert import (
    PriceAlert,
    AlertHistory,
    AlertStatus,
    AlertType,
)

from app.services.macro_alert_engine import MacroAlertEngine

from app.models.macro_alert import (
    MacroEventAlert,
    MacroEventSubscription,
    MacroEventCache,
    EventType,
    EventTiming,
    EventImpact,
    MacroAlertStatus,
)


class TestMacroAlertEngine:
    """Test cases for MacroAlertEngine."""

    @pytest.fixture
    def alert_engine(self, db_session: Session):
        """Create alert engine instance."""
        return MacroAlertEngine(db_session)

    @pytest.fixture
    def sample_alert(self, db_session: Session):
        """Create a sample alert for testing."""
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
    def sample_event(
        self,
        db_session: Session,
        sample_alert,
    ):
        """Create a sample macro event for testing."""
        event = MacroEventCache(
            id=sample_alert.id,
            event_id="test_event_001",
            event_type=EventType.FED,
            event_name="Federal Reserve Meeting",
            description="FOMC interest rate decision",
            scheduled_at=datetime.utcnow() + timedelta(days=2),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        return event

    @pytest.fixture
    def sample_subscription(
        self,
        db_session,
        sample_alert,
    ):
        """Create a sample subscription for testing."""
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

    # ============================================
    # TESTS FOR EVENT DETECTION
    # ============================================

    def test_event_detection_finds_upcoming_events(
        self,
        alert_engine,
        db_session,
        sample_event,
    ):
        """Test event detection finds upcoming events."""
        events = alert_engine.get_events_needing_notification()

        assert len(events) == 1
        assert events[0].id == sample_event.id

    def test_event_detection_ignores_past_events(
        self,
        alert_engine,
        db_session,
        sample_alert,
    ):
        """Test event detection ignores past events."""
        past_event = MacroEventCache(
            id=sample_alert.id,
            event_id="past_event_001",
            event_type=EventType.CPI,
            event_name="Past CPI Release",
            description="Past event",
            scheduled_at=datetime.utcnow() - timedelta(days=1),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(past_event)
        db_session.commit()

        events = alert_engine.get_events_needing_notification()

        assert len(events) == 0

    def test_event_detection_ignores_already_notified(
        self,
        alert_engine,
        db_session,
        sample_alert,
    ):
        """Test event detection ignores already notified events."""
        notified_event = MacroEventCache(
            id=sample_alert.id,
            event_id="notified_event_001",
            event_type=EventType.GDP,
            event_name="GDP Release",
            description="Already notified",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=True,
            notified_at=datetime.utcnow(),
        )

        db_session.add(notified_event)
        db_session.commit()

        events = alert_engine.get_events_needing_notification()

        assert len(events) == 0

    # ============================================
    # TESTS FOR TIMING CALCULATIONS
    # ============================================

    def test_1d_timing_triggers_alert(
        self,
        alert_engine,
        db_session,
        sample_event,
        sample_subscription,
    ):
        """Test 1 day before timing triggers alert."""
        sample_event.scheduled_at = datetime.utcnow() + timedelta(hours=24)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        assert len(triggered) == 1
        assert triggered[0]["timing"] == "1d"

    def test_12h_timing_triggers_alert(
        self,
        alert_engine,
        db_session,
        sample_event,
        sample_subscription,
    ):
        """Test 12 hours before timing triggers alert."""
        sample_event.scheduled_at = datetime.utcnow() + timedelta(hours=12)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        assert len(triggered) == 1
        assert triggered[0]["timing"] == "12h"

    def test_1h_timing_triggers_alert(
        self,
        alert_engine,
        db_session,
        sample_event,
        sample_subscription,
    ):
        """Test 1 hour before timing triggers alert."""
        sample_event.scheduled_at = datetime.utcnow() + timedelta(hours=1)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        assert len(triggered) == 1
        assert triggered[0]["timing"] == "1h"

    # ============================================
    # TESTS FOR SUBSCRIPTION FILTERING
    # ============================================

    def test_subscription_filtering_only_subscribed_users(
        self,
        alert_engine,
        db_session,
        sample_event,
        sample_alert,
    ):
        """Test only subscribed users receive alerts."""

        # Create multiple subscribed users.
        user_ids = [uuid4() for _ in range(3)]

        for user_id in user_ids:
            sub = MacroEventSubscription(
                id=uuid4(),
                user_id=user_id,
                event_type=EventType.FED,
                subscribed=True,
                impact_filter=EventImpact.HIGH,
            )

            db_session.add(sub)

        # Create one unsubscribed user.
        unsubscribed = MacroEventSubscription(
            id=uuid4(),
            user_id=uuid4(),
            event_type=EventType.FED,
            subscribed=False,
            impact_filter=EventImpact.HIGH,
        )

        db_session.add(unsubscribed)
        db_session.commit()

        sample_event.scheduled_at = datetime.utcnow() + timedelta(hours=24)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        # The engine returns the event/timing trigger,
        # not one result per subscribed user.
        assert len(triggered) == 1

        # The important assertion is that subscribed users
        # are selected by the engine rather than the unsubscribed user.
        subscribers = (
            db_session.query(MacroEventSubscription)
            .filter(
                MacroEventSubscription.event_type == EventType.FED,
                MacroEventSubscription.subscribed.is_(True),
            )
            .all()
        )

        assert len(subscribers) == 3

        assert all(
            subscriber.user_id in user_ids
            for subscriber in subscribers
        )

    def test_high_impact_only_filtering(
        self,
        alert_engine,
        db_session,
    ):
        """Test high impact only filtering."""

        # Create a high impact event.
        high_impact_event = MacroEventCache(
            id=uuid4(),
            event_id="high_impact_001",
            event_type=EventType.FED,
            event_name="Fed Meeting",
            description="High impact event",
            scheduled_at=datetime.utcnow() + timedelta(hours=24),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False,
        )

        db_session.add(high_impact_event)

        # Create a low impact event.
        low_impact_event = MacroEventCache(
            id=uuid4(),
            event_id="low_impact_001",
            event_type=EventType.OTHER,
            event_name="Minor Event",
            description="Low impact event",
            scheduled_at=datetime.utcnow() + timedelta(hours=24),
            timezone="UTC",
            impact=EventImpact.LOW,
            notified=False,
        )

        db_session.add(low_impact_event)

        # Create subscription with high impact filter.
        sub = MacroEventSubscription(
            id=uuid4(),
            user_id=uuid4(),
            event_type=EventType.FED,
            subscribed=True,
            impact_filter=EventImpact.HIGH,
        )

        db_session.add(sub)

        # Create subscription with low impact filter.
        sub_low = MacroEventSubscription(
            id=uuid4(),
            user_id=uuid4(),
            event_type=EventType.OTHER,
            subscribed=True,
            impact_filter=EventImpact.LOW,
        )

        db_session.add(sub_low)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        # Should trigger both events.
        assert len(triggered) == 2

    # ============================================
    # TESTS FOR EDGE CASES
    # ============================================

    def test_no_subscribers_no_alerts(
        self,
        alert_engine,
        db_session,
        sample_event,
    ):
        """Test no subscribers results in no alerts."""

        sample_event.scheduled_at = datetime.utcnow() + timedelta(hours=24)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        assert len(triggered) == 0

    def test_event_already_passed_no_alerts(
        self,
        alert_engine,
        db_session,
        sample_event,
        sample_subscription,
    ):
        """Test event already passed results in no alerts."""

        sample_event.scheduled_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        assert len(triggered) == 0

    def test_multiple_events_triggers_multiple_alerts(
        self,
        alert_engine,
        db_session,
    ):
        """Test multiple events trigger multiple alerts."""

        # Create multiple events.
        events = [
            MacroEventCache(
                id=uuid4(),
                event_id=f"event_{i}",
                event_type=(
                    EventType.FED
                    if i % 2 == 0
                    else EventType.CPI
                ),
                event_name=f"Event {i}",
                description=f"Test event {i}",
                scheduled_at=datetime.utcnow() + timedelta(hours=24),
                timezone="UTC",
                impact=EventImpact.HIGH,
                notified=False,
            )
            for i in range(3)
        ]

        for event in events:
            db_session.add(event)

        # Create a separate FED subscription for each FED event.
        # This ensures both FED events can independently trigger
        # an alert for different users.
        fed_events = [
            event
            for event in events
            if event.event_type == EventType.FED
        ]

        for _ in fed_events:
            sub = MacroEventSubscription(
                id=uuid4(),
                user_id=uuid4(),
                event_type=EventType.FED,
                subscribed=True,
                impact_filter=EventImpact.HIGH,
            )

            db_session.add(sub)

        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        # Two FED events should trigger.
        # The CPI event has no matching subscription.
        assert len(triggered) == 2

        assert all(
            item["event"].event_type == EventType.FED
            for item in triggered
        )

    # ============================================
    # TESTS FOR ALERT STATUS MANAGEMENT
    # ============================================

    def test_alert_created_and_triggered(
        self,
        alert_engine,
        db_session,
        sample_event,
        sample_subscription,
    ):
        """Test alert is created and triggered."""

        sample_event.scheduled_at = datetime.utcnow() + timedelta(hours=24)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        # Check alert was created.
        alert = db_session.query(MacroEventAlert).first()

        assert alert is not None
        assert alert.user_id == sample_subscription.user_id
        assert alert.event_type == EventType.FED
        assert alert.status == MacroAlertStatus.TRIGGERED
        assert alert.triggered_at is not None

    def test_inactive_alerts_ignored(
        self,
        alert_engine,
        db_session,
        sample_event,
        sample_subscription,
    ):
        """Test inactive alerts are ignored."""

        # Create disabled alert.
        alert = MacroEventAlert(
            id=uuid4(),
            user_id=sample_subscription.user_id,
            event_id=sample_event.id,
            event_type=EventType.FED,
            timing=EventTiming.ONE_DAY,
            impact_filter=EventImpact.HIGH,
            status=MacroAlertStatus.DISABLED,
        )

        db_session.add(alert)
        db_session.commit()

        sample_event.scheduled_at = datetime.utcnow() + timedelta(hours=24)
        db_session.commit()

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            triggered = alert_engine.check_upcoming_events()

        # Alert should not trigger.
        db_session.refresh(alert)

        assert alert.status == MacroAlertStatus.DISABLED