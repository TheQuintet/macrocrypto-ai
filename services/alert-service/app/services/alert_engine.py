"""Alert evaluation engine"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.alert import PriceAlert, AlertStatus, AlertType, AlertHistory, HistoryEventType
from app.models.notification import InAppNotification, NotificationType
from app.services.notification_service import NotificationService
from app.rabbitmq.producer import RabbitMQProducer

logger = logging.getLogger(__name__)


class AlertEngine:
    """Core alert evaluation engine"""
    
    def __init__(self, db: Session, producer: Optional[RabbitMQProducer] = None):
        self.db = db
        self.producer = producer
        self.notification_service = NotificationService(db)
    
    def evaluate_price_alerts(self, price_data: Dict[str, Any]) -> List[PriceAlert]:
        """
        Evaluate all price alerts against new price data.
        
        Args:
            price_data: {
                "symbol": "BTC/USD",
                "price": 85000.50,
                "previous_price": 84000.00,
                "timestamp": "2026-08-15T10:00:00Z"
            }
        
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        symbol = price_data.get("symbol", "BTC/USD")
        current_price = price_data.get("price")
        previous_price = price_data.get("previous_price")
        
        if not current_price:
            logger.warning("No price data provided for evaluation")
            return triggered_alerts
        
        logger.info(f"🔍 Evaluating price alerts for {symbol} at ${current_price:,.2f}")
        
        # Get all active price alerts
        alerts = self.db.query(PriceAlert).filter(
            PriceAlert.status == AlertStatus.ACTIVE,
            PriceAlert.asset == symbol
        ).all()
        
        logger.info(f"📊 Found {len(alerts)} active price alerts")
        
        for alert in alerts:
            triggered = self._evaluate_alert_condition(alert, current_price, previous_price)
            
            if triggered:
                self._handle_triggered_alert(alert, current_price)
                triggered_alerts.append(alert)
        
        return triggered_alerts
    
    def _evaluate_alert_condition(
        self, 
        alert: PriceAlert, 
        current_price: float, 
        previous_price: Optional[float]
    ) -> bool:
        """
        Evaluate if alert condition is met.
        
        Alert types:
        - reaches: current_price == threshold (within tolerance)
        - crosses_above: previous_price <= threshold < current_price
        - crosses_below: previous_price >= threshold > current_price
        """
        threshold = alert.threshold_price
        alert_type = alert.alert_type
        
        triggered = False
        
        if alert_type == AlertType.REACHES:
            # Allow small tolerance for floating point
            tolerance = 0.01
            if abs(current_price - threshold) <= tolerance:
                triggered = True
                logger.info(f"✅ Alert {alert.id}: Price reached ${threshold:,.2f}")
        
        elif alert_type == AlertType.CROSSES_ABOVE:
            if previous_price is not None:
                if previous_price <= threshold < current_price:
                    triggered = True
                    logger.info(f"✅ Alert {alert.id}: Price crossed above ${threshold:,.2f}")
        
        elif alert_type == AlertType.CROSSES_BELOW:
            if previous_price is not None:
                if previous_price >= threshold > current_price:
                    triggered = True
                    logger.info(f"✅ Alert {alert.id}: Price crossed below ${threshold:,.2f}")
        
        # Log evaluation
        self._log_evaluation(alert, current_price, triggered)
        
        return triggered
    
    def _handle_triggered_alert(self, alert: PriceAlert, current_price: float):
        """Handle a triggered alert - update status and send notifications."""
        logger.info(f"🔔 Alert triggered: {alert.id} for user {alert.user_id}")
        
        # Update alert
        alert.status = AlertStatus.TRIGGERED
        alert.triggered_at = datetime.utcnow()
        
        # Disable one-time alerts
        if alert.one_time:
            alert.status = AlertStatus.DISABLED
        
        self.db.commit()
        
        # Create history entry
        self._create_history_entry(alert, current_price)
        
        # Create in-app notification
        if alert.notify_in_app:
            self._create_in_app_notification(alert, current_price)
        
        # Send email notification
        if alert.notify_email:
            self._queue_email_notification(alert, current_price)
        
        # Publish AlertTriggered event
        if self.producer:
            self.producer.publish_alert_triggered(
                alert_id=str(alert.id),
                user_id=str(alert.user_id),
                alert_type="price",
                condition=alert.alert_type.value if alert.alert_type else "unknown",
                triggered_value={
                    "current_price": current_price,
                    "threshold_price": alert.threshold_price,
                    "triggered_at": datetime.utcnow().isoformat()
                },
                config={
                    "threshold_price": alert.threshold_price,
                    "alert_type": alert.alert_type.value if alert.alert_type else None,
                    "one_time": alert.one_time
                }
            )
    
    def _log_evaluation(self, alert: PriceAlert, current_price: float, triggered: bool):
        """Log alert evaluation for monitoring."""
        history = AlertHistory(
            alert_id=alert.id,
            event_type=HistoryEventType.EVALUATION,
            event_source="engine",
            triggered_price=current_price,
            threshold_price=alert.threshold_price,
            alert_type=alert.alert_type.value if alert.alert_type else None,
            previous_status=AlertStatus.ACTIVE,
            new_status=AlertStatus.TRIGGERED if triggered else AlertStatus.ACTIVE,
            triggered_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
    
    def _create_history_entry(self, alert: PriceAlert, current_price: float):
        """Create history entry for triggered alert."""
        history = AlertHistory(
            alert_id=alert.id,
            event_type=HistoryEventType.TRIGGERED,
            event_source="engine",
            triggered_price=current_price,
            threshold_price=alert.threshold_price,
            alert_type=alert.alert_type.value if alert.alert_type else None,
            previous_status=AlertStatus.ACTIVE,
            new_status=AlertStatus.TRIGGERED,
            triggered_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
        logger.debug(f"📝 History entry created for alert {alert.id}")
    
    def _create_in_app_notification(self, alert: PriceAlert, current_price: float):
        """Create in-app notification for triggered alert."""
        title, message = self._format_alert_message(alert, current_price)
        
        notification = InAppNotification(
            user_id=alert.user_id,
            alert_id=alert.id,
            title=title,
            message=message,
            notification_type=NotificationType.PRICE_ALERT,
            data={
                "alert_id": str(alert.id),
                "triggered_price": current_price,
                "threshold_price": alert.threshold_price,
                "alert_type": alert.alert_type.value if alert.alert_type else None,
                "asset": alert.asset
            },
            action_url=f"/alerts/{alert.id}"
        )
        self.db.add(notification)
        self.db.commit()
        logger.debug(f"📱 In-app notification created for alert {alert.id}")
    
    def _queue_email_notification(self, alert: PriceAlert, current_price: float):
        """Queue email notification for triggered alert."""
        # This will be implemented in T7.5
        logger.info(f"📧 Email notification queued for alert {alert.id}")
        # Placeholder - will be implemented in T7.5
    
    def _format_alert_message(self, alert: PriceAlert, current_price: float) -> tuple:
        """Format alert title and message."""
        alert_type = alert.alert_type
        threshold = alert.threshold_price
        symbol = alert.asset
        
        type_labels = {
            AlertType.REACHES: "reached",
            AlertType.CROSSES_ABOVE: "crossed above",
            AlertType.CROSSES_BELOW: "crossed below",
        }
        
        label = type_labels.get(alert_type, "triggered")
        
        title = f"Price Alert: {symbol} {label} ${threshold:,.2f}"
        message = f"{symbol} is now at ${current_price:,.2f} (target: ${threshold:,.2f})"
        
        return title, message
    
    def get_alerts_requiring_check(self, limit: int = 1000) -> List[PriceAlert]:
        """Get active alerts that need to be checked."""
        return self.db.query(PriceAlert).filter(
            PriceAlert.status == AlertStatus.ACTIVE
        ).limit(limit).all()
    
    def expire_alerts(self) -> int:
        """Expire alerts that have passed their expiry date."""
        # For now, one-time alerts are disabled when triggered
        # This method can be extended for time-based expiry
        expired_count = 0
        # Implementation for time-based expiry
        return expired_count