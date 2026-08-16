"""Email notification service for alert delivery"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models.alert import  PriceAlert
from app.models.alert import AlertHistory
from app.models.email_queue import EmailQueue, EmailStatus

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def queue_email(
        self,
        user_id: str,
        alert_id: str,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        priority: int = 5,
        scheduled_for: Optional[datetime] = None
    ) -> EmailQueue:
        """Queue an email for delivery."""
        email = EmailQueue(
            user_id=user_id,
            alert_id=alert_id,
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body or "",
            status=EmailStatus.PENDING,
            attempts=0,
            max_attempts=3,
            priority=priority,
            scheduled_for=scheduled_for or datetime.utcnow()
        )
        
        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)
        
        logger.debug(f"📧 Email queued: {email.id} to {to_email}")
        return email
    
    def process_email_queue(self, limit: int = 50) -> int:
        """Process pending emails in the queue."""
        pending_emails = self.db.query(EmailQueue).filter(
            EmailQueue.status.in_([EmailStatus.PENDING, EmailStatus.RETRY]),
            EmailQueue.scheduled_for <= datetime.utcnow()
        ).order_by(
            EmailQueue.priority
        ).limit(limit).all()
        
        processed = 0
        for email in pending_emails:
            success = self._send_email(email)
            if success:
                processed += 1
        
        logger.info(f"📧 Processed {processed} emails from queue")
        return processed
    
    def _send_email(self, email: EmailQueue) -> bool:
        """Send an email using SMTP."""
        if not settings.EMAIL_ENABLED:
            logger.warning("Email notifications disabled")
            return False
        
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email.subject
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email.to_email
            
            # Attach parts
            if email.text_body:
                part1 = MIMEText(email.text_body, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(email.html_body, 'html')
            msg.attach(part2)
            
            # Send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            # Update status
            email.status = EmailStatus.SENT
            email.sent_at = datetime.utcnow()
            self.db.commit()
            
            # Update alert history
            self._update_history_email_status(email.alert_id, sent=True)
            
            logger.info(f"📧 Email sent to {email.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            
            # Update status
            email.attempts += 1
            email.last_attempt_at = datetime.utcnow()
            email.error_message = str(e)
            
            if email.attempts >= email.max_attempts:
                email.status = EmailStatus.FAILED
            else:
                email.status = EmailStatus.RETRY
            
            self.db.commit()
            
            # Update alert history
            self._update_history_email_status(email.alert_id, sent=False, error=str(e))
            
            return False
    
    def _update_history_email_status(self, alert_id: str, sent: bool, error: Optional[str] = None):
        """Update email status in alert history."""
        if alert_id:
            history = self.db.query(AlertHistory).filter(
                AlertHistory.alert_id == alert_id
            ).order_by(
                AlertHistory.created_at.desc()
            ).first()
            
            if history:
                history.email_sent = sent
                if error:
                    history.email_error = error
                self.db.commit()
    
    def create_alert_email_body(
        self,
        alert: PriceAlert,
        current_price: float,
        chart_url: Optional[str] = None
    ) -> tuple:
        """Create HTML and text email body for price alert."""
        alert_type_labels = {
            "reaches": "reached",
            "crosses_above": "crossed above",
            "crosses_below": "crossed below",
        }
        
        label = alert_type_labels.get(
            alert.alert_type.value if alert.alert_type else "",
            "triggered"
        )
        
        subject = f"🚨 Price Alert: BTC {label} ${alert.threshold_price:,.2f}"
        
        text_body = f"""
        {subject}
        
        Alert Details:
        ---------------
        Asset: {alert.asset}
        Current Price: ${current_price:,.2f}
        Threshold: ${alert.threshold_price:,.2f}
        Direction: {alert.alert_type.value if alert.alert_type else 'N/A'}
        Triggered At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        View your alert: https://macrocrypto.ai/alerts/{alert.id}
        View price chart: {chart_url or 'https://macrocrypto.ai/price'}
        
        MacroCrypto AI
        """
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .alert-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .price {{ font-size: 32px; font-weight: bold; color: #667eea; }}
                .threshold {{ font-size: 24px; color: #764ba2; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
                .direction {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: bold; }}
                .direction-up {{ background: #d4edda; color: #155724; }}
                .direction-down {{ background: #f8d7da; color: #721c24; }}
                .direction-reached {{ background: #fff3cd; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Price Alert Triggered</h1>
                    <p>{alert.asset}</p>
                </div>
                <div class="content">
                    <h2>Alert Details</h2>
                    <div class="alert-details">
                        <p><strong>Current Price:</strong> <span class="price">${current_price:,.2f}</span></p>
                        <p><strong>Threshold:</strong> <span class="threshold">${alert.threshold_price:,.2f}</span></p>
                        <p><strong>Direction:</strong> 
                            <span class="direction direction-{alert.alert_type.value if alert.alert_type else ''}">
                                {alert.alert_type.value if alert.alert_type else 'N/A'}
                            </span>
                        </p>
                        <p><strong>Triggered At:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                    <a href="{chart_url or 'https://macrocrypto.ai/price'}" class="button">View Price Chart</a>
                    <a href="https://macrocrypto.ai/alerts/{alert.id}" class="button" style="background: #764ba2;">View Alert</a>
                </div>
                <div class="footer">
                    <p>MacroCrypto AI - Your AI-powered crypto intelligence platform</p>
                    <p>To unsubscribe from alerts, visit your <a href="https://macrocrypto.ai/settings">settings</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_body, text_body