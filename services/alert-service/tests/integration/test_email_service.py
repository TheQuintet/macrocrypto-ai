"""Integration tests for email service"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime

from app.services.email_service import EmailService
from app.models.alert import PriceAlert, AlertStatus, AlertType
from app.models.email_queue import EmailQueue, EmailStatus


class TestEmailService:
    """Test cases for EmailService."""

    @pytest.fixture
    def email_service(self, db_session):
        """Create email service instance."""
        return EmailService(db_session)

    @pytest.fixture
    def sample_alert(self, db_session):
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

    def test_queue_email(self, email_service, db_session, sample_alert):
        """Test queuing an email."""
        email = email_service.queue_email(
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text body",
            priority=5
        )

        assert email is not None
        assert email.to_email == "test@example.com"
        assert email.subject == "Test Subject"
        assert email.html_body == "<h1>Test HTML</h1>"
        assert email.text_body == "Test text body"
        assert email.status == EmailStatus.PENDING
        assert email.attempts == 0
        assert email.max_attempts == 3

    def test_queue_email_default_values(self, email_service, db_session, sample_alert):
        """Test queuing email with default values."""
        email = email_service.queue_email(
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>"
        )

        assert email.text_body == ""  # Default empty string
        assert email.priority == 5  # Default priority
        assert email.max_attempts == 3

    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_service, db_session, sample_alert):
        """Test sending email successfully."""
        email = EmailQueue(
            id=uuid4(),
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text",
            status=EmailStatus.PENDING,
            attempts=0,
            max_attempts=3
        )
        db_session.add(email)
        db_session.commit()

        # Mock SMTP connection
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Set EMAIL_ENABLED to True for this test
        with patch('app.config.settings.EMAIL_ENABLED', True):
            with patch('app.config.settings.SMTP_USER', 'test@example.com'):
                with patch('app.config.settings.SMTP_PASSWORD', 'password'):
                    result = email_service._send_email(email)

        assert result == True
        assert email.status == EmailStatus.SENT
        assert email.sent_at is not None

    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_email_retry_on_failure(self, mock_smtp, email_service, db_session, sample_alert):
        """Test email retry on failure."""
        email = EmailQueue(
            id=uuid4(),
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text",
            status=EmailStatus.PENDING,
            attempts=0,
            max_attempts=3
        )
        db_session.add(email)
        db_session.commit()

        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")

        with patch('app.config.settings.EMAIL_ENABLED', True):
            with patch('app.config.settings.SMTP_USER', 'test@example.com'):
                with patch('app.config.settings.SMTP_PASSWORD', 'password'):
                    result = email_service._send_email(email)

        assert result == False
        assert email.attempts == 1
        assert email.last_attempt_at is not None
        assert email.status == EmailStatus.RETRY
        assert email.error_message == "SMTP connection failed"

    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_email_fails_after_max_attempts(self, mock_smtp, email_service, db_session, sample_alert):
        """Test email fails after max attempts."""
        email = EmailQueue(
            id=uuid4(),
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text",
            status=EmailStatus.PENDING,
            attempts=3,  # Already at max attempts
            max_attempts=3
        )
        db_session.add(email)
        db_session.commit()

        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")

        with patch('app.config.settings.EMAIL_ENABLED', True):
            with patch('app.config.settings.SMTP_USER', 'test@example.com'):
                with patch('app.config.settings.SMTP_PASSWORD', 'password'):
                    result = email_service._send_email(email)

        assert result == False
        assert email.status == EmailStatus.FAILED

    def test_process_email_queue(self, email_service, db_session, sample_alert):
        """Test processing email queue."""
        # Create multiple emails
        for i in range(5):
            email = EmailQueue(
                id=uuid4(),
                user_id=str(sample_alert.user_id),
                alert_id=str(sample_alert.id),
                to_email=f"test{i}@example.com",
                subject=f"Test {i}",
                html_body=f"<h1>Test {i}</h1>",
                text_body=f"Test {i}",
                status=EmailStatus.PENDING,
                attempts=0,
                max_attempts=3,
                priority=5,
                scheduled_for=datetime.utcnow()
            )
            db_session.add(email)
        db_session.commit()

        # Mock _send_email to return True
        with patch.object(email_service, '_send_email', return_value=True):
            processed = email_service.process_email_queue(limit=3)

        assert processed == 3

    def test_create_alert_email_body(self, email_service, sample_alert):
        """Test creating email body for alert."""
        subject, html_body, text_body = email_service.create_alert_email_body(
            alert=sample_alert,
            current_price=85000.00,
            chart_url="https://macrocrypto.ai/price"
        )

        assert "Price Alert" in subject
        assert "BTC" in subject
        assert "85,000.00" in subject
        assert "<html>" in html_body
        assert "85,000.00" in html_body
        assert "BTC" in text_body
        assert "85,000.00" in text_body

    @patch('app.services.email_service.smtplib.SMTP')
    def test_email_disabled(self, mock_smtp, email_service, db_session, sample_alert):
        """Test email sending when disabled."""
        email = EmailQueue(
            id=uuid4(),
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text",
            status=EmailStatus.PENDING,
            attempts=0,
            max_attempts=3
        )
        db_session.add(email)
        db_session.commit()

        with patch('app.config.settings.EMAIL_ENABLED', False):
            result = email_service._send_email(email)

        assert result == False
        assert email.status == EmailStatus.PENDING  # Unchanged

    @patch('app.services.email_service.smtplib.SMTP')
    def test_email_missing_credentials(self, mock_smtp, email_service, db_session, sample_alert):
        """Test email sending when credentials are missing."""
        email = EmailQueue(
            id=uuid4(),
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text",
            status=EmailStatus.PENDING,
            attempts=0,
            max_attempts=3
        )
        db_session.add(email)
        db_session.commit()

        with patch('app.config.settings.EMAIL_ENABLED', True):
            with patch('app.config.settings.SMTP_USER', None):
                with patch('app.config.settings.SMTP_PASSWORD', None):
                    result = email_service._send_email(email)

        assert result == False
        assert email.status == EmailStatus.PENDING  # Unchanged

    @patch('app.services.email_service.smtplib.SMTP')
    def test_update_history_email_status(self, mock_smtp, email_service, db_session, sample_alert):
        """Test updating history with email status."""
        # Create history entry
        from app.models.alert import AlertHistory, HistoryEventType
        history = AlertHistory(
            alert_id=sample_alert.id,
            event_type=HistoryEventType.TRIGGERED,
            event_source="engine",
            triggered_price=85000.00,
            threshold_price=85000.00,
            alert_type="reaches",
            previous_status=AlertStatus.ACTIVE,
            new_status=AlertStatus.TRIGGERED,
            triggered_at=datetime.utcnow()
        )
        db_session.add(history)
        db_session.commit()

        email = EmailQueue(
            id=uuid4(),
            user_id=str(sample_alert.user_id),
            alert_id=str(sample_alert.id),
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test text",
            status=EmailStatus.PENDING,
            attempts=0,
            max_attempts=3
        )
        db_session.add(email)
        db_session.commit()

        # Update history
        email_service._update_history_email_status(
            alert_id=str(sample_alert.id),
            sent=True
        )

        # Check history was updated
        db_session.refresh(history)
        assert history.email_sent == True