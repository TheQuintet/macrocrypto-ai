"""Integration tests for macro email service"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.alert import PriceAlert, AlertType, AlertStatus

from app.services.macro_email_service import MacroEmailService
from app.services.email_service import EmailService
from app.models.macro_alert import (
    MacroEventAlert,
    MacroEventCache,
    EventType,
    EventTiming,
    EventImpact,
    MacroAlertStatus
)
from app.models.email_queue import EmailQueue, EmailStatus


class TestMacroEmailService:
    """Test cases for MacroEmailService."""

    @pytest.fixture
    def macro_email_service(self, db_session):
        """Create macro email service instance."""
        return MacroEmailService(db_session)

    @pytest.fixture
    def sample_alert(self, db_session: Session):
        """Create a sample alert for testing."""
        alert = PriceAlert(
            id=uuid4(),
            user_id=uuid4(),
            threshold_price=85000.00,
            alert_type=AlertType.REACHES,
            asset="BTC/USD",
            status=AlertStatus.ACTIVE,
            one_time=True,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert


    @pytest.fixture
    def sample_macro_event(self, db_session: Session, sample_alert: PriceAlert):
        """Create a sample macro alert for testing."""
        alert = MacroEventAlert(
            id=sample_alert.id,  # Reuse PriceAlert ID for FK
            user_id=uuid4(),
            event_type=EventType.FED,
            timing=EventTiming.ONE_DAY,
            impact_filter=EventImpact.HIGH,
            status=MacroAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    @pytest.fixture
    def sample_event(self, db_session, sample_alert ):
        """Create a sample macro event for testing."""
        event = MacroEventCache(
            id=sample_alert.id,
            event_id="test_event_001",
            event_type=EventType.FED,
            event_name="Federal Reserve Meeting",
            description="FOMC interest rate decision",
            scheduled_at=datetime.utcnow() + timedelta(days=2),
            timezone="UTC",
            impact=EventImpact.HIGH,
            notified=False
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        return event

    def test_queue_macro_alert_email(
        self, macro_email_service, db_session, sample_alert, sample_event
    ):
        """Test queuing a macro alert email."""
        user_email = "test@example.com"

        macro_email_service.queue_macro_alert_email(
            alert=sample_alert,
            event=sample_event,
            timing="1d",
            user_email=user_email
        )

        # Check email was queued
        email = db_session.query(EmailQueue).filter(
            EmailQueue.alert_id == str(sample_alert.id)
        ).first()

        assert email is not None
        assert email.to_email == user_email
        assert "Macro Event Alert" in email.subject
        assert "Federal Reserve Meeting" in email.html_body
        assert email.status == EmailStatus.PENDING

    def test_email_content_creation(self, macro_email_service, sample_alert, sample_event):
        """Test email content creation for macro alert."""
        subject, html_body, text_body = macro_email_service._create_email_content(
            alert=sample_alert,
            event=sample_event,
            timing="1d"
        )

        assert "Macro Event Alert" in subject
        assert "Federal Reserve Meeting" in subject

        assert "<html>" in html_body
        assert "Federal Reserve Meeting" in html_body
        assert "FOMC interest rate decision" in html_body
        assert "HIGH" in html_body
        assert "View Economic Calendar" in html_body

        assert "Federal Reserve Meeting" in text_body
        assert "FOMC interest rate decision" in text_body
        assert "HIGH" in text_body
        assert "View Economic Calendar" in text_body

    def test_btc_impact_description(self, macro_email_service, sample_event):
        """Test BTC impact description generation."""
        sample_event.event_type = EventType.FED
        description = macro_email_service._get_btc_impact_description(sample_event)

        assert "Federal Reserve" in description or "rate" in description

        sample_event.event_type = EventType.CPI
        description = macro_email_service._get_btc_impact_description(sample_event)

        assert "CPI" in description or "inflation" in description

    @patch('app.services.email_service.smtplib.SMTP')
    def test_email_retry_logic(
        self, mock_smtp, macro_email_service, db_session, sample_alert, sample_event
    ):
        """Test email retry logic on failure."""
        # Queue email
        user_email = "test@example.com"
        macro_email_service.queue_macro_alert_email(
            alert=sample_alert,
            event=sample_event,
            timing="1d",
            user_email=user_email
        )

        email = db_session.query(EmailQueue).filter(
            EmailQueue.alert_id == str(sample_alert.id)
        ).first()

        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")

        # Process email
        email_service = EmailService(db_session)
        with patch('app.config.settings.EMAIL_ENABLED', True):
            with patch('app.config.settings.SMTP_USER', 'test@example.com'):
                with patch('app.config.settings.SMTP_PASSWORD', 'password'):
                    result = email_service._send_email(email)

        assert result is False
        assert email.attempts == 1
        assert email.status == EmailStatus.RETRY

    def test_timezone_adjusted_event_times(self, macro_email_service, sample_alert):
        """Test timezone-adjusted event times in email."""
        event = MacroEventCache(
            id=sample_alert.id,
            event_id="test_event_002",
            event_type=EventType.FED,
            event_name="Test Event",
            description="Test with timezone",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            timezone="America/New_York",
            impact=EventImpact.HIGH,
            notified=False
        )

        subject, html_body, text_body = macro_email_service._create_email_content(
            alert=sample_alert,
            event=event,
            timing="1d"
        )

        # Check timezone info is included
        assert "UTC" in html_body or "America/New_York" in html_body