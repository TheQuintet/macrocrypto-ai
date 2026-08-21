"""Scheduled jobs for prediction monitoring"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.prediction_alert_engine import PredictionAlertEngine
from app.services.prediction_email_service import PredictionEmailService
from app.rabbitmq.producer import RabbitMQProducer
from app.models.prediction_alert import PredictionChangeHistory

logger = logging.getLogger(__name__)


def check_prediction_changes_job():
    """
    Scheduled job to check for prediction changes.
    Runs every hour.
    """
    logger.info("🔄 Running check_prediction_changes_job")

    db = SessionLocal()
    producer = RabbitMQProducer()
    producer.connect()

    try:
        # Initialize engine
        engine = PredictionAlertEngine(db, producer)

        # Get current predictions from cache or database
        # This would typically fetch from Data Service via API or cache
        # For now, we'll simulate with a placeholder
        predictions = _fetch_current_predictions()

        for prediction in predictions:
            horizon = prediction.get("horizon", "24h")
            triggered = engine.evaluate_prediction_alerts(prediction)

            if triggered:
                logger.info(f"🔔 {len(triggered)} prediction alerts triggered for {horizon}")

                # Send emails for triggered alerts
                email_service = PredictionEmailService(db)
                for alert in triggered:
                    # Get the history entry for this alert
                    history = db.query(PredictionChangeHistory).filter(
                        PredictionChangeHistory.alert_id == alert.id
                    ).order_by(
                        PredictionChangeHistory.created_at.desc()
                    ).first()

                    if history:
                        # In production, fetch user email from user service
                        user_email = f"user_{alert.user_id}@example.com"  # TODO: Fetch from user service
                        email_service.queue_prediction_alert_email(
                            alert=alert,
                            previous_prediction=history.previous_prediction,
                            new_prediction=history.new_prediction,
                            change_percent=history.change_percent,
                            recommendation=history.recommendation,
                            horizon=history.horizon,
                            user_email=user_email
                        )

        logger.info("✅ check_prediction_changes_job completed successfully")

    except Exception as e:
        logger.error(f"❌ Error in check_prediction_changes_job: {e}")
        db.rollback()

    finally:
        db.close()
        producer.close()


def _fetch_current_predictions() -> list:
    """
    Fetch current predictions from Data Service.
    This is a placeholder - in production, this would call the Data Service API.
    """
    # Placeholder - in production, fetch from Data Service
    now = datetime.utcnow()
    return [
        {
            "asset": "BTC/USD",
            "horizon": "24h",
            "prediction": 85000.50,
            "previous_prediction": 82000.00,
            "confidence": 85.5,
            "previous_confidence": 92.0,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "asset": "BTC/USD",
            "horizon": "7d",
            "prediction": 88000.00,
            "previous_prediction": 86000.00,
            "confidence": 78.0,
            "previous_confidence": 82.0,
            "timestamp": datetime.utcnow().isoformat()
        }
    ]


def cleanup_prediction_history_job():
    """
    Cleanup old prediction history entries.
    Runs daily.
    """
    logger.info("🔄 Running cleanup_prediction_history_job")

    db = SessionLocal()

    try:
        # Delete history older than 30 days based on triggered_at
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        deleted = db.query(PredictionChangeHistory).filter(
            PredictionChangeHistory.triggered_at < cutoff_date
        ).delete()

        db.commit()
        logger.info(f"✅ Deleted {deleted} old prediction history entries")

    except Exception as e:
        logger.error(f"❌ Error in cleanup_prediction_history_job: {e}")
        db.rollback()

    finally:
        db.close()