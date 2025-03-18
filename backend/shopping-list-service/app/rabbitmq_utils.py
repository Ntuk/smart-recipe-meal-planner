import json
import os
import aio_pika
import logging
import asyncio
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
        self.should_reconnect = True
        self.reconnect_delay = 5  # seconds
        self._consuming = False
        self._consumer_tag = None
        self._current_callback = None
        self._current_queue = None
        
    async def connect(self) -> bool:
        """
        Establish a connection to RabbitMQ and create a channel.
        
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        while self.should_reconnect:
            try:
                # Create a connection parameters object from the URL
                self.connection = await aio_pika.connect_robust(
                    self.connection_url,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                
                # Create a channel
                self.channel = await self.connection.channel()
                
                logger.info("Successfully connected to RabbitMQ")
                
                # If we were consuming before, resume consumption
                if self._consuming and self._current_queue and self._current_callback:
                    await self.start_consuming(self._current_queue, self._current_callback)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
                if self.should_reconnect:
                    logger.info(f"Retrying connection in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    return False
        
        return False
    
    async def close(self):
        """Close the connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
    
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
            exchange_name,
            type=aio_pika.ExchangeType(exchange_type),
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
            queue_name,
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
                
        # Get the queue and exchange
        queue = await self.channel.get_queue(queue_name)
        exchange = await self.channel.get_exchange(exchange_name)
        
        # Bind the queue to the exchange
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
            return False
    
    async def start_consuming(self, queue_name: str, callback: Callable, auto_ack: bool = True):
        """
        Start consuming messages from a queue.
        
        Args:
            queue_name: Name of the queue to consume from
            callback: Function to call when a message is received
            auto_ack: Whether to automatically acknowledge messages
        """
        if not self.channel:
            if not await self.connect():
                return
        
        # Store current consumer settings
        self._current_queue = queue_name
        self._current_callback = callback
        self._consuming = True
        
        # Set up the consumer
        try:
            # Cancel any existing consumer
            if self._consumer_tag:
                try:
                    queue = await self.channel.get_queue(self._current_queue)
                    await queue.cancel(self._consumer_tag)
                except Exception:
                    pass
            
            # Get the queue
            queue = await self.channel.get_queue(queue_name)
            
            # Start consuming
            async def process_message(message):
                async with message.process():
                    body = message.body.decode()
                    await callback(None, None, None, body)
            
            self._consumer_tag = await queue.consume(process_message)
            
            logger.info(f"Started consuming messages from queue '{queue_name}'")
            
        except Exception as e:
            logger.error(f"Failed to start consuming: {str(e)}")
            self._consuming = False
    
    async def stop_consuming(self):
        """Stop consuming messages."""
        self._consuming = False
        if self.channel and self._consumer_tag:
            try:
                queue = await self.channel.get_queue(self._current_queue)
                await queue.cancel(self._consumer_tag)
                self._consumer_tag = None
            except Exception as e:
                logger.error(f"Error stopping consumer: {str(e)}")
    
    async def setup_shopping_list_queues(self):
        """Set up the necessary exchanges and queues for the shopping list service."""
        # Declare exchanges
        await self.declare_exchange("shopping_lists", "topic")
        await self.declare_exchange("meal_plans", "topic")
        
        # Declare queues
        await self.declare_queue("shopping_lists_created")
        await self.declare_queue("shopping_lists_updated")
        await self.declare_queue("shopping_lists_deleted")
        await self.declare_queue("meal_plans_created")
        
        # Bind queues to exchanges
        await self.bind_queue("shopping_lists_created", "shopping_lists", "created")
        await self.bind_queue("shopping_lists_updated", "shopping_lists", "updated")
        await self.bind_queue("shopping_lists_deleted", "shopping_lists", "deleted")
        await self.bind_queue("meal_plans_created", "meal_plans", "created")
        
        logger.info("Shopping list queues setup completed") 