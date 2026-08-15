"""Unit tests for alert engine"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.alert_engine import AlertEngine
from app.models.alert import PriceAlert, AlertStatus, AlertType


class TestAlertEngine:
    """Test cases for AlertEngine."""

    @pytest.fixture
    def alert_engine(self, db_session: Session):
        """Create alert engine instance."""
        return AlertEngine(db_session)

    @pytest.fixture
    def sample_price_data(self):
        """Sample price data for testing."""
        return {
            "symbol": "BTC/USD",
            "price": 85000.00,
            "previous_price": 84000.00,
            "timestamp": "2026-08-15T10:00:00Z"
        }

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
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    # ============================================
    # TESTS FOR 'REACHES' ALERT TYPE
    # ============================================

    def test_reaches_alert_triggers_when_price_equals_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'reaches' alert triggers when price equals threshold."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1
        assert triggered[0].id == sample_alert.id
        assert triggered[0].status == AlertStatus.TRIGGERED

    def test_reaches_alert_does_not_trigger_when_price_not_equal_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'reaches' alert does not trigger when price != threshold."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 84000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 0

    def test_reaches_alert_with_tolerance(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'reaches' alert with small tolerance."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 84999.99  # Within 0.01 tolerance

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1

    # ============================================
    # TESTS FOR 'CROSSES_ABOVE' ALERT TYPE
    # ============================================

    def test_crosses_above_alert_triggers_when_price_crosses_above_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'crosses_above' alert triggers when price crosses above threshold."""
        sample_alert.alert_type = AlertType.CROSSES_ABOVE
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 86000.00
        price_data["previous_price"] = 84000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1
        assert triggered[0].id == sample_alert.id

    def test_crosses_above_alert_does_not_trigger_when_price_below_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'crosses_above' alert does not trigger when price below threshold."""
        sample_alert.alert_type = AlertType.CROSSES_ABOVE
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 84000.00
        price_data["previous_price"] = 83000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 0

    def test_crosses_above_alert_does_not_trigger_when_price_equals_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'crosses_above' alert does not trigger when price equals threshold."""
        sample_alert.alert_type = AlertType.CROSSES_ABOVE
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00
        price_data["previous_price"] = 84000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 0

    # ============================================
    # TESTS FOR 'CROSSES_BELOW' ALERT TYPE
    # ============================================

    def test_crosses_below_alert_triggers_when_price_crosses_below_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'crosses_below' alert triggers when price crosses below threshold."""
        sample_alert.alert_type = AlertType.CROSSES_BELOW
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 83000.00
        price_data["previous_price"] = 86000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1
        assert triggered[0].id == sample_alert.id

    def test_crosses_below_alert_does_not_trigger_when_price_above_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'crosses_below' alert does not trigger when price above threshold."""
        sample_alert.alert_type = AlertType.CROSSES_BELOW
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 86000.00
        price_data["previous_price"] = 87000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 0

    def test_crosses_below_alert_does_not_trigger_when_price_equals_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test 'crosses_below' alert does not trigger when price equals threshold."""
        sample_alert.alert_type = AlertType.CROSSES_BELOW
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00
        price_data["previous_price"] = 86000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 0

    # ============================================
    # TESTS FOR ONE-TIME ALERTS
    # ============================================

    def test_one_time_alert_disabled_after_trigger(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test one-time alert is disabled after triggering."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        sample_alert.one_time = True
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1
        db_session.refresh(sample_alert)
        assert sample_alert.status == AlertStatus.DISABLED

    def test_one_time_alert_does_not_trigger_again(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test one-time alert does not trigger again after being disabled."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        sample_alert.one_time = True
        db_session.commit()

        # First trigger
        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00
        alert_engine.evaluate_price_alerts(price_data)

        # Second evaluation
        price_data["price"] = 85000.00
        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 0

    # ============================================
    # TESTS FOR RECURRING ALERTS
    # ============================================

    def test_recurring_alert_remains_active_after_trigger(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test recurring alert remains active after triggering."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        sample_alert.one_time = False
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1
        db_session.refresh(sample_alert)
        assert sample_alert.status == AlertStatus.TRIGGERED

    def test_recurring_alert_can_trigger_multiple_times(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test recurring alert can trigger multiple times."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        sample_alert.one_time = False
        db_session.commit()

        # First trigger
        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00
        alert_engine.evaluate_price_alerts(price_data)

        # Reset alert status for testing
        sample_alert.status = AlertStatus.ACTIVE
        db_session.commit()

        # Second trigger
        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1

    # ============================================
    # TESTS FOR EDGE CASES
    # ============================================

    def test_alert_with_zero_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test alert with zero threshold."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 0
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 0

        triggered = alert_engine.evaluate_price_alerts(price_data)

        # Zero threshold should not trigger (validation prevents it)
        assert len(triggered) == 0

    def test_alert_with_negative_threshold(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test alert with negative threshold."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = -1000
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = -1000

        triggered = alert_engine.evaluate_price_alerts(price_data)

        # Negative threshold should not trigger (validation prevents it)
        assert len(triggered) == 0

    def test_alert_with_no_previous_price(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test alert evaluation when previous_price is None."""
        sample_alert.alert_type = AlertType.CROSSES_ABOVE
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 86000.00
        price_data["previous_price"] = None

        triggered = alert_engine.evaluate_price_alerts(price_data)

        # Should not trigger without previous_price
        assert len(triggered) == 0

    # ============================================
    # TESTS FOR MULTIPLE ALERTS
    # ============================================

    def test_multiple_alerts_trigger_simultaneously(
        self, alert_engine, db_session, sample_price_data
    ):
        """Test multiple alerts trigger at the same time."""
        user_id = uuid4()

        # Create multiple alerts
        alerts = []
        thresholds = [85000.00, 86000.00, 87000.00]
        for threshold in thresholds:
            alert = PriceAlert(
                id=uuid4(),
                user_id=user_id,
                threshold_price=threshold,
                alert_type=AlertType.REACHES,
                asset="BTC/USD",
                status=AlertStatus.ACTIVE,
                one_time=True,
                notify_in_app=True,
                notify_email=True
            )
            db_session.add(alert)
            alerts.append(alert)

        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        # Only alert with threshold 85000 should trigger
        assert len(triggered) == 1
        assert triggered[0].threshold_price == 85000.00

    def test_multiple_alert_types_simultaneously(
        self, alert_engine, db_session, sample_price_data
    ):
        """Test multiple alert types trigger at the same time."""
        user_id = uuid4()

        # Create alerts of different types
        alert_reaches = PriceAlert(
            id=uuid4(),
            user_id=user_id,
            threshold_price=85000.00,
            alert_type=AlertType.REACHES,
            asset="BTC/USD",
            status=AlertStatus.ACTIVE,
            one_time=True,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert_reaches)

        alert_crosses_above = PriceAlert(
            id=uuid4(),
            user_id=user_id,
            threshold_price=84000.00,
            alert_type=AlertType.CROSSES_ABOVE,
            asset="BTC/USD",
            status=AlertStatus.ACTIVE,
            one_time=True,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert_crosses_above)

        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00
        price_data["previous_price"] = 83000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        # Both alerts should trigger
        assert len(triggered) == 2

    # ============================================
    # TESTS FOR EVALUATION LOGGING
    # ============================================

    def test_alert_evaluation_logs_history(
        self, alert_engine, db_session, sample_alert, sample_price_data
    ):
        """Test alert evaluation creates history entries."""
        sample_alert.alert_type = AlertType.REACHES
        sample_alert.threshold_price = 85000.00
        db_session.commit()

        price_data = sample_price_data.copy()
        price_data["price"] = 85000.00

        triggered = alert_engine.evaluate_price_alerts(price_data)

        assert len(triggered) == 1

        # Check history was created
        from app.models.alert import AlertHistory
        history = db_session.query(AlertHistory).filter(
            AlertHistory.alert_id == sample_alert.id
        ).first()

        assert history is not None
        assert history.event_type.value == "triggered"
        assert history.triggered_price == 85000.00
        assert history.threshold_price == 85000.00