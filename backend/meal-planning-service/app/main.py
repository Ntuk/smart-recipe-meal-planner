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
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "recipe_db")
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://localhost:8001")

# MongoDB client
client = None

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

@app.post("/meal-plans", response_model=MealPlan, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    meal_plan: MealPlanCreate,
    current_user: dict = Depends(get_current_user)
):
    now = datetime.utcnow()
    meal_plan_id = str(uuid.uuid4())
    
    # Convert days to dict for MongoDB
    days_data = []
    for day in meal_plan.days:
        day_dict = day.dict()
        day_dict["date"] = day.date.isoformat()
        days_data.append(day_dict)
    
    meal_plan_data = meal_plan.dict(exclude={"days"})
    meal_plan_data.update({
        "id": meal_plan_id,
        "user_id": current_user["id"],
        "days": days_data,
        "start_date": meal_plan.start_date.isoformat(),
        "end_date": meal_plan.end_date.isoformat(),
        "created_at": now,
        "updated_at": now
    })
    
    await get_database().meal_plans.insert_one(meal_plan_data)
    
    # Convert dates back to date objects for response
    meal_plan_data["start_date"] = meal_plan.start_date
    meal_plan_data["end_date"] = meal_plan.end_date
    for day in meal_plan_data["days"]:
        day["date"] = date.fromisoformat(day["date"])
    
    return meal_plan_data

@app.get("/meal-plans", response_model=List[MealPlan])
async def get_meal_plans(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    
    # Add date filters if provided
    if start_date:
        query["start_date"] = {"$gte": start_date.isoformat()}
    
    if end_date:
        query["end_date"] = {"$lte": end_date.isoformat()}
    
    meal_plans = []
    cursor = get_database().meal_plans.find(query).sort("start_date", -1)
    async for document in cursor:
        # Convert date strings to date objects
        document["start_date"] = date.fromisoformat(document["start_date"])
        document["end_date"] = date.fromisoformat(document["end_date"])
        for day in document["days"]:
            day["date"] = date.fromisoformat(day["date"])
        
        meal_plans.append(document)
    
    return meal_plans

@app.get("/meal-plans/{meal_plan_id}", response_model=MealPlan)
async def get_meal_plan(meal_plan_id: str, current_user: dict = Depends(get_current_user)):
    meal_plan = await get_database().meal_plans.find_one({"id": meal_plan_id, "user_id": current_user["id"]})
    
    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal plan with ID {meal_plan_id} not found"
        )
    
    # Convert date strings to date objects
    meal_plan["start_date"] = date.fromisoformat(meal_plan["start_date"])
    meal_plan["end_date"] = date.fromisoformat(meal_plan["end_date"])
    for day in meal_plan["days"]:
        day["date"] = date.fromisoformat(day["date"])
    
    return meal_plan

@app.put("/meal-plans/{meal_plan_id}", response_model=MealPlan)
async def update_meal_plan(
    meal_plan_id: str,
    meal_plan_update: MealPlanUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Check if meal plan exists
    meal_plan = await get_database().meal_plans.find_one({"id": meal_plan_id, "user_id": current_user["id"]})
    
    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal plan with ID {meal_plan_id} not found"
        )
    
    # Update meal plan
    update_data = meal_plan_update.dict(exclude_unset=True)
    
    # Convert days to dict for MongoDB if provided
    if "days" in update_data:
        days_data = []
        for day in meal_plan_update.days:
            day_dict = day.dict()
            day_dict["date"] = day.date.isoformat()
            days_data.append(day_dict)
        update_data["days"] = days_data
    
    update_data["updated_at"] = datetime.utcnow()
    
    await get_database().meal_plans.update_one(
        {"id": meal_plan_id},
        {"$set": update_data}
    )
    
    # Get updated meal plan
    updated_meal_plan = await get_database().meal_plans.find_one({"id": meal_plan_id})
    
    # Convert date strings to date objects
    updated_meal_plan["start_date"] = date.fromisoformat(updated_meal_plan["start_date"])
    updated_meal_plan["end_date"] = date.fromisoformat(updated_meal_plan["end_date"])
    for day in updated_meal_plan["days"]:
        day["date"] = date.fromisoformat(day["date"])
    
    return updated_meal_plan

@app.delete("/meal-plans/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(meal_plan_id: str, current_user: dict = Depends(get_current_user)):
    # Check if meal plan exists
    meal_plan = await get_database().meal_plans.find_one({"id": meal_plan_id, "user_id": current_user["id"]})
    
    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meal plan with ID {meal_plan_id} not found"
        )
    
    # Delete meal plan
    await get_database().meal_plans.delete_one({"id": meal_plan_id})
    
    return None 