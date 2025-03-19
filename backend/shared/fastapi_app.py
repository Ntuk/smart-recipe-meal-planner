from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
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

    # Attach clients to app state
    app.state.mongodb_client = mongodb_client
    app.state.rabbitmq_client = rabbitmq_client

    @app.on_event("startup")
    async def startup_event():
        """Initialize connections on startup"""
        try:
            # Connect to MongoDB
            await mongodb_client.connect()
            
            # Initialize database
            db_name = os.getenv("DB_NAME", "recipe_app")
            try:
                db = await mongodb_client.get_database(db_name)
                # Store the database in app state, ensuring it's properly initialized
                # Avoid direct object comparison that might cause issues with MongoDB objects
                setattr(app.state, 'db', db)
                # Verify connection works
                await db.command("ping")
                logger.info(f"Successfully initialized MongoDB database: {db_name}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {str(e)}")
                raise

            # Connect to RabbitMQ
            await rabbitmq_client.connect()
            logger.info("Successfully initialized all connections")
        except Exception as e:
            logger.error(f"Error during startup: {str(e)}")
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """Close connections on shutdown"""
        try:
            # Close MongoDB connection
            await mongodb_client.close()
            # Close RabbitMQ connection
            await rabbitmq_client.close()
            logger.info("Successfully closed all connections")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

    return app 