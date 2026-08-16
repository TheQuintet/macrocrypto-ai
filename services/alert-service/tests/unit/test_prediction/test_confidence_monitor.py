"""Unit tests for confidence level monitoring"""

import pytest
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session

from app.services.confidence_monitor import ConfidenceMonitor
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection
)


class TestConfidenceMonitor:
    """Test cases for ConfidenceMonitor."""

    @pytest.fixture
    def confidence_monitor(self, db_session: Session):
        """Create confidence monitor instance."""
        return ConfidenceMonitor(db_session)

    @pytest.fixture
    def sample_alert(self, db_session: Session):
        """Create a sample prediction alert for testing."""
        alert = PredictionChangeAlert(
            id=uuid4(),
            user_id=uuid4(),
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            monitor_confidence=True,
            confidence_threshold_percent=5.0,
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    # ============================================
    # TESTS FOR CONFIDENCE CHANGE DETECTION
    # ============================================

    def test_confidence_change_detection_returns_trigger(
        self, confidence_monitor, sample_alert
    ):
        """Test confidence change detection returns trigger data."""
        result = confidence_monitor.check_confidence_changes(
            alert=sample_alert,
            previous_confidence=92.0,
            new_confidence=85.0
        )

        assert result is not None
        assert result["triggered"] is True
        assert result["previous_confidence"] == 92.0
        assert result["new_confidence"] == 85.0
        assert result["change_percent"] == pytest.approx(-7.61)
        assert result["direction"] == "down"

    def test_confidence_change_below_threshold_no_trigger(
        self, confidence_monitor, sample_alert
    ):
        """Test confidence change below threshold does not trigger."""
        sample_alert.confidence_threshold_percent = 10.0

        result = confidence_monitor.check_confidence_changes(
            alert=sample_alert,
            previous_confidence=92.0,
            new_confidence=88.0
        )

        assert result is None

    def test_confidence_monitor_disabled_no_trigger(
        self, confidence_monitor, sample_alert
    ):
        """Test confidence monitor disabled does not trigger."""
        sample_alert.monitor_confidence = False

        result = confidence_monitor.check_confidence_changes(
            alert=sample_alert,
            previous_confidence=92.0,
            new_confidence=85.0
        )

        assert result is None

    def test_missing_confidence_values_no_trigger(
        self, confidence_monitor, sample_alert
    ):
        """Test missing confidence values do not trigger."""
        result = confidence_monitor.check_confidence_changes(
            alert=sample_alert,
            previous_confidence=None,
            new_confidence=85.0
        )

        assert result is None

        result = confidence_monitor.check_confidence_changes(
            alert=sample_alert,
            previous_confidence=92.0,
            new_confidence=None
        )

        assert result is None

    # ============================================
    # TESTS FOR CALCULATE PERCENT CHANGE
    # ============================================

    def test_calculate_percent_change_positive(self, confidence_monitor):
        """Test calculating positive percent change."""
        change = confidence_monitor._calculate_percent_change(100, 110)
        assert change == 10.0

    def test_calculate_percent_change_negative(self, confidence_monitor):
        """Test calculating negative percent change."""
        change = confidence_monitor._calculate_percent_change(100, 90)
        assert change == -10.0

    def test_calculate_percent_change_zero_old_value(self, confidence_monitor):
        """Test calculating percent change with zero old value."""
        change = confidence_monitor._calculate_percent_change(0, 100)
        assert change == 0

    # ============================================
    # TESTS FOR GETTING ACTIVE ALERTS
    # ============================================

    def test_get_active_alerts_for_confidence_monitoring(
        self, confidence_monitor, db_session, sample_alert
    ):
        """Test getting active alerts with confidence monitoring enabled."""
        # Create another alert with confidence monitoring disabled
        alert_disabled = PredictionChangeAlert(
            id=uuid4(),
            user_id=sample_alert.user_id,
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            monitor_confidence=False,
            confidence_threshold_percent=5.0,
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert_disabled)
        db_session.commit()

        alerts = confidence_monitor.get_active_alerts_for_confidence_monitoring()

        assert len(alerts) == 1
        assert alerts[0].monitor_confidence is True

    # ============================================
    # TESTS FOR CONFIDENCE HISTORY
    # ============================================

    def test_get_confidence_history(
        self, confidence_monitor, db_session, sample_alert
    ):
        """Test getting confidence history for an alert."""
        # Create history entries
        from app.models.prediction_alert import PredictionChangeHistory
        for i in range(3):
            history = PredictionChangeHistory(
                alert_id=sample_alert.id,
                previous_confidence=90.0 + i,
                new_confidence=85.0 + i,
                confidence_change_percent=-5.0,
                triggered_at=datetime.utcnow()
            )
            db_session.add(history)

        db_session.commit()

        history = confidence_monitor.get_confidence_history(
            alert_id=str(sample_alert.id),
            limit=5
        )

        assert len(history) == 3
        assert "previous_confidence" in history[0]
        assert "new_confidence" in history[0]
        assert "confidence_change_percent" in history[0]