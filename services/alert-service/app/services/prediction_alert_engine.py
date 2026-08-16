"""Prediction change alert engine"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeHistory,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection
)
from app.models.alert import AlertHistory
from app.services.notification_service import NotificationService
from app.rabbitmq.producer import RabbitMQProducer

logger = logging.getLogger(__name__)


class PredictionAlertEngine:
    """Core prediction change alert engine"""

    def __init__(self, db: Session, producer: Optional[RabbitMQProducer] = None):
        self.db = db
        self.producer = producer
        self.notification_service = NotificationService(db)

    def evaluate_prediction_alerts(
        self,
        prediction_data: Dict[str, Any]
    ) -> List[PredictionChangeAlert]:
        """
        Evaluate all prediction alerts against new prediction data.

        Args:
            prediction_data: {
                "asset": "BTC/USD",
                "horizon": "24h",
                "prediction": 85000.50,
                "previous_prediction": 82000.00,
                "confidence": 85.5,
                "previous_confidence": 92.0,
                "timestamp": "2026-08-16T10:00:00Z"
            }
        """
        triggered_alerts = []
        asset = prediction_data.get("asset", "BTC/USD")
        horizon = prediction_data.get("horizon", "24h")
        new_prediction = prediction_data.get("prediction")
        previous_prediction = prediction_data.get("previous_prediction")
        new_confidence = prediction_data.get("confidence")
        previous_confidence = prediction_data.get("previous_confidence")

        if not new_prediction or not previous_prediction:
            logger.warning("Missing prediction data for evaluation")
            return triggered_alerts

        logger.info(f"🔍 Evaluating prediction alerts for {asset} ({horizon})")

        # Get all active prediction alerts
        alerts = self.db.query(PredictionChangeAlert).filter(
            PredictionChangeAlert.status == PredictionAlertStatus.ACTIVE,
            PredictionChangeAlert.asset == asset,
            PredictionChangeAlert.horizon == horizon
        ).all()

        logger.info(f"📊 Found {len(alerts)} active prediction alerts")

        for alert in alerts:
            # Calculate changes
            prediction_change = self._calculate_percent_change(
                previous_prediction, new_prediction
            )
            confidence_change = None
            if new_confidence and previous_confidence:
                confidence_change = self._calculate_percent_change(
                    previous_confidence, new_confidence
                )

            # Check if alert should trigger
            should_trigger = False
            trigger_reason = []

            # Check prediction change
            if abs(prediction_change) >= alert.threshold_percent:
                should_trigger = True
                trigger_reason.append(f"Prediction changed by {prediction_change:.2f}%")

            # Check confidence change
            if alert.monitor_confidence and confidence_change is not None:
                if abs(confidence_change) >= alert.confidence_threshold_percent:
                    should_trigger = True
                    trigger_reason.append(f"Confidence changed by {confidence_change:.2f}%")

            # Check direction
            if should_trigger and alert.direction != PredictionDirection.BOTH:
                if alert.direction == PredictionDirection.UP and prediction_change < 0:
                    should_trigger = False
                elif alert.direction == PredictionDirection.DOWN and prediction_change > 0:
                    should_trigger = False

            if should_trigger:
                self._handle_triggered_alert(
                    alert=alert,
                    previous_prediction=previous_prediction,
                    new_prediction=new_prediction,
                    prediction_change=prediction_change,
                    previous_confidence=previous_confidence,
                    new_confidence=new_confidence,
                    confidence_change=confidence_change,
                    trigger_reason=", ".join(trigger_reason),
                    horizon=horizon
                )
                triggered_alerts.append(alert)

        return triggered_alerts

    def _handle_triggered_alert(
        self,
        alert: PredictionChangeAlert,
        previous_prediction: float,
        new_prediction: float,
        prediction_change: float,
        previous_confidence: Optional[float],
        new_confidence: Optional[float],
        confidence_change: Optional[float],
        trigger_reason: str,
        horizon: str
    ):
        """Handle a triggered prediction alert."""
        logger.info(f"🔔 Prediction alert triggered: {alert.id} for user {alert.user_id}")

        # Generate recommendation
        recommendation = self._generate_recommendation(
            prediction_change, confidence_change
        )

        # Update alert
        alert.status = PredictionAlertStatus.TRIGGERED
        alert.triggered_at = datetime.utcnow()
        self.db.commit()

        # Create history entry
        history = PredictionChangeHistory(
            alert_id=alert.id,
            previous_prediction=previous_prediction,
            new_prediction=new_prediction,
            change_percent=prediction_change,
            horizon=horizon,
            previous_confidence=previous_confidence,
            new_confidence=new_confidence,
            confidence_change_percent=confidence_change,
            triggered_at=datetime.utcnow(),
            event_source="scheduler",
            recommendation=recommendation
        )
        self.db.add(history)
        self.db.commit()

        # Create in-app notification
        if alert.notify_in_app:
            self._create_in_app_notification(
                alert, previous_prediction, new_prediction,
                prediction_change, recommendation, horizon
            )

        # Queue email notification
        if alert.notify_email:
            self._queue_email_notification(
                alert, previous_prediction, new_prediction,
                prediction_change, recommendation, horizon
            )

        # Publish AlertTriggered event
        if self.producer:
            self.producer.publish_alert_triggered(
                alert_id=str(alert.id),
                user_id=str(alert.user_id),
                alert_type="prediction_change",
                condition=f"Prediction changed by {prediction_change:.2f}%",
                triggered_value={
                    "previous_prediction": previous_prediction,
                    "new_prediction": new_prediction,
                    "change_percent": prediction_change,
                    "horizon": horizon,
                    "trigger_reason": trigger_reason
                },
                config={
                    "threshold_percent": alert.threshold_percent,
                    "horizon": alert.horizon.value if alert.horizon else None,
                    "direction": alert.direction.value if alert.direction else None
                }
            )

    def _create_in_app_notification(
        self,
        alert: PredictionChangeAlert,
        previous_prediction: float,
        new_prediction: float,
        change_percent: float,
        recommendation: str,
        horizon: str
    ):
        """Create in-app notification for triggered alert."""
        title = f"📊 Prediction Change Alert: {change_percent:+.2f}%"
        message = (
            f"BTC prediction for {horizon} changed from ${previous_prediction:,.2f} "
            f"to ${new_prediction:,.2f} ({change_percent:+.2f}%)\n\n"
            f"💡 {recommendation}"
        )

        self.notification_service.create_notification(
            user_id=alert.user_id,
            alert_id=alert.id,
            title=title,
            message=message,
            notification_type="prediction_alert",
            data={
                "alert_id": str(alert.id),
                "previous_prediction": previous_prediction,
                "new_prediction": new_prediction,
                "change_percent": change_percent,
                "horizon": horizon,
                "recommendation": recommendation
            },
            action_url=f"/alerts/prediction/{alert.id}"
        )
        logger.debug(f"📱 In-app notification created for prediction alert {alert.id}")

    def _queue_email_notification(
        self,
        alert: PredictionChangeAlert,
        previous_prediction: float,
        new_prediction: float,
        change_percent: float,
        recommendation: str,
        horizon: str
    ):
        """Queue email notification for triggered alert."""
        # Placeholder - will be implemented in T8.5
        logger.info(f"📧 Email notification queued for prediction alert {alert.id}")

    def _generate_recommendation(
        self,
        prediction_change: float,
        confidence_change: Optional[float]
    ) -> str:
        """Generate recommendation based on prediction change."""
        if prediction_change > 0:
            if confidence_change and confidence_change > 0:
                return "📈 Strong buy signal: Prediction and confidence both increasing. Consider entering a long position."
            elif confidence_change and confidence_change < -5:
                return "⚠️ Cautious: Prediction up but confidence dropping. Consider waiting for confirmation."
            else:
                return "📈 Upward prediction: Consider adjusting your position accordingly."
        else:
            if confidence_change and confidence_change > 0:
                return "📉 Strong sell signal: Prediction down but confidence increasing. Consider taking profits."
            elif confidence_change and confidence_change < -5:
                return "⚠️ Cautious: Prediction down and confidence dropping. Consider reducing exposure."
            else:
                return "📉 Downward prediction: Consider adjusting your position accordingly."

    @staticmethod
    def _calculate_percent_change(old_value: float, new_value: float) -> float:
        """Calculate percent change between two values."""
        if old_value == 0:
            return 0
        return ((new_value - old_value) / old_value) * 100

    def get_alerts_for_horizon(self, horizon: str) -> List[PredictionChangeAlert]:
        """Get active alerts for a specific horizon."""
        return self.db.query(PredictionChangeAlert).filter(
            PredictionChangeAlert.status == PredictionAlertStatus.ACTIVE,
            PredictionChangeAlert.horizon == horizon
        ).all()