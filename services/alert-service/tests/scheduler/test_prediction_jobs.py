"""Tests for prediction scheduled jobs."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from app.scheduler.prediction_jobs import (
    check_prediction_changes_job,
    cleanup_prediction_history_job,
    _fetch_current_predictions,
)
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeHistory,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection,
)
from app.models.alert import PriceAlert, AlertType, AlertStatus
from app.database.session import SessionLocal


class TestPredictionJobs:
    """Test cases for prediction scheduled jobs."""

    def test_fetch_current_predictions(self):
        """Test fetching current predictions."""
        predictions = _fetch_current_predictions()

        assert len(predictions) == 2

        assert predictions[0]["asset"] == "BTC/USD"
        assert predictions[0]["horizon"] == "24h"
        assert predictions[0]["prediction"] == 85000.50
        assert predictions[0]["previous_prediction"] == 82000.00
        assert predictions[0]["confidence"] == 85.5
        assert predictions[0]["previous_confidence"] == 92.0
        assert "timestamp" in predictions[0]

        assert predictions[1]["asset"] == "BTC/USD"
        assert predictions[1]["horizon"] == "7d"
        assert predictions[1]["prediction"] == 88000.00
        assert predictions[1]["previous_prediction"] == 86000.00
        assert predictions[1]["confidence"] == 78.0
        assert predictions[1]["previous_confidence"] == 82.0
        assert "timestamp" in predictions[1]

    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_triggers_alerts(
        self,
        mock_fetch,
        db_session,
    ):
        """Test prediction changes job triggers alerts."""

        price_alert = PriceAlert(
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

        db_session.add(price_alert)
        db_session.commit()
        db_session.refresh(price_alert)

        alert = PredictionChangeAlert(
            id=price_alert.id,
            user_id=uuid4(),
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            monitor_confidence=False,
            confidence_threshold_percent=5.0,
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True,
        )

        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        alerts_test = (
            db_session.query(PredictionChangeAlert)
            .filter(
                PredictionChangeAlert.status
                == PredictionAlertStatus.ACTIVE
            )
            .all()
        )

        assert len(alerts_test) >= 1

        fresh_session = SessionLocal()

        alerts_fresh = (
            fresh_session.query(PredictionChangeAlert)
            .filter(
                PredictionChangeAlert.status
                == PredictionAlertStatus.ACTIVE
            )
            .all()
        )

        fresh_session.close()

        if len(alerts_fresh) == 0:
            pytest.skip(
                "Database doesn't persist across sessions "
                "(likely SQLite in-memory). "
                "This test requires a persistent database."
            )

        mock_fetch.return_value = [
            {
                "asset": "BTC/USD",
                "horizon": "24h",
                "prediction": 85000.00,
                "previous_prediction": 82000.00,
                "confidence": 85.0,
                "previous_confidence": 90.0,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            with patch(
                "app.rabbitmq.producer.RabbitMQProducer.publish_alert_triggered",
                return_value=True,
            ):
                check_prediction_changes_job()

        db_session.refresh(alert)

        assert alert.status == PredictionAlertStatus.TRIGGERED

        history = (
            db_session.query(PredictionChangeHistory)
            .filter(
                PredictionChangeHistory.alert_id == alert.id
            )
            .first()
        )

        assert history is not None
        assert history.previous_prediction == 82000.00
        assert history.new_prediction == 85000.00
        assert history.change_percent is not None

    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_no_triggers(
        self,
        mock_fetch,
        db_session,
    ):
        """Test prediction changes job when no alerts should trigger."""

        price_alert = PriceAlert(
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

        db_session.add(price_alert)
        db_session.commit()
        db_session.refresh(price_alert)

        alert = PredictionChangeAlert(
            id=price_alert.id,
            user_id=uuid4(),
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            monitor_confidence=False,
            confidence_threshold_percent=5.0,
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True,
        )

        db_session.add(alert)
        db_session.commit()

        fresh_session = SessionLocal()

        alerts_fresh = (
            fresh_session.query(PredictionChangeAlert)
            .filter(
                PredictionChangeAlert.status
                == PredictionAlertStatus.ACTIVE
            )
            .all()
        )

        fresh_session.close()

        if len(alerts_fresh) == 0:
            pytest.skip(
                "Database doesn't persist across sessions "
                "(likely SQLite in-memory). "
                "This test requires a persistent database."
            )

        mock_fetch.return_value = [
            {
                "asset": "BTC/USD",
                "horizon": "24h",
                "prediction": 82200.00,
                "previous_prediction": 82000.00,
                "confidence": 90.0,
                "previous_confidence": 92.0,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            with patch(
                "app.rabbitmq.producer.RabbitMQProducer.publish_alert_triggered",
                return_value=True,
            ):
                check_prediction_changes_job()

        db_session.refresh(alert)

        assert alert.status == PredictionAlertStatus.ACTIVE

    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_with_error_handling(
        self,
        mock_fetch,
        db_session,
    ):
        """Test prediction changes job handles errors gracefully."""

        mock_fetch.side_effect = Exception(
            "Failed to fetch predictions"
        )

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            check_prediction_changes_job()

        # The job handles the exception internally.

    @patch("app.scheduler.prediction_jobs.PredictionEmailService")
    @patch("app.scheduler.prediction_jobs.PredictionAlertEngine")
    @patch("app.scheduler.prediction_jobs.RabbitMQProducer")
    @patch("app.scheduler.prediction_jobs.SessionLocal")
    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_queues_email_for_triggered_alert(
        self,
        mock_fetch,
        mock_session_local,
        mock_producer_cls,
        mock_engine_cls,
        mock_email_cls,
    ):
        """Test triggered alerts with history are queued for email."""

        db = Mock()
        producer = Mock()
        engine = Mock()
        email_service = Mock()

        mock_session_local.return_value = db
        mock_producer_cls.return_value = producer
        mock_engine_cls.return_value = engine
        mock_email_cls.return_value = email_service

        alert = Mock()
        alert.id = uuid4()
        alert.user_id = uuid4()

        history = Mock()
        history.previous_prediction = 82000.00
        history.new_prediction = 85000.00
        history.change_percent = 3.66
        history.recommendation = "BUY"
        history.horizon = "24h"

        engine.evaluate_prediction_alerts.return_value = [alert]

        (
            db.query.return_value
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = history

        prediction = {
            "asset": "BTC/USD",
            "horizon": "24h",
            "prediction": 85000.00,
            "previous_prediction": 82000.00,
            "confidence": 85.0,
            "previous_confidence": 90.0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        mock_fetch.return_value = [prediction]

        check_prediction_changes_job()

        engine.evaluate_prediction_alerts.assert_called_once_with(
            prediction
        )

        mock_email_cls.assert_called_once_with(db)

        email_service.queue_prediction_alert_email.assert_called_once_with(
            alert=alert,
            previous_prediction=82000.00,
            new_prediction=85000.00,
            change_percent=3.66,
            recommendation="BUY",
            horizon="24h",
            user_email=f"user_{alert.user_id}@example.com",
        )

        producer.connect.assert_called_once()
        producer.close.assert_called_once()
        db.close.assert_called_once()

    @patch("app.scheduler.prediction_jobs.PredictionEmailService")
    @patch("app.scheduler.prediction_jobs.PredictionAlertEngine")
    @patch("app.scheduler.prediction_jobs.RabbitMQProducer")
    @patch("app.scheduler.prediction_jobs.SessionLocal")
    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_does_not_email_without_history(
        self,
        mock_fetch,
        mock_session_local,
        mock_producer_cls,
        mock_engine_cls,
        mock_email_cls,
    ):
        """Test triggered alert without history does not queue email."""

        db = Mock()
        producer = Mock()
        engine = Mock()
        email_service = Mock()

        mock_session_local.return_value = db
        mock_producer_cls.return_value = producer
        mock_engine_cls.return_value = engine
        mock_email_cls.return_value = email_service

        alert = Mock()
        alert.id = uuid4()
        alert.user_id = uuid4()

        engine.evaluate_prediction_alerts.return_value = [alert]

        (
            db.query.return_value
            .filter.return_value
            .order_by.return_value
            .first.return_value
        ) = None

        prediction = {
            "asset": "BTC/USD",
            "horizon": "24h",
            "prediction": 85000.00,
            "previous_prediction": 82000.00,
            "confidence": 85.0,
            "previous_confidence": 90.0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        mock_fetch.return_value = [prediction]

        check_prediction_changes_job()

        engine.evaluate_prediction_alerts.assert_called_once_with(
            prediction
        )

        email_service.queue_prediction_alert_email.assert_not_called()

        producer.close.assert_called_once()
        db.close.assert_called_once()

    @patch("app.scheduler.prediction_jobs.PredictionAlertEngine")
    @patch("app.scheduler.prediction_jobs.RabbitMQProducer")
    @patch("app.scheduler.prediction_jobs.SessionLocal")
    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_processes_multiple_predictions(
        self,
        mock_fetch,
        mock_session_local,
        mock_producer_cls,
        mock_engine_cls,
    ):
        """Test that every fetched prediction is evaluated."""

        db = Mock()
        producer = Mock()
        engine = Mock()

        mock_session_local.return_value = db
        mock_producer_cls.return_value = producer
        mock_engine_cls.return_value = engine

        engine.evaluate_prediction_alerts.return_value = []

        predictions = [
            {
                "asset": "BTC/USD",
                "horizon": "24h",
                "prediction": 85000.00,
            },
            {
                "asset": "BTC/USD",
                "horizon": "7d",
                "prediction": 88000.00,
            },
            {
                "asset": "BTC/USD",
                "horizon": "30d",
                "prediction": 92000.00,
            },
        ]

        mock_fetch.return_value = predictions

        check_prediction_changes_job()

        assert engine.evaluate_prediction_alerts.call_count == 3

        engine.evaluate_prediction_alerts.assert_any_call(
            predictions[0]
        )
        engine.evaluate_prediction_alerts.assert_any_call(
            predictions[1]
        )
        engine.evaluate_prediction_alerts.assert_any_call(
            predictions[2]
        )

        producer.connect.assert_called_once()
        producer.close.assert_called_once()
        db.close.assert_called_once()

    @patch("app.scheduler.prediction_jobs.PredictionAlertEngine")
    @patch("app.scheduler.prediction_jobs.RabbitMQProducer")
    @patch("app.scheduler.prediction_jobs.SessionLocal")
    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_uses_default_horizon(
        self,
        mock_fetch,
        mock_session_local,
        mock_producer_cls,
        mock_engine_cls,
    ):
        """Test prediction processing when horizon is missing."""

        db = Mock()
        producer = Mock()
        engine = Mock()

        mock_session_local.return_value = db
        mock_producer_cls.return_value = producer
        mock_engine_cls.return_value = engine

        engine.evaluate_prediction_alerts.return_value = []

        prediction = {
            "asset": "BTC/USD",
            "prediction": 85000.00,
        }

        mock_fetch.return_value = [prediction]

        check_prediction_changes_job()

        engine.evaluate_prediction_alerts.assert_called_once_with(
            prediction
        )

        producer.connect.assert_called_once()
        producer.close.assert_called_once()
        db.close.assert_called_once()

    @patch("app.scheduler.prediction_jobs.PredictionAlertEngine")
    @patch("app.scheduler.prediction_jobs.RabbitMQProducer")
    @patch("app.scheduler.prediction_jobs.SessionLocal")
    @patch("app.scheduler.prediction_jobs._fetch_current_predictions")
    def test_check_prediction_changes_job_rolls_back_on_engine_error(
        self,
        mock_fetch,
        mock_session_local,
        mock_producer_cls,
        mock_engine_cls,
    ):
        """Test rollback and cleanup when prediction evaluation fails."""

        db = Mock()
        producer = Mock()
        engine = Mock()

        mock_session_local.return_value = db
        mock_producer_cls.return_value = producer
        mock_engine_cls.return_value = engine

        prediction = {
            "asset": "BTC/USD",
            "horizon": "24h",
            "prediction": 85000.00,
        }

        mock_fetch.return_value = [prediction]

        engine.evaluate_prediction_alerts.side_effect = Exception(
            "evaluation failed"
        )

        check_prediction_changes_job()

        db.rollback.assert_called_once()
        db.close.assert_called_once()
        producer.close.assert_called_once()

    def test_cleanup_prediction_history_job(self, db_session):
        """Test cleanup of old prediction history."""

        price_alert = PriceAlert(
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

        db_session.add(price_alert)
        db_session.commit()
        db_session.refresh(price_alert)

        sample_alert = PredictionChangeAlert(
            id=price_alert.id,
            user_id=uuid4(),
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            monitor_confidence=False,
            confidence_threshold_percent=5.0,
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True,
        )

        db_session.add(sample_alert)
        db_session.commit()

        fresh_session = SessionLocal()

        alerts_fresh = (
            fresh_session.query(PredictionChangeAlert)
            .filter(
                PredictionChangeAlert.status
                == PredictionAlertStatus.ACTIVE
            )
            .all()
        )

        fresh_session.close()

        if len(alerts_fresh) == 0:
            pytest.skip(
                "Database doesn't persist across sessions "
                "(likely SQLite in-memory). "
                "This test requires a persistent database."
            )

        for i in range(5):
            history = PredictionChangeHistory(
                alert_id=sample_alert.id,
                previous_prediction=80000.00 + i * 1000,
                new_prediction=81000.00 + i * 1000,
                change_percent=1.25,
                horizon="24h",
                triggered_at=datetime.utcnow()
                - timedelta(days=40 + i),
                created_at=datetime.utcnow()
                - timedelta(days=40 + i),
            )

            db_session.add(history)

        recent_history = PredictionChangeHistory(
            alert_id=sample_alert.id,
            previous_prediction=85000.00,
            new_prediction=86000.00,
            change_percent=1.18,
            horizon="24h",
            triggered_at=datetime.utcnow() - timedelta(days=5),
            created_at=datetime.utcnow() - timedelta(days=5),
        )

        db_session.add(recent_history)
        db_session.commit()

        total_before = (
            db_session.query(PredictionChangeHistory)
            .filter(
                PredictionChangeHistory.alert_id == sample_alert.id
            )
            .count()
        )

        assert total_before == 6

        with patch(
            "app.rabbitmq.producer.RabbitMQProducer.connect",
            return_value=True,
        ):
            cleanup_prediction_history_job()

        remaining = (
            db_session.query(PredictionChangeHistory)
            .filter(
                PredictionChangeHistory.alert_id == sample_alert.id
            )
            .all()
        )

        assert len(remaining) == 1
        assert remaining[0].id == recent_history.id

    @patch("app.scheduler.prediction_jobs.SessionLocal")
    def test_cleanup_prediction_history_job_deletes_old_history(
        self,
        mock_session_local,
    ):
        """Test that cleanup deletes records older than 30 days."""

        db = Mock()
        mock_session_local.return_value = db

        query = db.query.return_value
        filtered_query = query.filter.return_value
        filtered_query.delete.return_value = 5

        cleanup_prediction_history_job()

        db.query.assert_called_once_with(
            PredictionChangeHistory
        )

        query.filter.assert_called_once()

        filtered_query.delete.assert_called_once_with()

        db.commit.assert_called_once()
        db.rollback.assert_not_called()
        db.close.assert_called_once()

    @patch("app.scheduler.prediction_jobs.SessionLocal")
    def test_cleanup_prediction_history_job_rolls_back_on_error(
        self,
        mock_session_local,
    ):
        """Test cleanup rollback when the database operation fails."""

        db = Mock()
        mock_session_local.return_value = db

        query = db.query.return_value
        query.filter.side_effect = Exception(
            "database failure"
        )

        cleanup_prediction_history_job()

        db.rollback.assert_called_once()
        db.commit.assert_not_called()
        db.close.assert_called_once()

    @patch(
        "app.scheduler.prediction_jobs.RabbitMQProducer"
    )
    @patch(
        "app.scheduler.prediction_jobs.SessionLocal"
    )
    @patch(
        "app.scheduler.prediction_jobs._fetch_current_predictions"
    )
    def test_check_prediction_changes_job_closes_resources_when_fetch_fails(
        self,
        mock_fetch,
        mock_session_local,
        mock_producer_cls,
    ):
        """Test resources are closed after prediction fetch failure."""

        db = Mock()
        producer = Mock()

        mock_session_local.return_value = db
        mock_producer_cls.return_value = producer

        mock_fetch.side_effect = RuntimeError(
            "Data Service unavailable"
        )

        check_prediction_changes_job()

        db.rollback.assert_called_once()
        db.close.assert_called_once()
        producer.close.assert_called_once()

