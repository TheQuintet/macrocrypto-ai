"""Alert history and audit trail service"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.alert import AlertHistory, PriceAlert, AlertStatus, HistoryEventType

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing alert history and audit trail"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_alert_history(
        self,
        alert_id: UUID,
        limit: int = 50,
        offset: int = 0,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple:
        """Get history for a specific alert."""
        query = self.db.query(AlertHistory).filter(
            AlertHistory.alert_id == alert_id
        )
        
        if event_type:
            try:
                query = query.filter(AlertHistory.event_type == HistoryEventType(event_type))
            except ValueError:
                pass
        
        if start_date:
            query = query.filter(AlertHistory.created_at >= start_date)
        
        if end_date:
            query = query.filter(AlertHistory.created_at <= end_date)
        
        total = query.count()
        history = query.order_by(
            desc(AlertHistory.created_at)
        ).offset(offset).limit(limit).all()
        
        return total, history
    
    def get_user_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple:
        """Get all history for a user across all alerts."""
        # First get all alert IDs for the user
        alert_ids = self.db.query(PriceAlert.id).filter(
            PriceAlert.user_id == user_id
        ).subquery()
        
        query = self.db.query(AlertHistory).filter(
            AlertHistory.alert_id.in_(alert_ids)
        )
        
        if start_date:
            query = query.filter(AlertHistory.created_at >= start_date)
        
        if end_date:
            query = query.filter(AlertHistory.created_at <= end_date)
        
        total = query.count()
        history = query.order_by(
            desc(AlertHistory.created_at)
        ).offset(offset).limit(limit).all()
        
        return total, history
    
    def get_triggered_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """Get all triggered alerts history for a user."""
        alert_ids = self.db.query(PriceAlert.id).filter(
            PriceAlert.user_id == user_id
        ).subquery()
        
        query = self.db.query(AlertHistory).filter(
            and_(
                AlertHistory.alert_id.in_(alert_ids),
                AlertHistory.event_type == HistoryEventType.TRIGGERED
            )
        )
        
        total = query.count()
        history = query.order_by(
            desc(AlertHistory.triggered_at)
        ).offset(offset).limit(limit).all()
        
        return total, history
    
    def log_alert_acknowledged(self, alert_id: UUID, ip_address: Optional[str] = None):
        """Log when a user acknowledges an alert."""
        history = AlertHistory(
            alert_id=alert_id,
            event_type=HistoryEventType.ACKNOWLEDGED,
            event_source="user",
            ip_address=ip_address,
            triggered_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
        logger.debug(f"📝 Alert acknowledged: {alert_id}")
    
    def log_alert_dismissed(self, alert_id: UUID, ip_address: Optional[str] = None):
        """Log when a user dismisses an alert."""
        history = AlertHistory(
            alert_id=alert_id,
            event_type=HistoryEventType.DISMISSED,
            event_source="user",
            ip_address=ip_address,
            triggered_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
        logger.debug(f"📝 Alert dismissed: {alert_id}")
    
    def log_alert_disabled(self, alert_id: UUID, ip_address: Optional[str] = None):
        """Log when a user disables an alert."""
        history = AlertHistory(
            alert_id=alert_id,
            event_type=HistoryEventType.DISABLED,
            event_source="user",
            ip_address=ip_address,
            triggered_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.commit()
        logger.debug(f"📝 Alert disabled: {alert_id}")
    
    def get_alert_trigger_count(self, alert_id: UUID) -> int:
        """Get total trigger count for an alert."""
        return self.db.query(AlertHistory).filter(
            and_(
                AlertHistory.alert_id == alert_id,
                AlertHistory.event_type == HistoryEventType.TRIGGERED
            )
        ).count()
    
    def get_user_trigger_count(self, user_id: UUID) -> int:
        """Get total trigger count for a user."""
        alert_ids = self.db.query(PriceAlert.id).filter(
            PriceAlert.user_id == user_id
        ).subquery()
        
        return self.db.query(AlertHistory).filter(
            and_(
                AlertHistory.alert_id.in_(alert_ids),
                AlertHistory.event_type == HistoryEventType.TRIGGERED
            )
        ).count()
    
    def cleanup_old_history(self, days_to_keep: int = 30) -> int:
        """Delete history older than the retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        old_history = self.db.query(AlertHistory).filter(
            AlertHistory.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        logger.info(f"🧹 Cleaned up {old_history} old history records")
        return old_history