"""Macro event alert models for PostgreSQL"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, JSON,
    ForeignKey, Text, Enum, Index, CheckConstraint,
    Float
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.models.alert import Base
import uuid
from datetime import datetime
from enum import Enum as PyEnum


# ============================================
# ENUMS
# ============================================

class EventType(PyEnum):
    FED = "fed"
    CPI = "cpi"
    GDP = "gdp"
    EMPLOYMENT = "employment"
    OTHER = "other"


class EventTiming(PyEnum):
    ONE_DAY = "1d"
    TWELVE_HOURS = "12h"
    ONE_HOUR = "1h"


class EventImpact(PyEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MacroAlertStatus(PyEnum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


# ============================================
# MODELS
# ============================================

class MacroEventAlert(Base):
    """Macro event alerts for users"""
    __tablename__ = "macro_event_alerts"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, index=True)
    
    # Alert configuration
    event_type = Column(Enum(EventType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    timing = Column(Enum(EventTiming, values_callable=lambda x: [e.value for e in x]), nullable=False)
    impact_filter = Column(Enum(EventImpact, values_callable=lambda x: [e.value for e in x]), default=EventImpact.HIGH)
    
    # Status
    status = Column(Enum(MacroAlertStatus, values_callable=lambda x: [e.value for e in x]), default=MacroAlertStatus.ACTIVE)
    
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
    notifications = relationship("MacroEventNotification", back_populates="alert", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_macro_alerts_user_id_status', 'user_id', 'status'),
        Index('idx_macro_alerts_user_id_event_type', 'user_id', 'event_type'),
        Index('idx_macro_alerts_event_type_timing', 'event_type', 'timing'),
        CheckConstraint("event_type IN ('fed', 'cpi', 'gdp', 'employment', 'other')", name='ck_event_type_valid'),
        CheckConstraint("timing IN ('1d', '12h', '1h')", name='ck_timing_valid'),
        CheckConstraint("impact IN ('high', 'medium', 'low')", name='ck_impact_valid'),
        CheckConstraint("status IN ('active', 'triggered', 'disabled', 'expired')", name='ck_status_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_type": self.event_type.value if self.event_type else None,
            "timing": self.timing.value if self.timing else None,
            "impact_filter": self.impact_filter.value if self.impact_filter else None,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "notify_in_app": self.notify_in_app,
            "notify_email": self.notify_email,
            "name": self.name,
            "description": self.description,
        }


class MacroEventSubscription(Base):
    """User subscriptions to macro event types"""
    __tablename__ = "macro_event_subscriptions"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, index=True)
    event_type = Column(Enum(EventType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    subscribed = Column(Boolean, default=True)
    impact_filter = Column(Enum(EventImpact, values_callable=lambda x: [e.value for e in x]), default=EventImpact.HIGH)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_macro_subscriptions_user_id', 'user_id'),
        Index('idx_macro_subscriptions_user_event', 'user_id', 'event_type'),
        CheckConstraint("event_type IN ('fed', 'cpi', 'gdp', 'employment', 'other')", name='ck_sub_event_type_valid'),
        CheckConstraint("impact IN ('high', 'medium', 'low')", name='ck_sub_impact_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_type": self.event_type.value if self.event_type else None,
            "subscribed": self.subscribed,
            "impact_filter": self.impact_filter.value if self.impact_filter else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MacroEventNotification(Base):
    """In-app notifications for macro events"""
    __tablename__ = "macro_event_notifications"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, index=True)
    alert_id = Column(PGUUID, ForeignKey("macro_event_alerts.id", ondelete="SET NULL"), index=True)
    
    # Event details
    event_name = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_date = Column(DateTime, nullable=False)
    timing = Column(String(10), nullable=False)  # 1d, 12h, 1h
    impact = Column(String(20), nullable=False)
    description = Column(Text)
    
    # Additional data
    data = Column(JSON)
    action_url = Column(Text)
    
    # Status
    read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime)
    
    # Relationship
    alert = relationship("MacroEventAlert", back_populates="notifications")
    
    __table_args__ = (
        Index('idx_macro_notifications_user_id', 'user_id'),
        Index('idx_macro_notifications_user_sent', 'user_id', 'sent_at'),
        Index('idx_macro_notifications_alert_id', 'alert_id'),
        Index('idx_macro_notifications_user_read', 'user_id', 'read'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "alert_id": str(self.alert_id) if self.alert_id else None,
            "event_name": self.event_name,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "timing": self.timing,
            "impact": self.impact,
            "description": self.description,
            "data": self.data,
            "action_url": self.action_url,
            "read": self.read,
            "is_archived": self.is_archived,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


class MacroEventCache(Base):
    """Cached macro events from economic calendar"""
    __tablename__ = "macro_event_cache"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    event_id = Column(String(100), unique=True, index=True)  # External event ID
    event_type = Column(Enum(EventType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    event_name = Column(String(255), nullable=False)
    description = Column(Text)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    timezone = Column(String(50), default="UTC")
    impact = Column(Enum(EventImpact, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    # Event details
    actual_value = Column(String(50))
    expected_value = Column(String(50))
    previous_value = Column(String(50))
    
    # Source
    source = Column(String(100))
    url = Column(Text)
    
    # Status
    notified = Column(Boolean, default=False)  # Whether alerts have been sent
    notified_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_macro_cache_event_type', 'event_type'),
        Index('idx_macro_cache_scheduled_at', 'scheduled_at'),
        Index('idx_macro_cache_impact', 'impact'),
        Index('idx_macro_cache_notified', 'notified'),
        CheckConstraint("event_type IN ('fed', 'cpi', 'gdp', 'employment', 'other')", name='ck_cache_event_type_valid'),
        CheckConstraint("impact IN ('high', 'medium', 'low')", name='ck_cache_impact_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "event_id": self.event_id,
            "event_type": self.event_type.value if self.event_type else None,
            "event_name": self.event_name,
            "description": self.description,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "timezone": self.timezone,
            "impact": self.impact.value if self.impact else None,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "previous_value": self.previous_value,
            "source": self.source,
            "url": self.url,
            "notified": self.notified,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }