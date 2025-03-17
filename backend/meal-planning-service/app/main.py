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
                f"{RECIPE_SERVICE_URL}/profile",
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
async def fetch_recipes(ingredients=None, tags=None, cuisine=None):
    params = {}
    if ingredients:
        params["ingredients"] = ",".join(ingredients)
    if tags:
        params["tags"] = ",".join(tags)
    if cuisine:
        params["cuisine"] = cuisine
    
    try:
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_SERVICE_URL}/recipes", params=params)
            response.raise_for_status()
            RECIPE_SERVICE_LATENCY.labels(operation="fetch_recipes").observe(time.time() - start_time)
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error fetching recipes: {e}")
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
        logger.info(f"Received message: {message}")
        
        # Extract ingredients from the message
        scan_id = message.get("scan_id")
        user_id = message.get("user_id")
        ingredients_data = message.get("ingredients", [])
        
        if not scan_id or not user_id or not ingredients_data:
            logger.warning("Invalid message format: missing required fields")
            return
        
        # Extract ingredient names
        ingredient_names = [item.get("name") for item in ingredients_data if item.get("name")]
        
        if not ingredient_names:
            logger.warning("No valid ingredients found in the message")
            return
        
        logger.info(f"Processing {len(ingredient_names)} ingredients for user {user_id}: {ingredient_names}")
        
        # Create a task to process the ingredients asynchronously
        asyncio.create_task(process_ingredients_async(user_id, scan_id, ingredient_names))
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")

async def process_ingredients_async(user_id, scan_id, ingredient_names):
    """
    Process ingredients asynchronously.
    This function is called from the RabbitMQ callback to process ingredients.
    
    Args:
        user_id: User ID
        scan_id: Scan ID
        ingredient_names: List of ingredient names
    """
    try:
        # Fetch recipes that match the ingredients
        recipes = await fetch_recipes(ingredients=ingredient_names)
        
        if not recipes:
            logger.warning(f"No recipes found for ingredients: {ingredient_names}")
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
        await db.recipe_suggestions.insert_one(suggestion)
        
        # Publish a message to notify that recipes have been suggested
        message = {
            "user_id": user_id,
            "scan_id": scan_id,
            "suggestion_id": str(suggestion.get("_id")),
            "ingredient_count": len(ingredient_names),
            "recipe_count": len(recipes),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        rabbitmq_client.publish_message(
            exchange_name="meal_plans",
            routing_key="recipe.suggestion",
            message=message
        )
        
        logger.info(f"Processed ingredients and suggested recipes for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing ingredients asynchronously: {str(e)}") 