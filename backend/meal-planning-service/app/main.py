from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import httpx
import logging
import random
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "recipe_db")
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://localhost:8001")

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
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MealPlan(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[str] = None
    name: str
    recipes: List[str]  # List of recipe IDs
    days: int
    created_at: Optional[str] = None
    dietary_preferences: List[str] = []

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MealPlanCreate(BaseModel):
    name: str
    days: int = 7
    dietary_preferences: List[str] = []
    available_ingredients: List[str] = []
    user_id: Optional[str] = None

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
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_SERVICE_URL}/recipes", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error fetching recipes: {e}")
        return []

# Helper function to fetch a recipe by ID from Recipe Service
async def fetch_recipe_by_id(recipe_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECIPE_SERVICE_URL}/recipes/{recipe_id}")
            response.raise_for_status()
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

@app.post("/meal-plans", response_model=MealPlanResponse)
async def create_meal_plan(meal_plan: MealPlanCreate, db=Depends(get_database)):
    # Fetch recipes based on available ingredients and dietary preferences
    recipes = await fetch_recipes(
        ingredients=meal_plan.available_ingredients,
        tags=meal_plan.dietary_preferences
    )
    
    # If no recipes found with the exact ingredients, try to find recipes with at least some of the ingredients
    if not recipes and meal_plan.available_ingredients:
        # Try with fewer ingredients
        for i in range(len(meal_plan.available_ingredients) - 1, 0, -1):
            subset = meal_plan.available_ingredients[:i]
            recipes = await fetch_recipes(ingredients=subset, tags=meal_plan.dietary_preferences)
            if recipes:
                break
    
    # If still no recipes, fetch any recipes that match dietary preferences
    if not recipes and meal_plan.dietary_preferences:
        recipes = await fetch_recipes(tags=meal_plan.dietary_preferences)
    
    # If still no recipes, fetch any recipes
    if not recipes:
        recipes = await fetch_recipes()
    
    # Limit recipes to the number of days in the meal plan
    if len(recipes) > meal_plan.days:
        # Randomly select recipes for variety
        recipes = random.sample(recipes, meal_plan.days)
    
    # Create meal plan
    recipe_ids = [recipe["_id"] for recipe in recipes]
    
    from datetime import datetime
    new_meal_plan = {
        "name": meal_plan.name,
        "recipes": recipe_ids,
        "days": meal_plan.days,
        "created_at": datetime.now().isoformat(),
        "dietary_preferences": meal_plan.dietary_preferences,
    }
    
    if meal_plan.user_id:
        new_meal_plan["user_id"] = meal_plan.user_id
    
    result = await db.meal_plans.insert_one(new_meal_plan)
    
    # Fetch the created meal plan
    created_meal_plan = await db.meal_plans.find_one({"_id": result.inserted_id})
    
    # Fetch full recipe details for response
    recipe_details = []
    for recipe_id in created_meal_plan["recipes"]:
        recipe = await fetch_recipe_by_id(recipe_id)
        if recipe:
            recipe_details.append(recipe)
    
    # Prepare response
    response = {
        "id": str(created_meal_plan["_id"]),
        "name": created_meal_plan["name"],
        "recipes": recipe_details,
        "days": created_meal_plan["days"],
        "created_at": created_meal_plan["created_at"],
        "dietary_preferences": created_meal_plan["dietary_preferences"],
    }
    
    return response

@app.get("/meal-plans/{meal_plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(meal_plan_id: str, db=Depends(get_database)):
    if not ObjectId.is_valid(meal_plan_id):
        raise HTTPException(status_code=400, detail="Invalid meal plan ID format")
    
    meal_plan = await db.meal_plans.find_one({"_id": ObjectId(meal_plan_id)})
    if meal_plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    # Fetch full recipe details for response
    recipe_details = []
    for recipe_id in meal_plan["recipes"]:
        recipe = await fetch_recipe_by_id(recipe_id)
        if recipe:
            recipe_details.append(recipe)
    
    # Prepare response
    response = {
        "id": str(meal_plan["_id"]),
        "name": meal_plan["name"],
        "recipes": recipe_details,
        "days": meal_plan["days"],
        "created_at": meal_plan.get("created_at"),
        "dietary_preferences": meal_plan.get("dietary_preferences", []),
    }
    
    return response

@app.get("/meal-plans", response_model=List[MealPlan])
async def get_meal_plans(user_id: Optional[str] = None, db=Depends(get_database)):
    query = {}
    if user_id:
        query["user_id"] = user_id
    
    meal_plans = await db.meal_plans.find(query).to_list(100)
    return meal_plans

@app.delete("/meal-plans/{meal_plan_id}")
async def delete_meal_plan(meal_plan_id: str, db=Depends(get_database)):
    if not ObjectId.is_valid(meal_plan_id):
        raise HTTPException(status_code=400, detail="Invalid meal plan ID format")
    
    result = await db.meal_plans.delete_one({"_id": ObjectId(meal_plan_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    return {"message": "Meal plan deleted successfully"} 