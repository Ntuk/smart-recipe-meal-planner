from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
from bson import ObjectId
import uuid
import os
import random

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
    id: str
    name: str
    description: Optional[str] = None
    ingredients: List[str]
    steps: List[str]
    prep_time: int
    cook_time: int
    servings: int
    tags: List[str] = []
    cuisine: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[dict] = None

    class Config:
        from_attributes = True
        json_encoders = {
            ObjectId: str
        }
        arbitrary_types_allowed = True

class RecipeRef(BaseModel):
    id: str
    name: str
    prep_time: int
    cook_time: int
    servings: int
    image_url: Optional[str] = None
    ingredients: List[str] = []

    class Config:
        from_attributes = True
        json_encoders = {
            ObjectId: str
        }
        arbitrary_types_allowed = True

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
    dietary_preferences: Optional[List[str]] = []
    available_ingredients: Optional[List[str]] = []

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
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://recipe-service:8001")
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
@router.get("/api-info")
async def root():
    return {"message": "Meal Planning Service API"}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

async def select_recipes(
    dietary_preferences: List[str],
    available_ingredients: List[str],
    token: str
) -> List[RecipeRef]:
    """Select recipes based on dietary preferences and available ingredients"""
    try:
        async with httpx.AsyncClient() as client:
            # Build query parameters
            params = {}
            if dietary_preferences:
                params['tags'] = dietary_preferences
            if available_ingredients:
                params['ingredients'] = available_ingredients
            
            # Get recipes from recipe service
            response = await client.get(
                f"{RECIPE_SERVICE_URL}/recipes",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                recipes = response.json()
                # Convert recipes to RecipeRef format
                return [
                    RecipeRef(
                        id=recipe['id'],
                        name=recipe['name'],
                        prep_time=recipe['prep_time'],
                        cook_time=recipe['cook_time'],
                        servings=recipe['servings'],
                        image_url=recipe.get('image_url'),
                        ingredients=[ingredient['name'] for ingredient in recipe.get('ingredients', [])]
                    )
                    for recipe in recipes
                ]
            else:
                logger.error(f"Failed to get recipes: {response.status_code} - {response.text}")
                return []
    except Exception as e:
        logger.error(f"Error selecting recipes: {str(e)}")
        return []

@router.post("/", response_model=MealPlan, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    request: Request,
    meal_plan: MealPlanCreate,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        now = datetime.utcnow()
        meal_plan_id = str(uuid.uuid4())
        
        # Select recipes based on preferences and ingredients
        recipes = await select_recipes(
            meal_plan.dietary_preferences or [],
            meal_plan.available_ingredients or [],
            credentials.credentials
        )
        
        # Convert days to dict for MongoDB and assign recipes
        days_data = []
        for day in meal_plan.days:
            day_dict = day.dict()
            day_dict["date"] = day.date.isoformat()
            
            # Assign recipes to each meal
            for meal in day_dict["meals"]:
                # Select 1-2 recipes per meal randomly from the available recipes
                num_recipes = random.randint(1, 2)
                if recipes:
                    meal["recipes"] = random.sample(recipes, min(num_recipes, len(recipes)))
                else:
                    meal["recipes"] = []
            
            days_data.append(day_dict)
        
        # Create meal plan data without dietary preferences and available ingredients
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
        
        # Get database from request state
        if not hasattr(request.app.state, 'db'):
            logger.error("Database not initialized in app state")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not initialized"
            )
        
        db = request.app.state.db
        logger.info("Database connection retrieved successfully")
        
        # Insert meal plan into database
        try:
            collection = db["meal_plans"]
            # Convert meal_plan_data to a format that Motor can handle
            # This avoids comparison issues with MongoDB objects
            result = await collection.insert_one(meal_plan_data)
            
            if not result.inserted_id:
                logger.error("Insert operation did not return a valid result")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to insert meal plan"
                )
            
            logger.info(f"Successfully inserted meal plan with ID: {result.inserted_id}")
            return meal_plan_data
            
        except Exception as e:
            logger.error(f"Error inserting meal plan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inserting meal plan: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating meal plan: {str(e)}"
        )

@router.get("/", response_model=List[MealPlan])
async def get_meal_plans(
    request: Request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"GET meal plans request received for user: {current_user['id']}")
        if not hasattr(request.app.state, 'db'):
            logger.error("Database not initialized in app state")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not initialized"
            )
            
        db = request.app.state.db
        query = {"user_id": current_user["id"]}
        
        if start_date:
            query["start_date"] = {"$gte": start_date.isoformat()}
        if end_date:
            query["end_date"] = {"$lte": end_date.isoformat()}
        
        logger.info(f"Querying meal plans with: {query}")
        collection = db["meal_plans"]
        cursor = collection.find(query)
        meal_plans = await cursor.to_list(length=None)
        logger.info(f"Found {len(meal_plans)} meal plans: {meal_plans}")
        return meal_plans
    except Exception as e:
        logger.error(f"Error fetching meal plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching meal plans: {str(e)}"
        )

@router.get("/all", response_model=List[MealPlan])
async def get_all_meal_plans(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"GET all meal plans request received for user: {current_user['id']}")
        if not hasattr(request.app.state, 'db'):
            logger.error("Database not initialized in app state")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not initialized"
            )
            
        db = request.app.state.db
        query = {"user_id": current_user["id"]}
        
        logger.info(f"Querying all meal plans with: {query}")
        collection = db["meal_plans"]
        cursor = collection.find(query)
        meal_plans = await cursor.to_list(length=None)
        logger.info(f"Found {len(meal_plans)} meal plans: {meal_plans}")
        return meal_plans
    except Exception as e:
        logger.error(f"Error fetching all meal plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching all meal plans: {str(e)}"
        )

@router.get("/{meal_plan_id}", response_model=MealPlan)
async def get_meal_plan(
    request: Request,
    meal_plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        if not hasattr(request.app.state, 'db'):
            logger.error("Database not initialized in app state")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not initialized"
            )
            
        db = request.app.state.db
        collection = db["meal_plans"]
        meal_plan = await collection.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        return meal_plan
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching meal plan: {str(e)}"
        )

@router.put("/{meal_plan_id}", response_model=MealPlan)
async def update_meal_plan(
    request: Request,
    meal_plan_id: str,
    meal_plan_update: dict,
    current_user: dict = Depends(get_current_user)
):
    try:
        if not hasattr(request.app.state, 'db'):
            logger.error("Database not initialized in app state")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not initialized"
            )
            
        db = request.app.state.db
        collection = db["meal_plans"]
        
        # Check if meal plan exists and belongs to user
        meal_plan = await collection.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        # Process the update data
        update_data = {}
        logger.info(f"Received update data: {meal_plan_update}")
        
        if "days" in meal_plan_update:
            days_data = []
            for day in meal_plan_update["days"]:
                try:
                    # Convert date string to date object
                    if "date" in day:
                        day["date"] = datetime.strptime(day["date"], "%Y-%m-%d").date()
                    
                    # Process meals
                    if "meals" in day:
                        processed_meals = []
                        for meal in day["meals"]:
                            # Process recipes
                            if "recipes" in meal:
                                processed_recipes = []
                                for recipe in meal["recipes"]:
                                    # Ensure numeric fields
                                    recipe["prep_time"] = int(recipe.get("prep_time", 0))
                                    recipe["cook_time"] = int(recipe.get("cook_time", 0))
                                    recipe["servings"] = int(recipe.get("servings", 4))
                                    
                                    processed_recipes.append(recipe)
                                meal["recipes"] = processed_recipes
                            
                            processed_meals.append(meal)
                        day["meals"] = processed_meals
                    
                    days_data.append(day)
                except Exception as e:
                    logger.error(f"Error processing day data: {str(e)}")
                    logger.error(f"Problematic day data: {day}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Error processing day data: {str(e)}"
                    )
            update_data["days"] = days_data
        
        update_data["updated_at"] = datetime.utcnow()
        logger.info(f"Final update data: {update_data}")
        
        # Update the meal plan
        await collection.update_one(
            {"id": meal_plan_id},
            {"$set": update_data}
        )
        
        # Fetch and return the updated meal plan
        updated_meal_plan = await collection.find_one({"id": meal_plan_id})
        if not updated_meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found after update"
            )
        return updated_meal_plan
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating meal plan: {str(e)}"
        )

@router.delete("/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    request: Request,
    meal_plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        if not hasattr(request.app.state, 'db'):
            logger.error("Database not initialized in app state")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not initialized"
            )
            
        db = request.app.state.db
        collection = db["meal_plans"]
        
        # Check if meal plan exists and belongs to user
        meal_plan = await collection.find_one({
            "id": meal_plan_id,
            "user_id": current_user["id"]
        })
        
        if not meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found"
            )
        
        # Delete meal plan
        await collection.delete_one({"id": meal_plan_id})
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting meal plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting meal plan: {str(e)}"
        ) 