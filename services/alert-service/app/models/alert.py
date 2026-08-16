"""Alert models for PostgreSQL"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, JSON, 
    ForeignKey, Text, Enum, Index, CheckConstraint,
    Float
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()


# ============================================
# ENUMS
# ============================================

class AlertType(PyEnum):
    REACHES = "reaches"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"


class AlertStatus(PyEnum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


class NotificationType(PyEnum):
    PRICE_ALERT = "price_alert"
    PREDICTION_ALERT = "prediction_alert"
    CONFIDENCE_ALERT = "confidence_alert"
    MACRO_ALERT = "macro_alert"


class HistoryEventType(PyEnum):
    CREATED = "created"
    UPDATED = "updated"
    EVALUATION = "evaluation"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    DISMISSED = "dismissed"
    DISABLED = "disabled"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ============================================
# MODELS
# ============================================

class PriceAlert(Base):
    """Price level alerts for BTC"""
    __tablename__ = "price_alerts"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, index=True)
    
    # Alert configuration
    threshold_price = Column(Float, nullable=False)
    alert_type = Column(Enum(AlertType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    asset = Column(String(50), default="BTC/USD")
    
    # Status
    status = Column(Enum(AlertStatus, values_callable=lambda x: [e.value for e in x]), default=AlertStatus.ACTIVE)
    one_time = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    triggered_at = Column(DateTime)
    
    # Notification preferences
    notify_in_app = Column(Boolean, default=True)
    notify_email = Column(Boolean, default=True)
    
    # Metadata
    name = Column(String(255))
    description = Column(Text)
    
    # Relationships
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")
    notifications = relationship("InAppNotification", back_populates="alert")
    
    __table_args__ = (
        Index('idx_price_alerts_user_id_status', 'user_id', 'status'),
        Index('idx_price_alerts_user_id_created', 'user_id', 'created_at'),
        Index('idx_price_alerts_status_asset', 'status', 'asset'),
        CheckConstraint('threshold_price > 0', name='ck_threshold_positive'),
        CheckConstraint("alert_type IN ('reaches', 'crosses_above', 'crosses_below')", name='ck_alert_type_valid'),
        CheckConstraint("status IN ('active', 'triggered', 'disabled', 'expired')", name='ck_status_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "threshold_price": self.threshold_price,
            "alert_type": self.alert_type.value if self.alert_type else None,
            "asset": self.asset,
            "status": self.status.value if self.status else None,
            "one_time": self.one_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "notify_in_app": self.notify_in_app,
            "notify_email": self.notify_email,
            "name": self.name,
            "description": self.description,
        }


class AlertHistory(Base):
    """Alert history and audit trail"""
    __tablename__ = "alert_history"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    alert_id = Column(PGUUID, ForeignKey("price_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event details
    event_type = Column(Enum(HistoryEventType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    event_source = Column(String(50))
    
    # Trigger details
    triggered_price = Column(Float)
    threshold_price = Column(Float)
    alert_type = Column(String(50))
    
    # Status changes
    previous_status = Column(Enum(AlertStatus, values_callable=lambda x: [e.value for e in x]))
    new_status = Column(Enum(AlertStatus, values_callable=lambda x: [e.value for e in x]))
    
    # Notification tracking
    in_app_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    email_error = Column(Text)
    read_status = Column(Boolean, default=False)
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    note = Column(Text)
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    alert = relationship("PriceAlert", back_populates="history")
    
    __table_args__ = (
        Index('idx_alert_history_alert_id_created', 'alert_id', 'created_at'),
        Index('idx_alert_history_event_type', 'event_type'),
        Index('idx_alert_history_triggered_at', 'triggered_at'),
        CheckConstraint("event_type IN ('evaluation', 'triggered', 'acknowledged', 'dismissed', 'disabled', 'expired', 'archived', 'created', 'updated', 'deleted')", name='ck_event_type_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "alert_id": str(self.alert_id),
            "event_type": self.event_type.value if self.event_type else None,
            "event_source": self.event_source,
            "triggered_price": self.triggered_price,
            "threshold_price": self.threshold_price,
            "alert_type": self.alert_type,
            "previous_status": self.previous_status.value if self.previous_status else None,
            "new_status": self.new_status.value if self.new_status else None,
            "in_app_sent": self.in_app_sent,
            "email_sent": self.email_sent,
            "read_status": self.read_status,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InAppNotification(Base):
    """In-app notifications for users"""
    __tablename__ = "in_app_notifications"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, index=True)
    alert_id = Column(PGUUID, ForeignKey("price_alerts.id", ondelete="SET NULL"), index=True)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    # Additional data
    data = Column(JSON)
    action_url = Column(Text)
    
    # Status
    read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime)
    
    # Relationship
    alert = relationship("PriceAlert", back_populates="notifications")
    
    __table_args__ = (
        Index('idx_notifications_user_id_unread', 'user_id', 'read'),
        Index('idx_notifications_created_at', 'created_at'),
        Index('idx_notifications_user_id_created', 'user_id', 'created_at'),
        CheckConstraint("notification_type IN ('price_alert', 'prediction_alert', 'confidence_alert', 'macro_alert')", name='ck_notification_type_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "alert_id": str(self.alert_id) if self.alert_id else None,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type.value if self.notification_type else None,
            "data": self.data,
            "action_url": self.action_url,
            "read": self.read,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }