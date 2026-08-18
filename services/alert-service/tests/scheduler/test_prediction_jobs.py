"""Tests for prediction scheduled jobs"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.scheduler.prediction_jobs import (
    check_prediction_changes_job,
    cleanup_prediction_history_job,
    _fetch_current_predictions
)
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeHistory,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection
)
from app.models.alert import PriceAlert, AlertType, AlertStatus


class TestPredictionJobs:
    """Test cases for prediction scheduled jobs."""

    @pytest.fixture
    def sample_price_alert(self, db_session):
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
    def sample_alert(self, db_session, sample_price_alert):
        """Create a sample prediction alert for testing."""
        alert = PredictionChangeAlert(
            id=sample_price_alert.id,
            user_id=uuid4(),
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    def test_fetch_current_predictions(self):
        """Test fetching current predictions."""
        predictions = _fetch_current_predictions()

        assert len(predictions) == 2
        assert predictions[0]["horizon"] == "24h"
        assert predictions[1]["horizon"] == "7d"
        assert "prediction" in predictions[0]
        assert "previous_prediction" in predictions[0]
        assert "confidence" in predictions[0]
        assert "previous_confidence" in predictions[0]

    @patch('app.scheduler.prediction_jobs._fetch_current_predictions')
    def test_check_prediction_changes_job_triggers_alerts(
        self, mock_fetch, db_session, sample_alert
    ):
        """Test prediction changes job triggers alerts."""
        # Mock predictions
        mock_fetch.return_value = [{
            "asset": "BTC/USD",
            "horizon": "24h",
            "prediction": 85000.00,
            "previous_prediction": 82000.00,
            "confidence": 85.0,
            "previous_confidence": 90.0,
            "timestamp": datetime.utcnow().isoformat()
        }]

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            with patch('app.rabbitmq.producer.RabbitMQProducer.publish_alert_triggered', return_value=True):
                check_prediction_changes_job()

        # Check alert was triggered
        db_session.refresh(sample_alert)
        assert sample_alert.status == PredictionAlertStatus.TRIGGERED

        # Check history was created
        history = db_session.query(PredictionChangeHistory).filter(
            PredictionChangeHistory.alert_id == sample_alert.id
        ).first()

        assert history is not None
        assert history.previous_prediction == 82000.00
        assert history.new_prediction == 85000.00
        assert history.change_percent is not None

    @patch('app.scheduler.prediction_jobs._fetch_current_predictions')
    def test_check_prediction_changes_job_no_triggers(
        self, mock_fetch, db_session, sample_alert
    ):
        """Test prediction changes job when no alerts should trigger."""
        # Mock predictions with small change
        mock_fetch.return_value = [{
            "asset": "BTC/USD",
            "horizon": "24h",
            "prediction": 82200.00,
            "previous_prediction": 82000.00,
            "confidence": 90.0,
            "previous_confidence": 92.0,
            "timestamp": datetime.utcnow().isoformat()
        }]

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            with patch('app.rabbitmq.producer.RabbitMQProducer.publish_alert_triggered', return_value=True):
                check_prediction_changes_job()

        # Alert should not trigger
        db_session.refresh(sample_alert)
        assert sample_alert.status == PredictionAlertStatus.ACTIVE

    @patch('app.scheduler.prediction_jobs._fetch_current_predictions')
    def test_check_prediction_changes_job_with_error_handling(
        self, mock_fetch, db_session
    ):
        """Test prediction changes job handles errors gracefully."""
        # Mock predictions to raise exception
        mock_fetch.side_effect = Exception("Failed to fetch predictions")

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            # Should not raise exception
            check_prediction_changes_job()

        # Job should complete without error

    def test_cleanup_prediction_history_job(self, db_session, sample_alert):
        """Test cleanup of old prediction history."""
        # Create old history entries
        for i in range(5):
            history = PredictionChangeHistory(
                alert_id=sample_alert.id,
                previous_prediction=80000.00 + i * 1000,
                new_prediction=81000.00 + i * 1000,
                change_percent=1.25,
                horizon="24h",
                triggered_at=datetime.utcnow() - timedelta(days=40 + i)
            )
            db_session.add(history)

        # Create recent history entry (should be kept)
        recent_history = PredictionChangeHistory(
            alert_id=sample_alert.id,
            previous_prediction=85000.00,
            new_prediction=86000.00,
            change_percent=1.18,
            horizon="24h",
            triggered_at=datetime.utcnow() - timedelta(days=5)
        )
        db_session.add(recent_history)
        db_session.commit()

        with patch('app.rabbitmq.producer.RabbitMQProducer.connect', return_value=True):
            cleanup_prediction_history_job()

        # Check old history was deleted
        remaining = db_session.query(PredictionChangeHistory).filter(
            PredictionChangeHistory.alert_id == sample_alert.id
        ).all()

        # Only the recent history should remain
        assert len(remaining) == 1
        assert remaining[0].id == recent_history.id