import os
import logging
from shared.fastapi_app import create_app
from shared.logging_config import setup_logging
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from .routers import meal_plans
from shared import rabbitmq_utils
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from dotenv import load_dotenv
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
from prometheus_fastapi_instrumentator import Instrumentator
import threading
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG to get more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Set MongoDB driver logging to DEBUG
logging.getLogger("motor").setLevel(logging.DEBUG)
logging.getLogger("pymongo").setLevel(logging.DEBUG)

# Apply MongoDB fix for database object comparison
try:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    
    # Monkey patch to fix the database comparison issue
    def __bool__(self):
        """Returns True if the database object exists."""
        return True
        
    # Apply the patch
    AsyncIOMotorDatabase.__bool__ = __bool__
    print("MongoDB database object comparison patch applied!")
except Exception as e:
    print(f"Failed to apply MongoDB patch: {str(e)}")

# Setup logging
setup_logging()

# Create FastAPI app with shared configuration
app = create_app(
    title="Meal Planning Service",
    description="Service for generating meal plans based on ingredients and preferences",
    version="1.0.0",
    mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
    rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://admin:password@localhost:5672/"),
    rabbitmq_exchange="meal_planning",
    rabbitmq_queue="meal_planning_queue",
    rabbitmq_routing_key="meal_planning"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(meal_plans.router, prefix="/api/v1/meal-plans", tags=["meal-plans"])

# Port Configuration
PORT = int(os.getenv("PORT", "8003"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "9093"))

# Prometheus metrics
REQUESTS = Counter('meal_planning_service_requests_total', 'Total requests to the meal planning service', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('meal_planning_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint'])
PLAN_OPERATIONS = Counter('meal_planning_service_operations_total', 'Total meal plan operations', ['operation', 'status'])

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://recipe-service:8001")

# Initialize metrics app
metrics_app = FastAPI()

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(metrics_app)

# Start metrics server in a separate thread
def run_metrics_server():
    uvicorn.run(metrics_app, host="0.0.0.0", port=METRICS_PORT)

# Start the metrics server in a background thread when the app starts
@app.on_event("startup")
async def startup_event():
    metrics_thread = threading.Thread(target=run_metrics_server, daemon=True)
    metrics_thread.start()
    logger.info(f"Metrics server started on port {METRICS_PORT}") 