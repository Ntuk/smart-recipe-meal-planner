import os
from shared.fastapi_app import create_app
from shared.logging_config import setup_logging

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

# Import and include routers
from .routers import meal_plans
app.include_router(meal_plans.router, prefix="/api/v1/meal-plans", tags=["meal-plans"]) 