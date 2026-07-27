"""RabbitMQ event producer"""

import json
import logging
from typing import Dict, Any
import pika
from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQProducer:
    """RabbitMQ producer for publishing events"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.is_connected = False
        
        # Exchange names
        self.EXCHANGE_DATA = "data_exchange"
        
        # ✅ Queue names (permanent)
        self.QUEUE_PRICE_UPDATES = "price_updates"
        self.QUEUE_ECONOMIC_UPDATES = "economic_updates"
    
    async def connect(self):
        """Establish connection to RabbitMQ"""
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
            
            # ✅ Declare exchange (durable)
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_DATA,
                exchange_type="topic",
                durable=True
            )
            
            # ✅ Create permanent queues
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
            
            # ✅ Bind queues to exchange
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
            logger.info("✅ RabbitMQ connected with permanent queues")
            logger.info(f"   📋 price_updates queue created")
            logger.info(f"   📋 economic_updates queue created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            return False
    
    def publish_price_update(self, price_data: Dict[str, Any]):
        """
        Publish price update event to permanent queue
        """
        if not self.is_connected or not self.channel:
            logger.error("Not connected to RabbitMQ")
            return
        
        try:
            message = json.dumps({
                "type": "price_update",
                "data": price_data,
                "timestamp": price_data.get("timestamp")
            })
            
            self.channel.basic_publish(
                exchange=self.EXCHANGE_DATA,
                routing_key="data.price.update",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # ✅ Persistent message
                    content_type="application/json"
                )
            )
            
            logger.debug(f"📤 Published price update: {price_data.get('symbol', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error publishing price update: {e}")
    
    def publish_economic_update(self, economic_data: Dict[str, Any]):
        """
        Publish economic indicator update to permanent queue
        """
        if not self.is_connected or not self.channel:
            logger.error("Not connected to RabbitMQ")
            return
        
        try:
            message = json.dumps({
                "type": "economic_update",
                "data": economic_data,
                "timestamp": economic_data.get("timestamp")
            })
            
            self.channel.basic_publish(
                exchange=self.EXCHANGE_DATA,
                routing_key="data.economic.update",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # ✅ Persistent message
                    content_type="application/json"
                )
            )
            
            logger.debug("📤 Published economic update")
            
        except Exception as e:
            logger.error(f"Error publishing economic update: {e}")
    
    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False
            logger.info("Closed RabbitMQ connection")