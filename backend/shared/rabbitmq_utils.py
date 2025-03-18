import logging
import threading
import time
from typing import Callable, Optional, Dict
import pika
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(
        self,
        url: str,
        exchange: str,
        queue: str,
        routing_key: str,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        self.url = url
        self.exchange = exchange
        self.queue = queue
        self.routing_key = routing_key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._consumer_threads: Dict[str, threading.Thread] = {}
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _connect_sync(self) -> bool:
        """Synchronous connection method to be run in a thread pool"""
        for attempt in range(self.max_retries):
            try:
                parameters = pika.URLParameters(self.url)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                logger.info("Successfully connected to RabbitMQ")
                return True
            except Exception as e:
                logger.warning(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Failed to connect to RabbitMQ after all retries")
                    return False

    async def connect(self) -> bool:
        """Asynchronous connection method that runs the blocking connection in a thread pool"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._connect_sync)

    async def setup_queues(self):
        """Declare exchanges and queues"""
        try:
            with self._lock:
                if not self.channel:
                    if not await self.connect():
                        raise Exception("Failed to connect to RabbitMQ")

                # Declare exchange
                self.channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type='topic',
                    durable=True
                )

                # Declare queue
                self.channel.queue_declare(
                    queue=self.queue,
                    durable=True
                )

                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange=self.exchange,
                    queue=self.queue,
                    routing_key=self.routing_key
                )

                logger.info(f"Successfully set up RabbitMQ queues for {self.queue}")
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ queues: {str(e)}")
            raise

    async def publish_message(self, message: dict) -> bool:
        """Publish a message to RabbitMQ"""
        try:
            with self._lock:
                if not self.channel:
                    if not await self.connect():
                        raise Exception("Failed to connect to RabbitMQ")

                self.channel.basic_publish(
                    exchange=self.exchange,
                    routing_key=self.routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # make message persistent
                        content_type='application/json'
                    )
                )
                logger.debug(f"Published message to {self.exchange}:{self.routing_key}")
                return True
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            return False

    async def start_consuming(self, callback: Callable) -> bool:
        """Start consuming messages in a separate thread"""
        try:
            with self._lock:
                if not self.channel:
                    if not await self.connect():
                        raise Exception("Failed to connect to RabbitMQ")

                # Create a new thread for consuming
                thread = threading.Thread(
                    target=self._consume_messages,
                    args=(callback,),
                    daemon=True
                )
                self._consumer_threads[self.queue] = thread
                thread.start()
                logger.info(f"Started consuming messages from {self.queue}")
                return True
        except Exception as e:
            logger.error(f"Failed to start consuming messages: {str(e)}")
            return False

    async def _consume_messages(self, callback: Callable):
        """Internal method to consume messages"""
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    if not self.channel:
                        if not await self.connect():
                            raise Exception("Failed to connect to RabbitMQ")

                    self.channel.basic_qos(prefetch_count=1)
                    self.channel.basic_consume(
                        queue=self.queue,
                        on_message_callback=callback,
                        auto_ack=True
                    )
                    
                    # Start consuming in a non-blocking way
                    while not self._stop_event.is_set():
                        try:
                            self.channel.connection.process_data_events(time_limit=1)
                        except Exception as e:
                            logger.error(f"Error processing data events: {str(e)}")
                            break
                        
            except Exception as e:
                logger.error(f"Error in consumer thread: {str(e)}")
                if not self._stop_event.is_set():
                    time.sleep(self.retry_delay)

    async def stop_consuming(self):
        """Stop all consumer threads"""
        self._stop_event.set()
        for queue, thread in self._consumer_threads.items():
            try:
                thread.join(timeout=5)
                logger.info(f"Stopped consuming messages from {queue}")
            except Exception as e:
                logger.error(f"Error stopping consumer for {queue}: {str(e)}")
        self._consumer_threads.clear()
        self._stop_event.clear()

    async def close(self):
        """Close RabbitMQ connection"""
        try:
            await self.stop_consuming()
            with self._lock:
                if self.channel:
                    self.channel.close()
                if self.connection:
                    self.connection.close()
                self.channel = None
                self.connection = None
                logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}") 