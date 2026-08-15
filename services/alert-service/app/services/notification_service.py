"""Notification service for alert delivery"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.alert import InAppNotification, NotificationType, AlertHistory
from app.models.alert import PriceAlert

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing in-app notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self,
        user_id: UUID,
        alert_id: UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
        data: Optional[dict] = None,
        action_url: Optional[str] = None
    ) -> InAppNotification:
        """Create an in-app notification."""
        notification = InAppNotification(
            user_id=user_id,
            alert_id=alert_id,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data,
            action_url=action_url,
            read=False,
            is_archived=False
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        logger.debug(f"📱 Notification created: {notification.id}")
        return notification
    
    def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """Get notifications for a user."""
        query = self.db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id,
            InAppNotification.is_archived == False
        )
        
        if unread_only:
            query = query.filter(InAppNotification.read == False)
        
        total = query.count()
        notifications = query.order_by(
            desc(InAppNotification.created_at)
        ).offset(offset).limit(limit).all()
        
        return total, notifications
    
    def mark_as_read(self, notification_id: UUID) -> Optional[InAppNotification]:
        """Mark a notification as read."""
        notification = self.db.query(InAppNotification).filter(
            InAppNotification.id == notification_id
        ).first()
        
        if notification and not notification.read:
            notification.read = True
            notification.read_at = datetime.utcnow()
            
            # Update history
            history = self.db.query(AlertHistory).filter(
                AlertHistory.alert_id == notification.alert_id
            ).order_by(desc(AlertHistory.created_at)).first()
            
            if history:
                history.read_status = True
            
            self.db.commit()
            self.db.refresh(notification)
            logger.debug(f"📱 Notification marked as read: {notification_id}")
        
        return notification
    
    def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        notifications = self.db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id,
            InAppNotification.read == False,
            InAppNotification.is_archived == False
        ).all()
        
        count = 0
        for notification in notifications:
            notification.read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        self.db.commit()
        logger.debug(f"📱 Marked {count} notifications as read")
        return count
    
    def archive_notifications(self, user_id: UUID, older_than_days: int = 30) -> int:
        """Archive old notifications."""
        cutoff_date = datetime.utcnow().date()
        # Implementation for archiving
        # This would be called by a scheduled job
        return 0
    
    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        return self.db.query(InAppNotification).filter(
            InAppNotification.user_id == user_id,
            InAppNotification.read == False,
            InAppNotification.is_archived == False
        ).count()