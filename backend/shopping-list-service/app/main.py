from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import asyncio
import logging
from .rabbitmq_utils import RabbitMQClient
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import threading

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Port Configuration
PORT = int(os.getenv("PORT", "8004"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "9094"))

# Prometheus metrics
REQUESTS = Counter('shopping_list_service_requests_total', 'Total requests to the shopping list service', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('shopping_list_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint'])
LIST_OPERATIONS = Counter('shopping_list_service_operations_total', 'Total shopping list operations', ['operation', 'status'])
MEAL_PLAN_SERVICE_LATENCY = Histogram('shopping_list_service_meal_plan_service_duration_seconds', 'Meal plan service request latency in seconds', ['operation'])

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
MEAL_PLANNING_SERVICE_URL = os.getenv("MEAL_PLANNING_SERVICE_URL", "http://meal-planning-service:8000")
RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://admin:password@rabbitmq:5672/")

# Initialize FastAPI app
app = FastAPI(title="Shopping List Service", description="Service for managing shopping lists")

# Initialize metrics app
metrics_app = FastAPI()

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(metrics_app)

# Security
security = HTTPBearer()

# Initialize RabbitMQ client
rabbitmq_client = RabbitMQClient(RABBITMQ_URI)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Database connection
@app.on_event("startup")
async def startup_db_client():
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        await app.mongodb_client.admin.command('ping')
        app.mongodb = app.mongodb_client[DB_NAME]
        logger.info("Successfully connected to MongoDB with optimized settings")
        
        # Create indexes for shopping lists collection
        await app.mongodb["shopping_lists"].create_index("user_id")
        await app.mongodb["shopping_lists"].create_index("meal_plan_id")
        
        # Setup RabbitMQ with retries
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Connect to RabbitMQ
                await rabbitmq_client.connect()
                await rabbitmq_client.setup_shopping_list_queues()
                
                # Start consuming messages from the meal_plans_created queue
                async def process_meal_plan_created(ch, method, properties, body):
                    try:
                        # Parse the message body
                        message = json.loads(body)
                        logger.info(f"Received meal plan created message: {message}")
                        
                        # Extract meal plan data from the message
                        meal_plan_id = message.get("meal_plan_id")
                        user_id = message.get("user_id")
                        
                        if not meal_plan_id or not user_id:
                            logger.warning("Invalid message format: missing required fields")
                            return
                            
                        # Create a shopping list from the meal plan
                        await create_shopping_list_from_meal_plan(meal_plan_id, user_id)
                        
                    except Exception as e:
                        logger.error(f"Error processing meal plan created message: {str(e)}")
                
                await rabbitmq_client.start_consuming(
                    queue_name="meal_plans_created",
                    callback=process_meal_plan_created
                )
                
                logger.info("Started consuming messages from RabbitMQ")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Failed to connect to RabbitMQ. Retrying in 5 seconds... (Attempt {retry_count}/{max_retries})")
                    await asyncio.sleep(5)
                else:
                    logger.error("Failed to connect to RabbitMQ after maximum retries")
                    raise e
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

@app.on_event("shutdown")
async def shutdown_db_client():
    if hasattr(app, "mongodb_client"):
        app.mongodb_client.close()
        logger.info("Closed MongoDB connection")
        
        # Stop consuming messages and close RabbitMQ connection
        rabbitmq_client.should_reconnect = False  # Prevent reconnection attempts during shutdown
        await rabbitmq_client.stop_consuming()
        await rabbitmq_client.close()
        logger.info("Closed RabbitMQ connection")

# Models
class ShoppingListItem(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    checked: bool = False

class ShoppingListBase(BaseModel):
    name: str
    items: List[ShoppingListItem]
    meal_plan_id: Optional[str] = None
    notes: Optional[str] = None

class ShoppingListCreate(ShoppingListBase):
    pass

class ShoppingList(ShoppingListBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class ShoppingListUpdate(BaseModel):
    name: Optional[str] = None
    items: Optional[List[ShoppingListItem]] = None
    notes: Optional[str] = None

class ItemCheckUpdate(BaseModel):
    checked: bool

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

# Helper functions
async def get_meal_plan_ingredients(meal_plan_id: str, token: str):
    """Get ingredients from a meal plan."""
    try:
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MEAL_PLANNING_SERVICE_URL}/meal-plans/{meal_plan_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            MEAL_PLAN_SERVICE_LATENCY.labels(operation="get_meal_plan").observe(time.time() - start_time)
            meal_plan = response.json()
            
            # Extract ingredients from meal plan
            ingredients = set()
            for day in meal_plan.get("days", []):
                for meal in day.get("meals", []):
                    for recipe in meal.get("recipes", []):
                        recipe_id = recipe.get("id")
                        if recipe_id:
                            start_time = time.time()
                            recipe_response = await client.get(
                                f"{MEAL_PLANNING_SERVICE_URL}/recipes/{recipe_id}",
                                headers={"Authorization": f"Bearer {token}"}
                            )
                            recipe_response.raise_for_status()
                            MEAL_PLAN_SERVICE_LATENCY.labels(operation="get_recipe").observe(time.time() - start_time)
                            recipe_data = recipe_response.json()
                            ingredients.update(recipe_data.get("ingredients", []))
            
            return list(ingredients)
    except httpx.HTTPError as e:
        logger.error(f"Error fetching meal plan ingredients: {e}")
        return []

def process_meal_plan_created(ch, method, properties, body):
    """
    Process meal plan created messages from RabbitMQ.
    This function is called when a message is received from the meal_plans_created queue.
    
    Args:
        ch: Channel
        method: Method
        properties: Properties
        body: Message body
    """
    try:
        # Parse the message body
        message = json.loads(body)
        logger.info(f"Received meal plan created message: {message}")
        
        # Extract meal plan data from the message
        meal_plan_id = message.get("meal_plan_id")
        user_id = message.get("user_id")
        
        if not meal_plan_id or not user_id:
            logger.warning("Invalid message format: missing required fields")
            return
        
        # Create a task to process the meal plan asynchronously
        asyncio.create_task(create_shopping_list_from_meal_plan(user_id, meal_plan_id))
        
    except Exception as e:
        logger.error(f"Error processing meal plan created message: {str(e)}")

async def create_shopping_list_from_meal_plan(user_id, meal_plan_id):
    """
    Create a shopping list from a meal plan.
    This function is called from the RabbitMQ callback to process meal plans.
    
    Args:
        user_id: User ID
        meal_plan_id: Meal Plan ID
    """
    try:
        # Get the user's token for authentication with other services
        # This is a simplified approach - in a real system, you might use a service account
        # or a different authentication mechanism for service-to-service communication
        token = "service_token"  # Placeholder
        
        # Fetch ingredients from the meal plan
        ingredients = await get_meal_plan_ingredients(meal_plan_id, token)
        
        if not ingredients:
            logger.warning(f"No ingredients found for meal plan: {meal_plan_id}")
            return
        
        # Create shopping list items from ingredients
        shopping_list_items = []
        for ingredient in ingredients:
            shopping_list_items.append(
                ShoppingListItem(
                    name=ingredient["name"],
                    quantity=ingredient.get("quantity"),
                    unit=ingredient.get("unit"),
                    checked=False
                )
            )
        
        # Create a new shopping list
        shopping_list_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        shopping_list_data = {
            "id": shopping_list_id,
            "user_id": user_id,
            "name": f"Shopping List for Meal Plan {meal_plan_id}",
            "items": [item.dict() for item in shopping_list_items],
            "meal_plan_id": meal_plan_id,
            "created_at": created_at,
            "updated_at": created_at
        }
        
        # Store the shopping list in the database
        await app.mongodb["shopping_lists"].insert_one(shopping_list_data)
        
        # Publish a message to notify that a shopping list has been created
        message = {
            "shopping_list_id": shopping_list_id,
            "user_id": user_id,
            "meal_plan_id": meal_plan_id,
            "item_count": len(shopping_list_items),
            "timestamp": created_at.isoformat()
        }
        
        rabbitmq_client.publish_message(
            exchange_name="shopping_lists",
            routing_key="shopping_list.created",
            message=message
        )
        
        logger.info(f"Created shopping list {shopping_list_id} for meal plan {meal_plan_id}")
        
    except Exception as e:
        logger.error(f"Error creating shopping list from meal plan: {str(e)}")

# Routes
@app.post("/shopping-lists", response_model=ShoppingList, status_code=status.HTTP_201_CREATED)
async def create_shopping_list(
    shopping_list: ShoppingListCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Create a new shopping list document
        shopping_list_data = shopping_list.dict()
        
        # Ensure items are properly formatted
        formatted_items = []
        for item in shopping_list_data.get("items", []):
            if isinstance(item, str):
                formatted_items.append({
                    "name": item,
                    "quantity": None,
                    "unit": None,
                    "checked": False
                })
            elif isinstance(item, dict):
                formatted_items.append({
                    "name": item.get("name", ""),
                    "quantity": item.get("quantity"),
                    "unit": item.get("unit"),
                    "checked": item.get("checked", False)
                })
        
        shopping_list_data["items"] = formatted_items
        shopping_list_data.update({
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert the shopping list into the database
        await app.mongodb["shopping_lists"].insert_one(shopping_list_data)
        logger.info(f"Created shopping list with ID: {shopping_list_data['id']}")
        
        # Publish event to RabbitMQ in a separate thread to avoid event loop issues
        def publish_event():
            try:
                event_data = {
                    "shopping_list_id": shopping_list_data["id"],
                    "user_id": current_user["id"],
                    "event_type": "created"
                }
                
                if not rabbitmq_client.publish_message(
                    exchange_name="shopping_lists",
                    routing_key="shopping_list.created",
                    message=event_data
                ):
                    logger.warning("Failed to publish shopping list created event")
            except Exception as e:
                logger.error(f"Error publishing event: {str(e)}")
        
        # Run the RabbitMQ publish in a thread
        threading.Thread(target=publish_event, daemon=True).start()
        
        return shopping_list_data
        
    except Exception as e:
        logger.error(f"Error creating shopping list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating shopping list: {str(e)}"
        )

@app.get("/shopping-lists", response_model=List[ShoppingList])
async def get_shopping_lists(current_user: dict = Depends(get_current_user)):
    try:
        shopping_lists = await app.mongodb["shopping_lists"].find({"user_id": current_user["id"]}).to_list(length=None)
        LIST_OPERATIONS.labels(operation="list", status="success").inc()
        return shopping_lists
    except Exception as e:
        LIST_OPERATIONS.labels(operation="list", status="error").inc()
        logger.error(f"Error fetching shopping lists: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching shopping lists"
        )

@app.get("/shopping-lists/{shopping_list_id}", response_model=ShoppingList)
async def get_shopping_list(shopping_list_id: str, current_user: dict = Depends(get_current_user)):
    try:
        shopping_list = await app.mongodb["shopping_lists"].find_one({
            "id": shopping_list_id,
            "user_id": current_user["id"]
        })
        
        if not shopping_list:
            LIST_OPERATIONS.labels(operation="get", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shopping list {shopping_list_id} not found"
            )
        
        LIST_OPERATIONS.labels(operation="get", status="success").inc()
        return shopping_list
    except Exception as e:
        if not isinstance(e, HTTPException):
            LIST_OPERATIONS.labels(operation="get", status="error").inc()
        raise e

@app.put("/shopping-lists/{shopping_list_id}", response_model=ShoppingList)
async def update_shopping_list(
    shopping_list_id: str,
    shopping_list_update: ShoppingListUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Check if shopping list exists and belongs to user
        shopping_list = await app.mongodb["shopping_lists"].find_one({
            "id": shopping_list_id,
            "user_id": current_user["id"]
        })
        
        if not shopping_list:
            LIST_OPERATIONS.labels(operation="update", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shopping list {shopping_list_id} not found"
            )
        
        # Update shopping list
        update_data = shopping_list_update.dict(exclude_unset=True)
        if "items" in update_data:
            update_data["items"] = [item.dict() for item in shopping_list_update.items]
        
        update_data["updated_at"] = datetime.utcnow()
        
        await app.mongodb["shopping_lists"].update_one(
            {"id": shopping_list_id},
            {"$set": update_data}
        )
        
        updated_shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id})
        LIST_OPERATIONS.labels(operation="update", status="success").inc()
        return updated_shopping_list
    except Exception as e:
        if not isinstance(e, HTTPException):
            LIST_OPERATIONS.labels(operation="update", status="error").inc()
        raise e

@app.put("/shopping-lists/{shopping_list_id}/items/{item_name}/check", response_model=ShoppingList)
async def check_item(
    shopping_list_id: str,
    item_name: str,
    update: ItemCheckUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Check if shopping list exists and belongs to user
        shopping_list = await app.mongodb["shopping_lists"].find_one({
            "id": shopping_list_id,
            "user_id": current_user["id"]
        })
        
        if not shopping_list:
            LIST_OPERATIONS.labels(operation="check_item", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shopping list {shopping_list_id} not found"
            )
        
        # Find and update the item
        item_found = False
        for item in shopping_list["items"]:
            if item["name"].lower() == item_name.lower():
                item["checked"] = update.checked
                item_found = True
                break
        
        if not item_found:
            LIST_OPERATIONS.labels(operation="check_item", status="item_not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_name} not found in shopping list"
            )
        
        # Update the shopping list
        await app.mongodb["shopping_lists"].update_one(
            {"id": shopping_list_id},
            {
                "$set": {
                    "items": shopping_list["items"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        updated_shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id})
        LIST_OPERATIONS.labels(operation="check_item", status="success").inc()
        return updated_shopping_list
    except Exception as e:
        if not isinstance(e, HTTPException):
            LIST_OPERATIONS.labels(operation="check_item", status="error").inc()
        raise e

@app.delete("/shopping-lists/{shopping_list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list(shopping_list_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # Check if shopping list exists and belongs to user
        shopping_list = await app.mongodb["shopping_lists"].find_one({
            "id": shopping_list_id,
            "user_id": current_user["id"]
        })
        
        if not shopping_list:
            LIST_OPERATIONS.labels(operation="delete", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shopping list {shopping_list_id} not found"
            )
        
        # Delete shopping list
        await app.mongodb["shopping_lists"].delete_one({"id": shopping_list_id})
        LIST_OPERATIONS.labels(operation="delete", status="success").inc()
    except Exception as e:
        if not isinstance(e, HTTPException):
            LIST_OPERATIONS.labels(operation="delete", status="error").inc()
        raise e

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Start metrics server in a separate thread
def run_metrics_server():
    uvicorn.run(metrics_app, host="0.0.0.0", port=METRICS_PORT)

# Start the metrics server in a background thread when the app starts
@app.on_event("startup")
async def startup_event():
    metrics_thread = threading.Thread(target=run_metrics_server, daemon=True)
    metrics_thread.start()
    logger.info(f"Metrics server started on port {METRICS_PORT}") 