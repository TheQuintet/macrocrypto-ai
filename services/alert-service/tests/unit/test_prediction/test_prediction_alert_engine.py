"""Unit tests for prediction change alert engine"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.prediction_alert_engine import PredictionAlertEngine
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeHistory,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection
)
from app.models.alert import PriceAlert, AlertType, AlertStatus


class TestPredictionAlertEngine:
    """Test cases for PredictionAlertEngine."""

    @pytest.fixture
    def alert_engine(self, db_session: Session):
        """Create alert engine instance."""
        return PredictionAlertEngine(db_session)

    @pytest.fixture
    def sample_price_alert(self, db_session: Session):
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
    def sample_alert(self, db_session: Session, sample_price_alert):
        """Create a sample prediction alert for testing."""
        alert = PredictionChangeAlert(
            id=sample_price_alert.id,  # Reuse PriceAlert ID
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

    @pytest.fixture
    def sample_prediction_data(self):
        """Sample prediction data for testing."""
        return {
            "asset": "BTC/USD",
            "horizon": "24h",
            "prediction": 85000.50,
            "previous_prediction": 82000.00,
            "confidence": 85.5,
            "previous_confidence": 92.0,
            "timestamp": "2026-08-16T10:00:00Z"
        }

    # ============================================
    # TESTS FOR PREDICTION CHANGE DETECTION
    # ============================================

    def test_prediction_change_detection_triggers_alert(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test prediction change detection triggers alert."""
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 1
        assert triggered[0].id == sample_alert.id

    def test_prediction_change_below_threshold_does_not_trigger(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test prediction change below threshold does not trigger."""
        sample_alert.threshold_percent = 5.0
        sample_alert.monitor_confidence = False
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 82500.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 0

    # ============================================
    # TESTS FOR THRESHOLD CHECKING
    # ============================================

    @pytest.mark.parametrize("threshold,should_trigger", [
        (1.0, True),
        (2.0, True),
        (5.0, False),
        (10.0, False),
    ])
    def test_threshold_checking(
        self, alert_engine, db_session, sample_alert,
        sample_prediction_data, threshold, should_trigger
    ):
        """Test different threshold values."""
        sample_alert.monitor_confidence = False
        sample_alert.threshold_percent = threshold
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        if should_trigger:
            assert len(triggered) == 1
        else:
            assert len(triggered) == 0

    # ============================================
    # TESTS FOR CONFIDENCE CHANGE DETECTION
    # ============================================

    def test_confidence_change_triggers_alert(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test confidence change triggers alert."""
        sample_alert.monitor_confidence = True
        sample_alert.confidence_threshold_percent = 5.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["confidence"] = 85.0
        prediction_data["previous_confidence"] = 92.0

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 1
        assert triggered[0].id == sample_alert.id

    def test_confidence_change_disabled_does_not_trigger(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test confidence change does not trigger when disabled."""
        sample_alert.monitor_confidence = False
        sample_alert.confidence_threshold_percent = 5.0
        sample_alert.threshold_percent = 10.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["confidence"] = 85.0
        prediction_data["previous_confidence"] = 92.0
        prediction_data["prediction"] = 82500.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 0

    def test_confidence_change_below_threshold_does_not_trigger(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test confidence change below threshold does not trigger."""
        sample_alert.monitor_confidence = True
        sample_alert.confidence_threshold_percent = 10.0
        sample_alert.threshold_percent = 10.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["confidence"] = 88.0
        prediction_data["previous_confidence"] = 92.0
        prediction_data["prediction"] = 82500.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 0

    # ============================================
    # TESTS FOR DIRECTION FILTERING
    # ============================================

    def test_direction_up_only_triggers_on_upward_change(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test direction 'up' only triggers on upward change."""
        sample_alert.direction = PredictionDirection.UP
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        # Upward change
        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)
        assert len(triggered) == 1

        # Downward change
        prediction_data["prediction"] = 80000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)
        assert len(triggered) == 0

    def test_direction_down_only_triggers_on_downward_change(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test direction 'down' only triggers on downward change."""
        sample_alert.direction = PredictionDirection.DOWN
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        # Downward change
        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 80000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)
        assert len(triggered) == 1

        # Upward change
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)
        assert len(triggered) == 0

    # ============================================
    # TESTS FOR HORIZON FILTERING
    # ============================================

    def test_horizon_24h_triggers_only_24h_alerts(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test horizon filtering for 24h alerts."""
        sample_alert.horizon = PredictionHorizon.HOUR_24
        db_session.commit()

        # Create 7d alert
        alert_7d = PredictionChangeAlert(
            id=uuid4(),
            user_id=sample_alert.user_id,
            threshold_percent=2.0,
            horizon=PredictionHorizon.DAY_7,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert_7d)
        db_session.commit()

        # 24h prediction data
        prediction_data = sample_prediction_data.copy()
        prediction_data["horizon"] = "24h"
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        # Should only trigger the 24h alert
        assert len(triggered) == 1
        assert triggered[0].horizon == PredictionHorizon.HOUR_24

    # ============================================
    # TESTS FOR MULTIPLE ALERTS
    # ============================================

    def test_multiple_alerts_trigger_simultaneously(
        self, alert_engine, db_session, sample_prediction_data
    ):
        """Test multiple alerts trigger at the same time."""
        user_id = uuid4()

        # Create multiple alerts with different thresholds
        alerts = []
        thresholds = [1.0, 2.0, 3.0, 5.0]
        for threshold in thresholds:
            alert = PredictionChangeAlert(
                id=uuid4(),
                user_id=user_id,
                threshold_percent=threshold,
                horizon=PredictionHorizon.HOUR_24,
                direction=PredictionDirection.BOTH,
                asset="BTC/USD",
                monitor_confidence=False,  # Disable to avoid FK violations
                notify_in_app=False,  # Disable to avoid FK violations
                notify_email=False,  # Disable to avoid FK violations
                status=PredictionAlertStatus.ACTIVE,
            )
            db_session.add(alert)
            alerts.append(alert)

        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        # Should trigger alerts with threshold <= 3.6%
        assert len(triggered) == 3

    # ============================================
    # TESTS FOR EDGE CASES
    # ============================================

    def test_no_previous_prediction_does_not_trigger(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test no previous prediction does not trigger."""
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["previous_prediction"] = None

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 0

    def test_zero_change_does_not_trigger(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test zero change does not trigger."""
        sample_alert.monitor_confidence = False
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 82000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 0

    def test_missing_prediction_data_does_not_trigger(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test missing prediction data does not trigger."""
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        prediction_data = {}
        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 0

    # ============================================
    # TESTS FOR ALERT STATUS MANAGEMENT
    # ============================================

    def test_alert_status_changes_to_triggered_after_trigger(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test alert status changes to triggered after triggering."""
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 1
        db_session.refresh(sample_alert)
        assert sample_alert.status == PredictionAlertStatus.TRIGGERED

    def test_inactive_alerts_are_ignored(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test inactive alerts are ignored by the engine."""
        sample_alert.threshold_percent = 2.0
        sample_alert.status = PredictionAlertStatus.DISABLED
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 0

    # ============================================
    # TESTS FOR RECOMMENDATION GENERATION
    # ============================================

    def test_recommendation_generation_for_upward_prediction(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test recommendation generation for upward prediction."""
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 85000.00
        prediction_data["previous_prediction"] = 82000.00
        prediction_data["confidence"] = 90.0
        prediction_data["previous_confidence"] = 85.0

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 1

        # Check history for recommendation
        history = db_session.query(PredictionChangeHistory).filter(
            PredictionChangeHistory.alert_id == sample_alert.id
        ).first()

        assert history is not None
        assert "Strong buy signal" in history.recommendation or "Upward prediction" in history.recommendation

    def test_recommendation_generation_for_downward_prediction(
        self, alert_engine, db_session, sample_alert, sample_prediction_data
    ):
        """Test recommendation generation for downward prediction."""
        sample_alert.threshold_percent = 2.0
        db_session.commit()

        prediction_data = sample_prediction_data.copy()
        prediction_data["prediction"] = 80000.00
        prediction_data["previous_prediction"] = 82000.00

        triggered = alert_engine.evaluate_prediction_alerts(prediction_data)

        assert len(triggered) == 1

        # Check history for recommendation
        history = db_session.query(PredictionChangeHistory).filter(
            PredictionChangeHistory.alert_id == sample_alert.id
        ).first()

        assert history is not None
        assert "Cautious: Prediction down" in history.recommendation or "sell" in history.recommendation.lower()