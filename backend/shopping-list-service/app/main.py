from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import httpx
import logging
from bson import ObjectId
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Shopping List Service API", description="API for generating shopping lists based on meal plans")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "recipe_db")
MEAL_PLANNING_SERVICE_URL = os.getenv("MEAL_PLANNING_SERVICE_URL", "http://localhost:8003")

# MongoDB client
client = None

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
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class ShoppingListItem(BaseModel):
    ingredient: str
    quantity: Optional[str] = None
    checked: bool = False

class ShoppingList(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[str] = None
    meal_plan_id: str
    name: str
    items: List[ShoppingListItem]
    created_at: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ShoppingListCreate(BaseModel):
    meal_plan_id: str
    name: str
    available_ingredients: List[str] = []
    user_id: Optional[str] = None

class ShoppingListResponse(BaseModel):
    id: str
    meal_plan_id: str
    name: str
    items: List[ShoppingListItem]
    created_at: Optional[str] = None

# Database connection
@app.on_event("startup")
async def startup_db_client():
    global client
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        # Validate the connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

# Dependency to get database
async def get_database():
    return client[DATABASE_NAME]

# Helper function to fetch meal plan from Meal Planning Service
async def fetch_meal_plan(meal_plan_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MEAL_PLANNING_SERVICE_URL}/meal-plans/{meal_plan_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error fetching meal plan {meal_plan_id}: {e}")
        return None

# Routes
@app.get("/")
async def root():
    return {"message": "Shopping List Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/shopping-lists", response_model=ShoppingListResponse)
async def create_shopping_list(shopping_list: ShoppingListCreate, db=Depends(get_database)):
    # Fetch meal plan
    meal_plan = await fetch_meal_plan(shopping_list.meal_plan_id)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Extract all ingredients from recipes in the meal plan
    all_ingredients = set()
    for recipe in meal_plan["recipes"]:
        all_ingredients.update(recipe["ingredients"])
    
    # Remove ingredients that are already available
    missing_ingredients = all_ingredients - set(shopping_list.available_ingredients)
    
    # Create shopping list items
    items = [{"ingredient": ingredient, "quantity": None, "checked": False} for ingredient in missing_ingredients]
    
    # Create shopping list
    new_shopping_list = {
        "meal_plan_id": shopping_list.meal_plan_id,
        "name": shopping_list.name,
        "items": items,
        "created_at": datetime.now().isoformat(),
    }
    
    if shopping_list.user_id:
        new_shopping_list["user_id"] = shopping_list.user_id
    
    result = await db.shopping_lists.insert_one(new_shopping_list)
    
    # Fetch the created shopping list
    created_shopping_list = await db.shopping_lists.find_one({"_id": result.inserted_id})
    
    # Prepare response
    response = {
        "id": str(created_shopping_list["_id"]),
        "meal_plan_id": created_shopping_list["meal_plan_id"],
        "name": created_shopping_list["name"],
        "items": created_shopping_list["items"],
        "created_at": created_shopping_list["created_at"],
    }
    
    return response

@app.get("/shopping-lists/{shopping_list_id}", response_model=ShoppingListResponse)
async def get_shopping_list(shopping_list_id: str, db=Depends(get_database)):
    if not ObjectId.is_valid(shopping_list_id):
        raise HTTPException(status_code=400, detail="Invalid shopping list ID format")
    
    shopping_list = await db.shopping_lists.find_one({"_id": ObjectId(shopping_list_id)})
    if shopping_list is None:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    # Prepare response
    response = {
        "id": str(shopping_list["_id"]),
        "meal_plan_id": shopping_list["meal_plan_id"],
        "name": shopping_list["name"],
        "items": shopping_list["items"],
        "created_at": shopping_list.get("created_at"),
    }
    
    return response

@app.get("/shopping-lists", response_model=List[ShoppingList])
async def get_shopping_lists(user_id: Optional[str] = None, db=Depends(get_database)):
    query = {}
    if user_id:
        query["user_id"] = user_id
    
    shopping_lists = await db.shopping_lists.find(query).to_list(100)
    return shopping_lists

@app.put("/shopping-lists/{shopping_list_id}/items/{ingredient}/check", response_model=ShoppingListResponse)
async def check_shopping_list_item(shopping_list_id: str, ingredient: str, checked: bool = True, db=Depends(get_database)):
    if not ObjectId.is_valid(shopping_list_id):
        raise HTTPException(status_code=400, detail="Invalid shopping list ID format")
    
    # Update the checked status of the item
    result = await db.shopping_lists.update_one(
        {"_id": ObjectId(shopping_list_id), "items.ingredient": ingredient},
        {"$set": {"items.$.checked": checked}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shopping list or item not found")
    
    # Fetch the updated shopping list
    updated_shopping_list = await db.shopping_lists.find_one({"_id": ObjectId(shopping_list_id)})
    
    # Prepare response
    response = {
        "id": str(updated_shopping_list["_id"]),
        "meal_plan_id": updated_shopping_list["meal_plan_id"],
        "name": updated_shopping_list["name"],
        "items": updated_shopping_list["items"],
        "created_at": updated_shopping_list.get("created_at"),
    }
    
    return response

@app.delete("/shopping-lists/{shopping_list_id}")
async def delete_shopping_list(shopping_list_id: str, db=Depends(get_database)):
    if not ObjectId.is_valid(shopping_list_id):
        raise HTTPException(status_code=400, detail="Invalid shopping list ID format")
    
    result = await db.shopping_lists.delete_one({"_id": ObjectId(shopping_list_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    return {"message": "Shopping list deleted successfully"} 