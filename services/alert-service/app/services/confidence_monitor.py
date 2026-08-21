"""Confidence level change monitoring service"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeHistory,
    PredictionAlertStatus
)

logger = logging.getLogger(__name__)


class ConfidenceMonitor:
    """Monitor confidence level changes and trigger alerts"""

    def __init__(self, db: Session):
        self.db = db

    def check_confidence_changes(
        self,
        alert: PredictionChangeAlert,
        previous_confidence: float,
        new_confidence: float
    ) -> Optional[Dict[str, Any]]:
        """
        Check if confidence change should trigger an alert.

        Returns:
            Dict with confidence change details if triggered, None otherwise
        """
        if not alert.monitor_confidence:
            return None

        if previous_confidence is None or new_confidence is None:
            return None

        # Calculate change
        change_percent = self._calculate_percent_change(
            previous_confidence, new_confidence
        )

        # Check threshold
        threshold = alert.confidence_threshold_percent
        if abs(change_percent) >= threshold:
            logger.info(
                f"Confidence change detected: {change_percent:+.2f}% "
                f"(threshold: {threshold}%) for alert {alert.id}"
            )

            return {
                "previous_confidence": previous_confidence,
                "new_confidence": new_confidence,
                "change_percent": change_percent,
                "threshold": threshold,
                "direction": "up" if change_percent > 0 else "down",
                "triggered": True
            }

        return None

    def get_confidence_history(
        self,
        alert_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get confidence change history for an alert."""
        history = self.db.query(PredictionChangeHistory).filter(
            PredictionChangeHistory.alert_id == alert_id
        ).order_by(
            PredictionChangeHistory.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": str(h.id),
                "previous_confidence": h.previous_confidence,
                "new_confidence": h.new_confidence,
                "confidence_change_percent": h.confidence_change_percent,
                "triggered_at": h.triggered_at.isoformat() if h.triggered_at else None,
                "recommendation": h.recommendation
            }
            for h in history
        ]

    @staticmethod
    def _calculate_percent_change(old_value: float, new_value: float) -> float:
        """Calculate percent change between two values."""
        if old_value == 0:
            return 0
        return ((new_value - old_value) / old_value) * 100

    def get_active_alerts_for_confidence_monitoring(self) -> List[PredictionChangeAlert]:
        """Get all active alerts that have confidence monitoring enabled."""
        return self.db.query(PredictionChangeAlert).filter(
            PredictionChangeAlert.status == PredictionAlertStatus.ACTIVE,
            PredictionChangeAlert.monitor_confidence == True
        ).all()