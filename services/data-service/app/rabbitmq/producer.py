"""RabbitMQ event producer"""

import json
import logging
from typing import Dict, Any
import pika
from pika.adapters.asyncio_connection import AsyncioConnection

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
    
    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            # Create connection parameters
            params = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ_USER,
                    settings.RABBITMQ_PASSWORD
                ),
                virtual_host=settings.RABBITMQ_VHOST
            )
            
            # We need to use the synchronous connection for now
            # Async connection would be better but requires more setup
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_DATA,
                exchange_type="topic",
                durable=True
            )
            
            self.is_connected = True
            logger.info("Connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def publish_price_update(self, price_data: Dict[str, Any]):
        """
        Publish price update event
        
        Args:
            price_data: Price data dictionary
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
                    delivery_mode=2,  # Persistent
                    content_type="application/json"
                )
            )
            
            logger.info(f"Published price update: {price_data.get('symbol', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error publishing price update: {e}")
    
    def publish_economic_update(self, economic_data: Dict[str, Any]):
        """
        Publish economic indicator update
        
        Args:
            economic_data: Economic data dictionary
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
                    delivery_mode=2,
                    content_type="application/json"
                )
            )
            
            logger.info("Published economic update")
            
        except Exception as e:
            logger.error(f"Error publishing economic update: {e}")
    
    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False
            logger.info("Closed RabbitMQ connection")