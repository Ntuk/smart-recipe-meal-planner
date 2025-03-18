import json
import os
import aio_pika
import logging
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RabbitMQClient:
    """
    A utility class for interacting with RabbitMQ message broker.
    Handles connection, channel creation, publishing, and consuming messages.
    """
    
    def __init__(self, connection_url: Optional[str] = None):
        """
        Initialize the RabbitMQ client with connection parameters.
        
        Args:
            connection_url: The RabbitMQ connection URL. If not provided, it will be read from environment variable.
        """
        self.connection_url = connection_url or os.getenv("RABBITMQ_URI", "amqp://admin:password@rabbitmq:5672/")
        self.connection = None
        self.channel = None
        
    async def connect(self) -> bool:
        """
        Establish a connection to RabbitMQ and create a channel.
        
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        try:
            # Create a connection parameters object from the URL
            logger.info(f"Connecting to RabbitMQ with URL: {self.connection_url}")
            
            # Establish connection
            logger.info("Attempting to establish connection...")
            self.connection = await aio_pika.connect_robust(self.connection_url)
            
            # Create a channel
            logger.info("Creating channel...")
            self.channel = await self.connection.channel()
            
            logger.info("Successfully connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            # Print detailed exception information for debugging
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            return False
    
    async def close(self):
        """Close the connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
    
    def is_connected(self) -> bool:
        """Check if the client is connected to RabbitMQ."""
        return self.connection is not None and not self.connection.is_closed and self.channel is not None and not self.channel.is_closed
    
    async def declare_exchange(self, exchange_name: str, exchange_type: str = "topic", durable: bool = True):
        """
        Declare an exchange.
        
        Args:
            exchange_name: Name of the exchange
            exchange_type: Type of exchange (direct, fanout, topic, headers)
            durable: Whether the exchange should survive broker restarts
        """
        if not self.channel:
            if not await self.connect():
                return
                
        await self.channel.declare_exchange(
            name=exchange_name,
            type=exchange_type,
            durable=durable
        )
        logger.info(f"Exchange '{exchange_name}' declared")
    
    async def declare_queue(self, queue_name: str, durable: bool = True):
        """
        Declare a queue.
        
        Args:
            queue_name: Name of the queue
            durable: Whether the queue should survive broker restarts
        """
        if not self.channel:
            if not await self.connect():
                return
                
        await self.channel.declare_queue(
            name=queue_name,
            durable=durable
        )
        logger.info(f"Queue '{queue_name}' declared")
    
    async def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """
        Bind a queue to an exchange with a routing key.
        
        Args:
            queue_name: Name of the queue
            exchange_name: Name of the exchange
            routing_key: Routing key for binding
        """
        if not self.channel:
            if not await self.connect():
                return
                
        queue = await self.channel.get_queue(queue_name)
        exchange = await self.channel.get_exchange(exchange_name)
        await queue.bind(exchange, routing_key)
        logger.info(f"Queue '{queue_name}' bound to exchange '{exchange_name}' with routing key '{routing_key}'")
    
    async def publish_message(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
        """
        Publish a message to an exchange with a routing key.
        
        Args:
            exchange_name: Name of the exchange
            routing_key: Routing key for message
            message: Dictionary containing the message data
        
        Returns:
            bool: True if message was published successfully, False otherwise
        """
        if not self.channel:
            if not await self.connect():
                return False
        
        try:
            # Convert message to JSON string
            message_body = json.dumps(message).encode()
            logger.info(f"Publishing message to exchange '{exchange_name}' with routing key '{routing_key}'")
            logger.debug(f"Message body: {message_body[:200]}...")
            
            # Get the exchange
            exchange = await self.channel.get_exchange(exchange_name)
            
            # Publish the message
            await exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type='application/json'
                ),
                routing_key=routing_key
            )
            logger.info(f"Message published to exchange '{exchange_name}' with routing key '{routing_key}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            return False
    
    async def setup_ingredient_scanner_queues(self):
        """
        Set up the exchanges and queues needed for the ingredient scanner service.
        """
        # Declare exchanges
        await self.declare_exchange("ingredients", "topic")
        
        # Declare queues
        await self.declare_queue("detected_ingredients")
        await self.declare_queue("meal_planning_requests")
        
        # Bind queues to exchanges
        await self.bind_queue("detected_ingredients", "ingredients", "ingredient.detected")
        await self.bind_queue("meal_planning_requests", "ingredients", "ingredient.planning")
        
    async def publish_scan_result(self, scan_result: Dict[str, Any]) -> bool:
        """
        Publish a scan result to the ingredients exchange.
        
        Args:
            scan_result: Dictionary containing the scan result data
            
        Returns:
            bool: True if message was published successfully, False otherwise
        """
        logger.info(f"Attempting to publish scan result: {scan_result}")
        try:
            if not self.is_connected():
                logger.warning("Not connected to RabbitMQ, attempting to connect...")
                if not await self.connect():
                    logger.error("Failed to connect to RabbitMQ")
                    return False
            
            result = await self.publish_message(
                exchange_name="ingredients",
                routing_key="ingredient.detected",
                message=scan_result
            )
            logger.info(f"Publish result: {result}")
            return result
        except Exception as e:
            logger.error(f"Exception in publish_scan_result: {str(e)}")
            import traceback
            logger.error(f"Detailed error: {traceback.format_exc()}")
            return False 