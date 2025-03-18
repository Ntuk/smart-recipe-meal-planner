from shared.logging_config import configure_logging
from fastapi import FastAPI
from shared.mongodb_utils import MongoDBClient
from shared.rabbitmq_utils import RabbitMQClient

configure_logging() 

app = FastAPI()
mongodb = MongoDBClient("mongodb://mongodb:27017")
rabbitmq = RabbitMQClient("amqp://admin:password@rabbitmq:5672/")

@app.on_event("startup")
async def startup():
    # Connect to MongoDB
    if not await mongodb.connect():
        raise Exception("Failed to connect to MongoDB")
    app.mongodb = mongodb.client

    # Connect to RabbitMQ
    if not rabbitmq.connect():
        logger.warning("Failed to connect to RabbitMQ")
    else:
        # Setup your queues and start consuming
        rabbitmq.setup_queues()
        rabbitmq.start_consuming("your_queue", your_callback)

@app.on_event("shutdown")
async def shutdown():
    await mongodb.close()
    rabbitmq.stop_consuming() 