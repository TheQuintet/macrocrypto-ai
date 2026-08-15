"""RabbitMQ producer for alert-service"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional
import pika

from app.config import settings
from app.schemas.events import AlertTriggeredEvent

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    """
    RabbitMQ producer for publishing events from Alert Service.
    
    Produces:
    - AlertTriggered events to alert_exchange
    """
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_connected = False
        
        # Exchange name
        self.EXCHANGE_ALERTS = "alert_exchange"
    
    def connect(self) -> bool:
        """Establish connection to RabbitMQ."""
        try:
            params = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ_USER,
                    settings.RABBITMQ_PASSWORD
                ),
                virtual_host=settings.RABBITMQ_VHOST
            )
            
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_ALERTS,
                exchange_type="topic",
                durable=True
            )
            
            self.is_connected = True
            logger.info("✅ RabbitMQ producer connected")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ producer: {e}")
            return False
    
    def publish_alert_triggered(
        self,
        alert_id: str,
        user_id: str,
        alert_type: str,
        condition: str,
        triggered_value: dict,
        config: dict
    ) -> bool:
        """
        Publish AlertTriggered event.
        
        Args:
            alert_id: ID of the triggered alert
            user_id: ID of the user
            alert_type: Type of alert (price, prediction, etc.)
            condition: The condition that was met
            triggered_value: The value that triggered the alert
            config: The alert configuration
        
        Returns:
            bool: True if published successfully
        """
        if not self.is_connected or not self.channel:
            logger.error("Not connected to RabbitMQ")
            return False
        
        try:
            event = AlertTriggeredEvent(
                event_id=str(uuid.uuid4()),
                event_type="alert_triggered",
                timestamp=datetime.utcnow(),
                source="alert_service",
                data={
                    "alert_id": alert_id,
                    "user_id": user_id,
                    "alert_type": alert_type,
                    "condition": condition,
                    "triggered_value": triggered_value,
                    "config": config,
                    "triggered_at": datetime.utcnow().isoformat()
                }
            )
            
            message = json.dumps(event.model_dump(), default=str)
            
            self.channel.basic_publish(
                exchange=self.EXCHANGE_ALERTS,
                routing_key="alert.triggered",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type="application/json"
                )
            )
            
            logger.info(f"📤 Published AlertTriggered for alert {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish AlertTriggered: {e}")
            return False
    
    def close(self):
        """Close RabbitMQ connection."""
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False
            logger.info("✅ RabbitMQ producer connection closed")