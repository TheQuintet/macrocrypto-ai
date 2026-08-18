"""Integration tests for prediction email service"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime

from app.services.prediction_email_service import PredictionEmailService
from app.services.email_service import EmailService
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection
)
from app.models.email_queue import EmailQueue, EmailStatus


class TestPredictionEmailService:
    """Test cases for PredictionEmailService."""

    @pytest.fixture
    def prediction_email_service(self, db_session):
        """Create prediction email service instance."""
        return PredictionEmailService(db_session)

    @pytest.fixture
    def sample_alert(self, db_session):
        """Create a sample prediction alert for testing."""
        alert = PredictionChangeAlert(
            id=uuid4(),
            user_id=uuid4(),
            threshold_percent=2.0,
            horizon=PredictionHorizon.HOUR_24,
            direction=PredictionDirection.BOTH,
            asset="BTC/USD",
            status=PredictionAlertStatus.ACTIVE,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    def test_queue_prediction_alert_email(
        self, prediction_email_service, db_session, sample_alert
    ):
        """Test queuing a prediction alert email."""
        user_email = "test@example.com"

        prediction_email_service.queue_prediction_alert_email(
            alert=sample_alert,
            previous_prediction=82000.00,
            new_prediction=85000.00,
            change_percent=3.66,
            recommendation="Consider adjusting position",
            horizon="24h",
            user_email=user_email
        )

        # Check email was queued
        email = db_session.query(EmailQueue).filter(
            EmailQueue.alert_id == str(sample_alert.id)
        ).first()

        assert email is not None
        assert email.to_email == user_email
        assert "Prediction Change Alert" in email.subject
        assert "Up 3.7%" in email.subject or "Up 3.66%" in email.subject
        assert "$82,000" in email.html_body or "82000" in email.html_body
        assert "$85,000" in email.html_body or "85000" in email.html_body
        assert "3.66" in email.html_body or "3.7" in email.html_body
        assert email.status == EmailStatus.PENDING

    def test_email_content_creation(self, prediction_email_service, sample_alert):
        """Test email content creation for prediction alert."""
        subject, html_body, text_body = prediction_email_service._create_email_content(
            alert=sample_alert,
            previous_prediction=82000.00,
            new_prediction=85000.00,
            change_percent=3.66,
            recommendation="Consider adjusting position",
            horizon="24h"
        )

        assert "Prediction Change Alert" in subject
        assert "BTC/USD" in subject
        assert "Up 3.7%" in subject or "Up 3.66%" in subject

        assert "<html>" in html_body
        assert "$82,000" in html_body or "82000" in html_body
        assert "$85,000" in html_body or "85000" in html_body
        assert "3.66" in html_body or "3.7" in html_body
        assert "Recommendation" in html_body
        assert "Consider adjusting position" in html_body

        assert "BTC/USD" in text_body
        assert "$82,000" in text_body or "82000" in text_body
        assert "$85,000" in text_body or "85000" in text_body
        assert "Up 3.7%" in text_body or "Up 3.66%" in text_body
        assert "Recommendation" in text_body
        assert "Consider adjusting position" in text_body

    @patch('app.services.email_service.smtplib.SMTP')
    def test_email_retry_logic(
        self, mock_smtp, prediction_email_service, db_session, sample_alert
    ):
        """Test email retry logic on failure."""
        # Queue email
        user_email = "test@example.com"
        prediction_email_service.queue_prediction_alert_email(
            alert=sample_alert,
            previous_prediction=82000.00,
            new_prediction=85000.00,
            change_percent=3.66,
            recommendation="Consider adjusting position",
            horizon="24h",
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

    @patch('app.services.email_service.smtplib.SMTP')
    def test_email_fails_after_max_attempts(
        self, mock_smtp, prediction_email_service, db_session, sample_alert
    ):
        """Test email fails after max attempts."""
        # Queue email
        user_email = "test@example.com"
        prediction_email_service.queue_prediction_alert_email(
            alert=sample_alert,
            previous_prediction=82000.00,
            new_prediction=85000.00,
            change_percent=3.66,
            recommendation="Consider adjusting position",
            horizon="24h",
            user_email=user_email
        )

        email = db_session.query(EmailQueue).filter(
            EmailQueue.alert_id == str(sample_alert.id)
        ).first()

        # Set attempts to max
        email.attempts = 3
        db_session.commit()

        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")

        # Process email
        email_service = EmailService(db_session)
        with patch('app.config.settings.EMAIL_ENABLED', True):
            with patch('app.config.settings.SMTP_USER', 'test@example.com'):
                with patch('app.config.settings.SMTP_PASSWORD', 'password'):
                    result = email_service._send_email(email)

        assert result is False
        assert email.status == EmailStatus.FAILED