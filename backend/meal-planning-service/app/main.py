from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import httpx
import logging
import random
from bson import ObjectId
import uuid
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, date
import json
import asyncio
from .rabbitmq_utils import RabbitMQClient
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
import nest_asyncio

# Prometheus metrics
REQUESTS = Counter('meal_planning_service_requests_total', 'Total requests to the meal planning service', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('meal_planning_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint'])
MEAL_PLAN_OPERATIONS = Counter('meal_planning_service_operations_total', 'Total meal plan operations', ['operation', 'status'])
RECIPE_SERVICE_LATENCY = Histogram('meal_planning_service_recipe_service_duration_seconds', 'Recipe service request latency in seconds', ['operation'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Meal Planning Service API", description="API for planning meals based on ingredients and preferences")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DB_NAME", "recipe_db")
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://localhost:8001")
RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://guest:guest@localhost:5672/")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")

# Initialize RabbitMQ client
rabbitmq_client = RabbitMQClient(RABBITMQ_URI)

# Security
security = HTTPBearer()

# Models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field_schema):
        return {"type": "string"}

class Recipe(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    description: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    tags: List[str] = []
    cuisine: Optional[str] = None
    difficulty: Optional[str] = None
    nutritional_info: Optional[dict] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RecipeRef(BaseModel):
    id: str
    name: str
    prep_time: int
    cook_time: int
    servings: int
    image_url: Optional[str] = None

class Meal(BaseModel):
    name: str  # e.g., "Breakfast", "Lunch", "Dinner", "Snack"
    time: Optional[str] = None  # e.g., "08:00", "12:30"
    recipes: List[RecipeRef] = []
    notes: Optional[str] = None

class MealPlanDay(BaseModel):
    date: date
    meals: List[Meal] = []
    notes: Optional[str] = None

class MealPlanBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    days: List[MealPlanDay] = []
    notes: Optional[str] = None

class MealPlanCreate(MealPlanBase):
    pass

class MealPlan(MealPlanBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class MealPlanUpdate(BaseModel):
    name: Optional[str] = None
    days: Optional[List[MealPlanDay]] = None
    notes: Optional[str] = None

class MealPlanResponse(BaseModel):
    id: str
    name: str
    recipes: List[Recipe]
    days: int
    created_at: Optional[str] = None
    dietary_preferences: List[str] = []

# Database connection
@app.on_event("startup")
async def startup_db_client():
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
        app.mongodb = app.mongodb_client[DATABASE_NAME]
        # Ping the database to check the connection
        await app.mongodb_client.admin.command('ping')
        logger.info("Connected to MongoDB")
        
        # Setup RabbitMQ
        if rabbitmq_client.connect():
            rabbitmq_client.setup_meal_planning_queues()
            
            # Start consuming messages from the detected_ingredients queue
            rabbitmq_client.start_consuming(
                queue_name="detected_ingredients",
                callback=process_detected_ingredients
            )
            logger.info("Started consuming messages from RabbitMQ")
        else:
            logger.warning("Failed to connect to RabbitMQ during startup. Will retry on demand.")
            
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    
    # Stop consuming messages and close RabbitMQ connection
    rabbitmq_client.stop_consuming()
    rabbitmq_client.close()
    logger.info("RabbitMQ connection closed")

# Dependency to get database
async def get_database():
    return app.mongodb

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )

# Request monitoring middleware
@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Helper function to fetch recipes from Recipe Service
async def fetch_recipes(ingredients=None, tags=None, cuisine=None, token=None):
    params = {}
    if ingredients:
        params["ingredients"] = ",".join(ingredients)
    if tags:
        params["tags"] = ",".join(tags)
    if cuisine:
        params["cuisine"] = cuisine
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        start_time = time.time()
        logger.info(f"Fetching recipes from {RECIPE_SERVICE_URL} with params: {params}")
        logger.info(f"Using token: {bool(token)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RECIPE_SERVICE_URL}/recipes",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            RECIPE_SERVICE_LATENCY.labels(operation="fetch_recipes").observe(time.time() - start_time)
            result = response.json()
            logger.info(f"Received {len(result)} recipes from recipe service")
            return result
    except httpx.HTTPStatusError as http_err:
        logger.error(f"HTTP error fetching recipes: {http_err.response.status_code} - {http_err}")
        # Try without auth if we get a 401
        if http_err.response.status_code == 401 and token:
            logger.info("Trying to fetch recipes without authentication")
            return await fetch_recipes(ingredients, tags, cuisine, None)
        return []
    except Exception as e:
        logger.error(f"Error fetching recipes: {str(e)}")
        return []

# Helper function to fetch a recipe by ID from Recipe Service
async def fetch_recipe_by_id(recipe_id):
    try:
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_SERVICE_URL}/recipes/{recipe_id}")
            response.raise_for_status()
            RECIPE_SERVICE_LATENCY.labels(operation="fetch_recipe_by_id").observe(time.time() - start_time)
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error fetching recipe {recipe_id}: {e}")
        return None

# Routes
@app.get("/")
async def root():
    return {"message": "Meal Planning Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/meal-plans", response_model=MealPlan, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    meal_plan: MealPlanCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        now = datetime.utcnow()
        meal_plan_id = str(uuid.uuid4())
        
        # Convert days to dict for MongoDB
        days_data = []
        for day in meal_plan.days:
            day_dict = day.dict()
            day_dict["date"] = day.date.isoformat()
            days_data.append(day_dict)
        
        meal_plan_data = {
            "id": meal_plan_id,
            "user_id": current_user["id"],
            "name": meal_plan.name,
            "start_date": meal_plan.start_date.isoformat(),
            "end_date": meal_plan.end_date.isoformat(),
            "days": days_data,
            "notes": meal_plan.notes,
            "created_at": now,
            "updated_at": now
        }
        
        await app.mongodb.meal_plans.insert_one(meal_plan_data)
        MEAL_PLAN_OPERATIONS.labels(operation="create", status="success").inc()
        return meal_plan_data
    except Exception as e:
        MEAL_PLAN_OPERATIONS.labels(operation="create", status="error").inc()
        logger.error(f"Error creating meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating meal plan"
        )

@app.get("/meal-plans", response_model=List[MealPlan])
async def get_meal_plans(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        query = {"user_id": current_user["id"]}
        
        if start_date:
            query["start_date"] = {"$gte": start_date.isoformat()}
        if end_date:
            query["end_date"] = {"$lte": end_date.isoformat()}
        
        cursor = app.mongodb.meal_plans.find(query)
        meal_plans = await cursor.to_list(length=None)
        
        MEAL_PLAN_OPERATIONS.labels(operation="list", status="success").inc()
        return meal_plans
    except Exception as e:
        MEAL_PLAN_OPERATIONS.labels(operation="list", status="error").inc()
        logger.error(f"Error fetching meal plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching meal plans"
        )

@app.get("/meal-plans/{meal_plan_id}", response_model=MealPlan)
async def get_meal_plan(meal_plan_id: str, current_user: dict = Depends(get_current_user)):
    try:
        meal_plan = await app.mongodb.meal_plans.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            MEAL_PLAN_OPERATIONS.labels(operation="get", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        MEAL_PLAN_OPERATIONS.labels(operation="get", status="success").inc()
        return meal_plan
    except Exception as e:
        if not isinstance(e, HTTPException):
            MEAL_PLAN_OPERATIONS.labels(operation="get", status="error").inc()
        raise e

@app.put("/meal-plans/{meal_plan_id}", response_model=MealPlan)
async def update_meal_plan(
    meal_plan_id: str,
    meal_plan_update: MealPlanUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Check if meal plan exists and belongs to user
        meal_plan = await app.mongodb.meal_plans.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            MEAL_PLAN_OPERATIONS.labels(operation="update", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        # Update meal plan
        update_data = meal_plan_update.dict(exclude_unset=True)
        if "days" in update_data:
            days_data = []
            for day in update_data["days"]:
                day_dict = day.dict()
                day_dict["date"] = day.date.isoformat()
                days_data.append(day_dict)
            update_data["days"] = days_data
        
        update_data["updated_at"] = datetime.utcnow()
        
        await app.mongodb.meal_plans.update_one(
            {"id": meal_plan_id},
            {"$set": update_data}
        )
        
        updated_meal_plan = await app.mongodb.meal_plans.find_one({"id": meal_plan_id})
        MEAL_PLAN_OPERATIONS.labels(operation="update", status="success").inc()
        return updated_meal_plan
    except Exception as e:
        if not isinstance(e, HTTPException):
            MEAL_PLAN_OPERATIONS.labels(operation="update", status="error").inc()
        raise e

@app.delete("/meal-plans/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(meal_plan_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # Check if meal plan exists and belongs to user
        meal_plan = await app.mongodb.meal_plans.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            MEAL_PLAN_OPERATIONS.labels(operation="delete", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        # Delete meal plan
        await app.mongodb.meal_plans.delete_one({"id": meal_plan_id})
        MEAL_PLAN_OPERATIONS.labels(operation="delete", status="success").inc()
    except Exception as e:
        if not isinstance(e, HTTPException):
            MEAL_PLAN_OPERATIONS.labels(operation="delete", status="error").inc()
        raise e

@app.get("/meal-plans/suggestions", response_model=List[dict])
async def get_recipe_suggestions(
    current_user: dict = Depends(get_current_user)
):
    """
    Get recipe suggestions based on scanned ingredients for the current user.
    Returns the most recent suggestions first.
    """
    try:
        logger.info(f"Fetching recipe suggestions for user: {current_user['id']}")
        db = app.mongodb
        
        # First check if the collection exists
        collections = await db.list_collection_names()
        if "recipe_suggestions" not in collections:
            logger.info("recipe_suggestions collection does not exist yet")
            return []
            
        # Query for suggestions
        cursor = db.recipe_suggestions.find(
            {"user_id": current_user["id"]},
            sort=[("created_at", -1)],
            limit=10
        )
        suggestions = await cursor.to_list(length=None)
        
        logger.info(f"Found {len(suggestions)} suggestions for user: {current_user['id']}")
        
        if not suggestions:
            logger.info(f"No suggestions found for user: {current_user['id']}")
            return []
            
        # Convert ObjectId to string for JSON serialization
        for suggestion in suggestions:
            suggestion["_id"] = str(suggestion["_id"])
            # Convert datetime to string for JSON serialization
            if isinstance(suggestion.get("created_at"), datetime):
                suggestion["created_at"] = suggestion["created_at"].isoformat()
            
        return suggestions
    except Exception as e:
        logger.error(f"Error fetching recipe suggestions: {str(e)}")
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")
        # Return empty array instead of raising an error
        return []

@app.get("/meal-plans/suggestions-basic")
async def get_basic_suggestions(
    current_user: dict = Depends(get_current_user)
):
    """
    A simplified endpoint that doesn't access MongoDB directly.
    Used for testing when there are issues with the database or message broker.
    """
    return [
        {
            "id": "simple-suggestion",
            "user_id": current_user["id"],
            "ingredients": ["chicken", "rice", "vegetables"],
            "suggested_recipes": [
                {
                    "id": "simple-recipe",
                    "name": "Simplified Chicken Rice Bowl",
                    "prep_time": 10,
                    "cook_time": 20,
                    "servings": 2
                }
            ],
            "created_at": datetime.utcnow().isoformat()
        }
    ]

def process_detected_ingredients(ch, method, properties, body):
    """
    Process detected ingredients from RabbitMQ.
    This function is called when a message is received from the detected_ingredients queue.
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    try:
        # Parse the message body
        message = json.loads(body)
        logger.info(f"Received message from RabbitMQ: {message}")
        
        # Extract ingredients from the message
        scan_id = message.get("scan_id")
        user_id = message.get("user_id")
        token = message.get("token")
        ingredients_data = message.get("ingredients", [])
        
        logger.info(f"Extracted data - scan_id: {scan_id}, user_id: {user_id}, token present: {bool(token)}, ingredients count: {len(ingredients_data)}")
        
        if not scan_id:
            logger.warning("Missing scan_id in message")
            return
            
        if not user_id:
            logger.warning("Missing user_id in message")
            return
            
        if not token:
            logger.warning("Missing token in message")
            return
            
        if not ingredients_data:
            logger.warning("No ingredients data in message")
            return
        
        # Extract ingredient names
        ingredient_names = [item.get("name") for item in ingredients_data if item.get("name")]
        logger.info(f"Extracted ingredient names: {ingredient_names}")
        
        if not ingredient_names:
            logger.warning("No valid ingredients found in the message")
            return
        
        logger.info(f"Processing {len(ingredient_names)} ingredients for user {user_id}: {ingredient_names}")
        
        # Run the async function in a new event loop
        nest_asyncio.apply()
        
        # Create a new event loop and run the coroutine
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process_ingredients_async(user_id, scan_id, ingredient_names, token))
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")

async def process_ingredients_async(user_id, scan_id, ingredient_names, token):
    """
    Process ingredients asynchronously.
    This function is called from the RabbitMQ callback to process ingredients.
    
    Args:
        user_id: User ID
        scan_id: Scan ID
        ingredient_names: List of ingredient names
        token: User's authentication token
    """
    try:
        logger.info(f"Processing ingredients asynchronously for user {user_id}, scan {scan_id}")
        logger.info(f"Ingredients: {ingredient_names}")
        logger.info(f"Token available: {bool(token)}")
        
        # Fetch recipes that match the ingredients
        try:
            logger.info(f"Attempting to fetch recipes with ingredients: {ingredient_names}")
            recipes = await fetch_recipes(ingredients=ingredient_names, token=token)
            logger.info(f"Fetch recipes result: {recipes and len(recipes) or 0} recipes found")
            if recipes:
                logger.info(f"Found recipes: {[recipe.get('name', 'Unknown') for recipe in recipes]}")
        except Exception as fetch_error:
            logger.error(f"Error fetching recipes: {str(fetch_error)}")
            import traceback
            logger.error(f"Detailed fetch error: {traceback.format_exc()}")
            recipes = []
        
        if not recipes:
            logger.warning(f"No recipes found for ingredients: {ingredient_names}")
            # Store the empty suggestions anyway so we can see the attempt
            suggestion = {
                "user_id": user_id,
                "scan_id": scan_id,
                "ingredients": ingredient_names,
                "suggested_recipes": [],
                "created_at": datetime.utcnow(),
                "error": "No recipes found for the provided ingredients"
            }
            
            db = app.mongodb
            try:
                logger.info(f"Storing empty suggestion record for user {user_id}")
                await db.recipe_suggestions.insert_one(suggestion)
                logger.info(f"Successfully stored empty suggestion record for user {user_id}")
            except Exception as db_error:
                logger.error(f"Error storing empty suggestion: {str(db_error)}")
                import traceback
                logger.error(f"Detailed DB error: {traceback.format_exc()}")
            
            return
        
        logger.info(f"Found {len(recipes)} recipes matching ingredients")
        
        # Store the suggested recipes in the database
        suggestion = {
            "user_id": user_id,
            "scan_id": scan_id,
            "ingredients": ingredient_names,
            "suggested_recipes": recipes,
            "created_at": datetime.utcnow()
        }
        
        db = app.mongodb
        try:
            logger.info(f"Storing suggestion with recipes for user {user_id}")
            result = await db.recipe_suggestions.insert_one(suggestion)
            suggestion_id = str(result.inserted_id)
            logger.info(f"Successfully stored suggestion with ID: {suggestion_id}")
        except Exception as db_error:
            logger.error(f"Error storing suggestion: {str(db_error)}")
            import traceback
            logger.error(f"Detailed DB error: {traceback.format_exc()}")
            return
        
        # Publish a message to notify that recipes have been suggested
        try:
            message = {
                "user_id": user_id,
                "scan_id": scan_id,
                "suggestion_id": suggestion_id,
                "ingredient_count": len(ingredient_names),
                "recipe_count": len(recipes),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Publishing suggestion notification: {message}")
            publish_result = rabbitmq_client.publish_message(
                exchange_name="meal_plans",
                routing_key="recipe.suggestion",
                message=message
            )
            logger.info(f"Published message result: {publish_result}")
        except Exception as publish_error:
            logger.error(f"Error publishing suggestion notification: {str(publish_error)}")
            import traceback
            logger.error(f"Detailed publish error: {traceback.format_exc()}")
        
        logger.info(f"Successfully processed ingredients and suggested recipes for user {user_id}")
        
    except Exception as e:
        logger.error(f"Unexpected error in process_ingredients_async: {str(e)}")
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")

@app.get("/test")
async def test_endpoint():
    """
    A simple test endpoint that just returns a static message.
    """
    return {"message": "Meal planning service is working"} 