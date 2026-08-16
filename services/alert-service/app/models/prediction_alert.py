"""Prediction change alert models for PostgreSQL"""

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

class PredictionHorizon(PyEnum):
    HOUR_24 = "24h"
    DAY_7 = "7d"


class PredictionAlertStatus(PyEnum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


class PredictionDirection(PyEnum):
    UP = "up"
    DOWN = "down"
    BOTH = "both"


# ============================================
# MODELS
# ============================================

class PredictionChangeAlert(Base):
    """Prediction change alerts for BTC"""
    __tablename__ = "prediction_change_alerts"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, index=True)
    
    # Alert configuration
    threshold_percent = Column(Float, nullable=False)  # 1%, 2%, 5%, 10%
    horizon = Column(Enum(PredictionHorizon, values_callable=lambda x: [e.value for e in x]), nullable=False)
    direction = Column(Enum(PredictionDirection, values_callable=lambda x: [e.value for e in x]), default=PredictionDirection.BOTH)
    asset = Column(String(50), default="BTC/USD")
    
    # Confidence change monitoring
    monitor_confidence = Column(Boolean, default=True)
    confidence_threshold_percent = Column(Float, default=5.0)  # Default ±5%
    
    # Status
    status = Column(Enum(PredictionAlertStatus, values_callable=lambda x: [e.value for e in x]), default=PredictionAlertStatus.ACTIVE)
    
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
    history = relationship("PredictionChangeHistory", back_populates="alert", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_prediction_alerts_user_id_status', 'user_id', 'status'),
        Index('idx_prediction_alerts_user_id_created', 'user_id', 'created_at'),
        Index('idx_prediction_alerts_horizon', 'horizon'),
        CheckConstraint('threshold_percent > 0 AND threshold_percent <= 10', name='ck_threshold_range'),
        CheckConstraint("horizon IN ('24h', '7d')", name='ck_horizon_valid'),
        CheckConstraint("direction IN ('up', 'down', 'both')", name='ck_direction_valid'),
        CheckConstraint("status IN ('active', 'triggered', 'disabled', 'expired')", name='ck_status_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "threshold_percent": self.threshold_percent,
            "horizon": self.horizon.value if self.horizon else None,
            "direction": self.direction.value if self.direction else None,
            "asset": self.asset,
            "monitor_confidence": self.monitor_confidence,
            "confidence_threshold_percent": self.confidence_threshold_percent,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "notify_in_app": self.notify_in_app,
            "notify_email": self.notify_email,
            "name": self.name,
            "description": self.description,
        }


class PredictionChangeHistory(Base):
    """Prediction change alert history"""
    __tablename__ = "prediction_change_history"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    alert_id = Column(PGUUID, ForeignKey("prediction_change_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Prediction details
    previous_prediction = Column(Float)
    new_prediction = Column(Float)
    change_percent = Column(Float)
    horizon = Column(String(10))
    
    # Confidence details
    previous_confidence = Column(Float)
    new_confidence = Column(Float)
    confidence_change_percent = Column(Float)
    
    # Trigger details
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_source = Column(String(50))  # 'scheduler', 'manual', 'system'
    
    # Notification tracking
    in_app_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    email_error = Column(Text)
    read_status = Column(Boolean, default=False)
    
    # Recommendation
    recommendation = Column(Text)
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    alert = relationship("PredictionChangeAlert", back_populates="history")
    
    __table_args__ = (
        Index('idx_prediction_history_alert_id', 'alert_id'),
        Index('idx_prediction_history_triggered_at', 'triggered_at'),
        Index('idx_prediction_history_alert_id_created', 'alert_id', 'created_at'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "alert_id": str(self.alert_id),
            "previous_prediction": self.previous_prediction,
            "new_prediction": self.new_prediction,
            "change_percent": self.change_percent,
            "horizon": self.horizon,
            "previous_confidence": self.previous_confidence,
            "new_confidence": self.new_confidence,
            "confidence_change_percent": self.confidence_change_percent,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "event_source": self.event_source,
            "in_app_sent": self.in_app_sent,
            "email_sent": self.email_sent,
            "read_status": self.read_status,
            "recommendation": self.recommendation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PredictionChangeConfig(Base):
    """User configuration for prediction change alerts"""
    __tablename__ = "prediction_change_configs"

    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, unique=True, index=True)
    
    # Default thresholds
    default_threshold = Column(Float, default=2.0)  # Default 2%
    confidence_change_threshold = Column(Float, default=5.0)  # Default ±5%
    
    # Preferences
    default_horizon = Column(Enum(PredictionHorizon, values_callable=lambda x: [e.value for e in x]), default=PredictionHorizon.HOUR_24)
    notify_in_app_default = Column(Boolean, default=True)
    notify_email_default = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_prediction_configs_user_id', 'user_id'),
        CheckConstraint('default_threshold > 0 AND default_threshold <= 10', name='ck_config_threshold_range'),
        CheckConstraint("default_horizon IN ('24h', '7d')", name='ck_config_horizon_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "default_threshold": self.default_threshold,
            "confidence_change_threshold": self.confidence_change_threshold,
            "default_horizon": self.default_horizon.value if self.default_horizon else None,
            "notify_in_app_default": self.notify_in_app_default,
            "notify_email_default": self.notify_email_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }