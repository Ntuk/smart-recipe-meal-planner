from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
from bson import ObjectId
import uuid
import os

logger = logging.getLogger(__name__)
router = APIRouter()
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

# Environment variables
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://recipe-service:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

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

# Routes
@router.get("/")
async def root():
    return {"message": "Meal Planning Service API"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/", response_model=MealPlan, status_code=status.HTTP_201_CREATED)
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
        return meal_plan_data
    except Exception as e:
        logger.error(f"Error creating meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating meal plan"
        )

@router.get("/", response_model=List[MealPlan])
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
        return meal_plans
    except Exception as e:
        logger.error(f"Error fetching meal plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching meal plans"
        )

@router.get("/{meal_plan_id}", response_model=MealPlan)
async def get_meal_plan(meal_plan_id: str, current_user: dict = Depends(get_current_user)):
    try:
        meal_plan = await app.mongodb.meal_plans.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        return meal_plan
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error fetching meal plan: {str(e)}")
        raise e

@router.put("/{meal_plan_id}", response_model=MealPlan)
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
        return updated_meal_plan
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error updating meal plan: {str(e)}")
        raise e

@router.delete("/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(meal_plan_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # Check if meal plan exists and belongs to user
        meal_plan = await app.mongodb.meal_plans.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        # Delete meal plan
        await app.mongodb.meal_plans.delete_one({"id": meal_plan_id})
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error deleting meal plan: {str(e)}")
        raise e 