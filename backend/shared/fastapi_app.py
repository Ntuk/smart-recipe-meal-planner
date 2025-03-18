from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .mongodb_utils import MongoDBClient
from .rabbitmq_utils import RabbitMQClient

logger = logging.getLogger(__name__)

def create_app(
    title: str,
    description: str,
    version: str,
    mongodb_url: str,
    rabbitmq_url: str,
    rabbitmq_exchange: str,
    rabbitmq_queue: str,
    rabbitmq_routing_key: str
) -> FastAPI:
    app = FastAPI(
        title=title,
        description=description,
        version=version
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize clients
    mongodb_client = MongoDBClient(mongodb_url)
    rabbitmq_client = RabbitMQClient(
        url=rabbitmq_url,
        exchange=rabbitmq_exchange,
        queue=rabbitmq_queue,
        routing_key=rabbitmq_routing_key
    )

    @app.on_event("startup")
    async def startup_event():
        """Initialize connections on startup"""
        try:
            # Connect to MongoDB
            if not await mongodb_client.connect():
                raise Exception("Failed to connect to MongoDB")
            
            # Connect to RabbitMQ and setup queues
            if not await rabbitmq_client.connect():
                raise Exception("Failed to connect to RabbitMQ")
            
            await rabbitmq_client.setup_queues()
            logger.info("Successfully initialized all connections")
        except Exception as e:
            logger.error(f"Failed to initialize connections: {str(e)}")
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup connections on shutdown"""
        try:
            # Stop RabbitMQ consumers
            await rabbitmq_client.stop_consuming()
            
            # Close RabbitMQ connection
            await rabbitmq_client.close()
            
            # Close MongoDB connection
            await mongodb_client.close()
            
            logger.info("Successfully closed all connections")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

    return app 