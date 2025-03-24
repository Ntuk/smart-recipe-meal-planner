from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from datetime import datetime, date
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, root_validator, model_validator
import logging
from bson import ObjectId
import uuid
import os
import random
import json
import copy
import traceback

print("**************** MEAL PLANS ROUTER MODULE LOADED ****************")

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

# Add a custom generic type for ingredients to handle both string and dict types
class IngredientType(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None

# Update the RecipeRef model to handle both types of ingredients
class RecipeRef(BaseModel):
    id: str
    name: str
    prep_time: int
    cook_time: int
    servings: int
    image_url: Optional[str] = None
    ingredients: List[Any] = []  # Can be string or dict

    class Config:
        from_attributes = True
        json_encoders = {
            ObjectId: str
        }
        arbitrary_types_allowed = True
        
    @model_validator(mode='after')
    def normalize_ingredients(self):
        """Convert all ingredients to string format during validation"""
        normalized = []
        for ingredient in self.ingredients:
            if isinstance(ingredient, dict):
                # Extract name from dict
                normalized.append(ingredient.get('name', 'Unknown ingredient'))
            else:
                # Already a string or other primitive
                normalized.append(str(ingredient))
        self.ingredients = normalized
        return self

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
                        # Standardize ingredient format - always convert to string list
                        ingredients=[
                            ingredient.get('name', ingredient) if isinstance(ingredient, dict) else ingredient
                            for ingredient in recipe.get('ingredients', [])
                        ]
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
        
        # Standardize ingredient format in all meal plans
        standardized_meal_plans = [standardize_meal_plan_ingredients(plan) for plan in meal_plans]
        
        return standardized_meal_plans
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
        
        # Standardize ingredient format before returning
        return standardize_meal_plan_ingredients(meal_plan)
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
    """
    Update a meal plan
    """
    try:
        logger.info(f"Received update data: {json.dumps(meal_plan_update, default=str)}")
        
        # Get the collection
        if not hasattr(request.app.state, 'db'):
            logger.error("Database not initialized in app state")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not initialized"
            )
            
        db = request.app.state.db
        collection = db["meal_plans"]
        
        # Get the existing meal plan
        existing_meal_plan = await collection.find_one({"id": meal_plan_id})
        if not existing_meal_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan not found"
            )
        
        # Create a deep copy of the existing meal plan to avoid modifying the original
        updated_meal_plan = copy.deepcopy(existing_meal_plan)
        
        # Extract the update data, check if it's using $set format from frontend
        if "$set" in meal_plan_update:
            update_data = meal_plan_update["$set"]
            logger.info(f"Extracted update data from $set: {json.dumps(update_data, default=str)}")
        else:
            update_data = meal_plan_update
        
        # Apply updates to our copy
        for key, value in update_data.items():
            # Update the field in our updated_meal_plan copy
            updated_meal_plan[key] = value
            print(f"Updated field '{key}' in meal plan")
            
            if key == "days":
                print(f"DAYS UPDATE FOUND: {len(value)} days")
                # Debug log to verify the recipes have been added
                for day_index, day in enumerate(value):
                    print(f"DAY {day_index + 1}: {day.get('date')}")
                    for meal_index, meal in enumerate(day.get("meals", [])):
                        recipes = meal.get("recipes", [])
                        print(f"  MEAL {meal_index + 1}: {meal.get('name')} - {len(recipes)} recipes")
                        for recipe_index, recipe in enumerate(recipes):
                            print(f"    RECIPE {recipe_index + 1}: {recipe.get('name', 'unnamed')}")
        
        # Remove the _id field before updating (MongoDB will handle this)
        if "_id" in updated_meal_plan:
            original_id = updated_meal_plan["_id"]
            del updated_meal_plan["_id"]
        else:
            original_id = None
            
        # Always update the 'updated_at' field
        updated_meal_plan["updated_at"] = datetime.utcnow()
        logger.info(f"Final update data: {json.dumps({'updated_at': updated_meal_plan['updated_at']}, default=str)}")
        
        print(f"REPLACING DOCUMENT with updated version: {json.dumps(updated_meal_plan, default=str)}")
        
        # Replace the entire document with our updated version
        result = await collection.replace_one(
            {"id": meal_plan_id}, 
            updated_meal_plan
        )
        
        print(f"REPLACE RESULT: matched={result.matched_count}, modified={result.modified_count}")
        
        if result.matched_count == 0:
            print(f"ERROR: No document matched the query for meal plan ID: {meal_plan_id}")
            print(f"QUERY USED: {{\"id\": \"{meal_plan_id}\"}}")
            print(f"ALL DOCUMENT KEYS: {list(updated_meal_plan.keys())}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meal plan {meal_plan_id} not found during update"
            )
        
        # Get the updated document to return
        updated_doc = await collection.find_one({"id": meal_plan_id})
        if not updated_doc:
            print("ERROR: Failed to retrieve updated document")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated document"
            )
        
        # Log the full document for debug purposes
        print(f"UPDATED DOCUMENT: {json.dumps(updated_doc, default=str)}")
        
        # Verify recipes were actually saved
        recipe_count = 0
        for day in updated_doc.get("days", []):
            for meal in day.get("meals", []):
                recipe_count += len(meal.get("recipes", []))
        
        print(f"Total recipes in updated document: {recipe_count}")
        
        return updated_doc
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log and raise other exceptions
        logger.error(f"Error updating meal plan: {str(e)}")
        traceback.print_exc()
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

# Add a function to standardize ingredients format in meal plans when returning from database
def standardize_meal_plan_ingredients(meal_plan_data):
    """Standardize ingredient format across all recipes in a meal plan"""
    if not meal_plan_data:
        return meal_plan_data
    
    # Deep copy to avoid modifying the original
    meal_plan = copy.deepcopy(meal_plan_data)
    
    # Process each day, meal, recipe
    if "days" in meal_plan:
        for day in meal_plan["days"]:
            if "meals" in day:
                for meal in day["meals"]:
                    if "recipes" in meal:
                        for recipe in meal["recipes"]:
                            if "ingredients" in recipe:
                                # Standardize ingredients to string list
                                recipe["ingredients"] = [
                                    ingredient.get('name', ingredient) if isinstance(ingredient, dict) else ingredient
                                    for ingredient in recipe["ingredients"]
                                ] 
    return meal_plan 