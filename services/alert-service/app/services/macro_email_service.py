"""Email notification service for macro events"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.services.email_service import EmailService
from app.models.macro_alert import MacroEventAlert, MacroEventCache

logger = logging.getLogger(__name__)


class MacroEmailService:
    """Service for sending macro event alert emails"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService(db)

    def queue_macro_alert_email(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str,
        user_email: str
    ):
        """Queue a macro alert email for delivery."""
        subject, html_body, text_body = self._create_email_content(
            alert=alert,
            event=event,
            timing=timing
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

        logger.info(f"📧 Macro alert email queued for alert {alert.id}")

    def _create_email_content(
        self,
        alert: MacroEventAlert,
        event: MacroEventCache,
        timing: str
    ) -> tuple:
        """Create email content for macro alert."""
        timing_labels = {
            "1d": "1 day before",
            "12h": "12 hours before",
            "1h": "1 hour before"
        }

        impact_emoji = {
            "high": "🔴 HIGH",
            "medium": "🟡 MEDIUM",
            "low": "🟢 LOW"
        }

        event_type_labels = {
            "fed": "Federal Reserve Meeting",
            "cpi": "CPI Release",
            "gdp": "GDP Release",
            "employment": "Employment Report",
            "other": "Economic Event"
        }

        event_label = event_type_labels.get(
            event.event_type.value if event.event_type else "other",
            event.event_name
        )

        subject = f"📅 Macro Event Alert: {event_label} - {impact_emoji.get(event.impact.value if event.impact else 'low', '')}"

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
                .impact-high {{ color: #dc3545; font-weight: bold; }}
                .impact-medium {{ color: #ffc107; font-weight: bold; }}
                .impact-low {{ color: #28a745; font-weight: bold; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Macro Event Alert</h1>
                    <p>{event_label}</p>
                </div>
                <div class="content">
                    <h2>Event Details</h2>
                    <div class="details">
                        <p><strong>Event:</strong> {event.event_name}</p>
                        <p><strong>Date & Time:</strong> {event.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
                        <p><strong>Timing:</strong> {timing_labels.get(timing, timing)}</p>
                        <p><strong>Impact:</strong> <span class="impact-{event.impact.value if event.impact else 'low'}">{impact_emoji.get(event.impact.value if event.impact else 'low', '')}</span></p>
                        <p><strong>Description:</strong> {event.description or 'Major economic event that may affect BTC'}</p>
                    </div>

                    <h3>📊 What This Means for BTC</h3>
                    <div class="details">
                        {self._get_btc_impact_description(event)}
                    </div>

                    <a href="https://macrocrypto.ai/economic-calendar" class="button">View Economic Calendar</a>
                    <a href="https://macrocrypto.ai/alerts/macro/{alert.id}" class="button" style="background: #764ba2;">Manage Alerts</a>
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

        Event Details:
        ----------------
        Event: {event.event_name}
        Date & Time: {event.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}
        Timing: {timing_labels.get(timing, timing)}
        Impact: {impact_emoji.get(event.impact.value if event.impact else 'low', '')}
        Description: {event.description or 'Major economic event that may affect BTC'}

        What This Means for BTC:
        {self._get_btc_impact_description(event)}

        View Economic Calendar: https://macrocrypto.ai/economic-calendar
        Manage Alerts: https://macrocrypto.ai/alerts/macro/{alert.id}

        MacroCrypto AI
        """

        return subject, html_body, text_body

    def _get_btc_impact_description(self, event: MacroEventCache) -> str:
        """Get description of what the event means for BTC."""
        event_type = event.event_type.value if event.event_type else "other"

        descriptions = {
            "fed": """
            <p>The Federal Reserve meeting can significantly impact BTC prices. If the Fed signals 
            <strong>rate cuts</strong>, it's typically <strong>bullish</strong> for BTC as it weakens the USD. 
            If the Fed signals <strong>rate hikes</strong>, it's typically <strong>bearish</strong> for BTC.</p>
            <p><strong>Watch for:</strong> Interest rate decisions, Powell's press conference, and forward guidance.</p>
            """,
            "cpi": """
            <p>CPI (Consumer Price Index) measures inflation. <strong>Higher than expected inflation</strong> 
            may lead to Fed rate hikes, which is typically <strong>bearish</strong> for BTC. 
            <strong>Lower than expected inflation</strong> may lead to rate cuts, which is typically 
            <strong>bullish</strong> for BTC.</p>
            <p><strong>Watch for:</strong> Headline CPI, Core CPI, and month-over-month changes.</p>
            """,
            "gdp": """
            <p>GDP (Gross Domestic Product) measures economic growth. <strong>Strong GDP growth</strong> 
            suggests a healthy economy but may lead to inflation concerns. <strong>Weak GDP growth</strong> 
            may signal recession and could lead to Fed rate cuts, which is typically <strong>bullish</strong> 
            for BTC.</p>
            <p><strong>Watch for:</strong> GDP growth rate, consumption data, and investment figures.</p>
            """,
            "employment": """
            <p>Employment reports (NFP) measure job growth. <strong>Strong job growth</strong> may lead to 
            Fed tightening, which is typically <strong>bearish</strong> for BTC. 
            <strong>Weak job growth</strong> may lead to Fed rate cuts, which is typically 
            <strong>bullish</strong> for BTC.</p>
            <p><strong>Watch for:</strong> Non-Farm Payrolls, unemployment rate, and wage growth.</p>
            """
        }

        return descriptions.get(event_type, """
        <p>This economic event may impact BTC prices. Monitor for market reactions and volatility.</p>
        """)