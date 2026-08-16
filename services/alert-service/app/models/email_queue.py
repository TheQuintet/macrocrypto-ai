"""Email queue models for PostgreSQL"""

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, 
    ForeignKey, Enum, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.alert import Base
import uuid
from datetime import datetime
from enum import Enum as PyEnum


class EmailStatus(PyEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"


class EmailQueue(Base):
    """Email queue for reliable email delivery"""
    __tablename__ = "email_queue"
    
    id = Column(PGUUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID, nullable=False, index=True)
    alert_id = Column(PGUUID, ForeignKey("price_alerts.id", ondelete="SET NULL"), index=True)
    
    # Email content
    to_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text)
    
    # Delivery tracking
    status = Column(Enum(EmailStatus, values_callable=lambda x: [e.value for e in x]), default=EmailStatus.PENDING)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_attempt_at = Column(DateTime)
    error_message = Column(Text)
    
    # Priority and scheduling
    priority = Column(Integer, default=5)
    scheduled_for = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_email_queue_status_scheduled', 'status', 'scheduled_for'),
        Index('idx_email_queue_user_id_status', 'user_id', 'status'),
        Index('idx_email_queue_priority', 'priority'),
        CheckConstraint("status IN ('pending', 'sent', 'failed', 'retry')", name='ck_email_status_valid'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "alert_id": str(self.alert_id) if self.alert_id else None,
            "to_email": self.to_email,
            "subject": self.subject,
            "status": self.status.value if self.status else None,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "priority": self.priority,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }