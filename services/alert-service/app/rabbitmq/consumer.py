"""RabbitMQ consumer for alert-service"""

import json
import logging
from typing import Optional, Callable
import pika
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """
    RabbitMQ consumer for receiving events from Data Service.
    
    Consumes:
    - PriceUpdated events from price_updates queue
    - IndicatorUpdated events from economic_updates queue
    """
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_connected = False
        
        # Exchange and queue names (match Data Service)
        self.EXCHANGE_DATA = "data_exchange"
        self.QUEUE_PRICE_UPDATES = "price_updates"
        self.QUEUE_ECONOMIC_UPDATES = "economic_updates"
        
        # Callbacks
        self.price_callback: Optional[Callable] = None
        self.indicator_callback: Optional[Callable] = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
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
            
            # Declare exchange (same as Data Service)
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_DATA,
                exchange_type="topic",
                durable=True
            )
            
            # Declare queues (same as Data Service)
            self.channel.queue_declare(
                queue=self.QUEUE_PRICE_UPDATES,
                durable=True,
                auto_delete=False
            )
            self.channel.queue_declare(
                queue=self.QUEUE_ECONOMIC_UPDATES,
                durable=True,
                auto_delete=False
            )
            
            # Bind queues to exchange
            self.channel.queue_bind(
                exchange=self.EXCHANGE_DATA,
                queue=self.QUEUE_PRICE_UPDATES,
                routing_key="data.price.update"
            )
            self.channel.queue_bind(
                exchange=self.EXCHANGE_DATA,
                queue=self.QUEUE_ECONOMIC_UPDATES,
                routing_key="data.economic.update"
            )
            
            self.is_connected = True
            logger.info("✅ RabbitMQ consumer connected")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            return False
    
    def start_consuming(self):
        """Start consuming messages from queues."""
        if not self.is_connected or not self.channel:
            logger.error("Not connected to RabbitMQ")
            return
        
        # Set up consumers
        if self.price_callback:
            self.channel.basic_consume(
                queue=self.QUEUE_PRICE_UPDATES,
                on_message_callback=self._price_callback_wrapper,
                auto_ack=False
            )
            logger.info(f"📥 Consuming from {self.QUEUE_PRICE_UPDATES}")
        
        if self.indicator_callback:
            self.channel.basic_consume(
                queue=self.QUEUE_ECONOMIC_UPDATES,
                on_message_callback=self._indicator_callback_wrapper,
                auto_ack=False
            )
            logger.info(f"📥 Consuming from {self.QUEUE_ECONOMIC_UPDATES}")
        
        # Start consuming
        self.channel.start_consuming()
    
    def _price_callback_wrapper(self, ch, method, properties, body):
        """Wrapper for price callback with ack handling."""
        try:
            message = json.loads(body)
            logger.debug(f"Received price update: {message.get('data', {}).get('symbol')}")
            
            if self.price_callback:
                self.price_callback(message)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing price message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _indicator_callback_wrapper(self, ch, method, properties, body):
        """Wrapper for indicator callback with ack handling."""
        try:
            message = json.loads(body)
            logger.debug(f"Received indicator update: {message.get('data', {}).get('indicator_type')}")
            
            if self.indicator_callback:
                self.indicator_callback(message)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing indicator message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def close(self):
        """Close RabbitMQ connection."""
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False
            logger.info("✅ RabbitMQ consumer connection closed")