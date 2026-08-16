"""Email notification service for prediction alerts"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.services.email_service import EmailService
from app.models.prediction_alert import PredictionChangeAlert, PredictionChangeHistory

logger = logging.getLogger(__name__)


class PredictionEmailService:
    """Service for sending prediction alert emails"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService(db)

    def queue_prediction_alert_email(
        self,
        alert: PredictionChangeAlert,
        previous_prediction: float,
        new_prediction: float,
        change_percent: float,
        recommendation: str,
        horizon: str,
        user_email: str
    ):
        """Queue a prediction alert email for delivery."""
        subject, html_body, text_body = self._create_email_content(
            alert=alert,
            previous_prediction=previous_prediction,
            new_prediction=new_prediction,
            change_percent=change_percent,
            recommendation=recommendation,
            horizon=horizon
        )

        self.email_service.queue_email(
            user_id=str(alert.user_id),
            alert_id=str(alert.id),
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            priority=5
        )

        logger.info(f"📧 Prediction alert email queued for alert {alert.id}")

    def _create_email_content(
        self,
        alert: PredictionChangeAlert,
        previous_prediction: float,
        new_prediction: float,
        change_percent: float,
        recommendation: str,
        horizon: str
    ) -> tuple:
        """Create email content for prediction alert."""
        direction_emoji = "📈" if change_percent > 0 else "📉"
        direction_text = "Up" if change_percent > 0 else "Down"

        subject = f"{direction_emoji} Prediction Change Alert: {direction_text} {abs(change_percent):.1f}%"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .price-change {{ font-size: 28px; font-weight: bold; color: {'#28a745' if change_percent > 0 else '#dc3545'}; }}
                .recommendation {{ background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Prediction Change Alert</h1>
                    <p>{alert.asset} - {horizon} Horizon</p>
                </div>
                <div class="content">
                    <h2>Prediction Update</h2>
                    <div class="details">
                        <p><strong>Previous Prediction:</strong> ${previous_prediction:,.2f}</p>
                        <p><strong>New Prediction:</strong> ${new_prediction:,.2f}</p>
                        <p><strong>Change:</strong> <span class="price-change">{change_percent:+.2f}%</span></p>
                        <p><strong>Horizon:</strong> {horizon}</p>
                        <p><strong>Threshold:</strong> {alert.threshold_percent}%</p>
                        <p><strong>Triggered At:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>

                    <div class="recommendation">
                        <strong>💡 Recommendation</strong>
                        <p>{recommendation}</p>
                    </div>

                    <a href="https://macrocrypto.ai/alerts/prediction/{alert.id}" class="button">View Alert Details</a>
                    <a href="https://macrocrypto.ai/predictions" class="button" style="background: #764ba2;">View Predictions</a>
                </div>
                <div class="footer">
                    <p>MacroCrypto AI - Your AI-powered crypto intelligence platform</p>
                    <p>To unsubscribe from alerts, visit your <a href="https://macrocrypto.ai/settings">settings</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        {subject}

        Prediction Update:
        -------------------
        Previous Prediction: ${previous_prediction:,.2f}
        New Prediction: ${new_prediction:,.2f}
        Change: {change_percent:+.2f}%
        Horizon: {horizon}
        Threshold: {alert.threshold_percent}%
        Triggered At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

        Recommendation:
        {recommendation}

        View alert details: https://macrocrypto.ai/alerts/prediction/{alert.id}
        View predictions: https://macrocrypto.ai/predictions

        MacroCrypto AI
        """

        return subject, html_body, text_body