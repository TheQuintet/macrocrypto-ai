"""Macro event notification service"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.macro_alert import MacroEventNotification
from app.services.notification_service import NotificationService
from app.config import settings

logger = logging.getLogger(__name__)


class MacroNotificationService:
    """Service for managing macro event in-app notifications"""

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def create_macro_notification(
        self,
        user_id: UUID,
        alert_id: UUID,
        event_name: str,
        event_type: str,
        event_date: datetime,
        timing: str,
        impact: str,
        description: Optional[str] = None,
        data: Optional[dict] = None,
        action_url: Optional[str] = None
    ) -> MacroEventNotification:
        """Create a macro event notification."""
        notification = MacroEventNotification(
            user_id=user_id,
            alert_id=alert_id,
            event_name=event_name,
            event_type=event_type,
            event_date=event_date,
            timing=timing,
            impact=impact,
            description=description,
            data=data,
            action_url=action_url,
            read=False,
            is_archived=False,
            sent_at=datetime.utcnow()
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        logger.debug(f"📱 Macro notification created: {notification.id}")
        return notification

    def get_macro_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """Get macro notifications for a user."""
        query = self.db.query(MacroEventNotification).filter(
            MacroEventNotification.user_id == user_id,
            MacroEventNotification.is_archived == False
        )

        if unread_only:
            query = query.filter(MacroEventNotification.read == False)

        total = query.count()
        notifications = query.order_by(
            desc(MacroEventNotification.sent_at)
        ).offset(offset).limit(limit).all()

        return total, notifications

    def mark_as_read(self, notification_id: UUID) -> Optional[MacroEventNotification]:
        """Mark a macro notification as read."""
        notification = self.db.query(MacroEventNotification).filter(
            MacroEventNotification.id == notification_id
        ).first()

        if notification and not notification.read:
            notification.read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(notification)
            logger.debug(f"📱 Macro notification marked as read: {notification_id}")

        return notification

    def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all macro notifications as read for a user."""
        notifications = self.db.query(MacroEventNotification).filter(
            MacroEventNotification.user_id == user_id,
            MacroEventNotification.read == False,
            MacroEventNotification.is_archived == False
        ).all()

        count = 0
        for notification in notifications:
            notification.read = True
            notification.read_at = datetime.utcnow()
            count += 1

        self.db.commit()
        logger.debug(f"📱 Marked {count} macro notifications as read")
        return count

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread macro notifications for a user."""
        return self.db.query(MacroEventNotification).filter(
            MacroEventNotification.user_id == user_id,
            MacroEventNotification.read == False,
            MacroEventNotification.is_archived == False
        ).count()

    def archive_old_notifications(self, user_id: UUID, older_than_days: int = 30) -> int:
        """Archive old macro notifications."""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        notifications = self.db.query(MacroEventNotification).filter(
            MacroEventNotification.user_id == user_id,
            MacroEventNotification.sent_at < cutoff_date,
            MacroEventNotification.is_archived == False
        ).all()

        count = 0
        for notification in notifications:
            notification.is_archived = True
            count += 1

        self.db.commit()
        logger.debug(f"📱 Archived {count} macro notifications")
        return count

    # ============================================
    # GLOBAL NOTIFICATION MANAGEMENT
    # ============================================

    def get_all_notifications(
        self,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """
        Get notifications without filtering by user_id.

        Only non-archived notifications within the configured
        history_notification_days period are returned.

        This method is intentionally separate from get_macro_notifications()
        so the existing user-scoped behavior remains unchanged.
        """
        # Calculate the oldest notification date that should be included.
        # The number of days is controlled through application configuration.
        cutoff_date = datetime.utcnow() - timedelta(
            days=settings.HISTORY_NOTIFICATION_DAYS
        )

        # Start with all non-archived notifications within the
        # configured notification history period.
        query = self.db.query(MacroEventNotification).filter(
            MacroEventNotification.is_archived == False,
            MacroEventNotification.sent_at >= cutoff_date
        )

        # When requested, restrict the result to unread notifications.
        if unread_only:
            query = query.filter(
                MacroEventNotification.read == False
            )

        # Count the complete filtered result before applying pagination.
        total = query.count()

        # Return the newest notifications first and apply pagination.
        notifications = query.order_by(
            desc(MacroEventNotification.sent_at)
        ).offset(offset).limit(limit).all()

        return total, notifications

    def mark_all_notifications_as_read(self) -> int:
        """
        Mark all notifications as read without filtering by user_id.

        Only unread, non-archived notifications within the configured
        history_notification_days period are updated.

        Returns:
            int: Number of notifications that were marked as read.
        """
        # Calculate the beginning of the configured notification history.
        cutoff_date = datetime.utcnow() - timedelta(
            days=settings.HISTORY_NOTIFICATION_DAYS
        )

        # Retrieve all unread and non-archived notifications that are
        # still inside the configured notification history period.
        notifications = self.db.query(MacroEventNotification).filter(
            MacroEventNotification.read == False,
            MacroEventNotification.is_archived == False,
            MacroEventNotification.sent_at >= cutoff_date
        ).all()

        count = 0
        read_at = datetime.utcnow()

        # Mark each matching notification as read and record when
        # the notification was read.
        for notification in notifications:
            notification.read = True
            notification.read_at = read_at
            count += 1

        # Persist all notification updates in a single transaction.
        self.db.commit()

        logger.debug(
            f"📱 Marked {count} notifications as read"
        )

        return count