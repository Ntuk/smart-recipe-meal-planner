import json
import os
import pika
import logging
import threading
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
        self.consumer_thread = None
        self._consuming = False
        
    def connect(self) -> bool:
        """
        Establish a connection to RabbitMQ and create a channel.
        
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        try:
            # Create a connection parameters object from the URL
            parameters = pika.URLParameters(self.connection_url)
            
            # Establish connection
            self.connection = pika.BlockingConnection(parameters)
            
            # Create a channel
            self.channel = self.connection.channel()
            
            logger.info("Successfully connected to RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def close(self):
        """Close the connection to RabbitMQ."""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = "topic", durable: bool = True):
        """
        Declare an exchange.
        
        Args:
            exchange_name: Name of the exchange
            exchange_type: Type of exchange (direct, fanout, topic, headers)
            durable: Whether the exchange should survive broker restarts
        """
        if not self.channel:
            if not self.connect():
                return
                
        self.channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=durable
        )
        logger.info(f"Exchange '{exchange_name}' declared")
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """
        Declare a queue.
        
        Args:
            queue_name: Name of the queue
            durable: Whether the queue should survive broker restarts
        """
        if not self.channel:
            if not self.connect():
                return
                
        self.channel.queue_declare(
            queue=queue_name,
            durable=durable
        )
        logger.info(f"Queue '{queue_name}' declared")
    
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """
        Bind a queue to an exchange with a routing key.
        
        Args:
            queue_name: Name of the queue
            exchange_name: Name of the exchange
            routing_key: Routing key for binding
        """
        if not self.channel:
            if not self.connect():
                return
                
        self.channel.queue_bind(
            queue=queue_name,
            exchange=exchange_name,
            routing_key=routing_key
        )
        logger.info(f"Queue '{queue_name}' bound to exchange '{exchange_name}' with routing key '{routing_key}'")
    
    def publish_message(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
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
            if not self.connect():
                return False
        
        try:
            # Convert message to JSON string
            message_body = json.dumps(message)
            
            # Publish the message
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Message published to exchange '{exchange_name}' with routing key '{routing_key}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            return False
    
    def start_consuming(self, queue_name: str, callback: Callable, auto_ack: bool = True):
        """
        Start consuming messages from a queue in a separate thread.
        
        Args:
            queue_name: Name of the queue to consume from
            callback: Function to call when a message is received
            auto_ack: Whether to automatically acknowledge messages
        """
        if not self.channel:
            if not self.connect():
                return
        
        # Set up the consumer
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=auto_ack
        )
        
        logger.info(f"Started consuming messages from queue '{queue_name}'")
        
        # Start consuming in a separate thread
        def consume_thread():
            try:
                self._consuming = True
                while self._consuming:
                    try:
                        self.connection.process_data_events(time_limit=1)  # Process events for 1 second
                    except Exception as e:
                        logger.error(f"Error processing events: {str(e)}")
                        if not self._consuming:
                            break
                        # Try to reconnect
                        if not self.connect():
                            break
            except Exception as e:
                logger.error(f"Error in consumer thread: {str(e)}")
            finally:
                self._consuming = False
        
        self.consumer_thread = threading.Thread(target=consume_thread, daemon=True)
        self.consumer_thread.start()
    
    def stop_consuming(self):
        """Stop consuming messages."""
        self._consuming = False
        if self.channel:
            try:
                self.channel.stop_consuming()
            except Exception as e:
                logger.error(f"Error stopping consumer: {str(e)}")
            logger.info("Stopped consuming messages")
        
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
    
    def setup_meal_planning_queues(self):
        """
        Set up the exchanges and queues needed for the meal planning service.
        """
        # Declare exchanges
        self.declare_exchange("ingredients", "topic")
        self.declare_exchange("meal_plans", "topic")
        
        # Declare queues
        self.declare_queue("detected_ingredients")
        self.declare_queue("meal_planning_requests")
        self.declare_queue("meal_plans_created")
        
        # Bind queues to exchanges
        self.bind_queue("detected_ingredients", "ingredients", "ingredient.detected")
        self.bind_queue("meal_planning_requests", "ingredients", "ingredient.planning")
        self.bind_queue("meal_plans_created", "meal_plans", "meal_plan.created") 