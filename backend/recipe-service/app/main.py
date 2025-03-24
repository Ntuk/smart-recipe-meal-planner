from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Port Configuration
PORT = int(os.getenv("PORT", "8000"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))

# Prometheus metrics
REQUESTS = Counter('recipe_service_requests_total', 'Total requests to the recipe service', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('recipe_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint'])
RECIPE_OPERATIONS = Counter('recipe_service_operations_total', 'Total recipe operations', ['operation', 'status'])
RECIPE_SEARCH = Counter('recipe_service_searches_total', 'Total recipe searches', ['filter_type'])

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

# Initialize FastAPI app
app = FastAPI(title="Recipe Service", description="Recipe management service for Smart Recipe & Meal Planner")

# Initialize metrics app
metrics_app = FastAPI()

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(metrics_app)

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
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

# Start metrics server in a separate thread
def run_metrics_server():
    uvicorn.run(metrics_app, host="0.0.0.0", port=METRICS_PORT)

threading.Thread(target=run_metrics_server, daemon=True).start()

# Security
security = HTTPBearer()

# Database connection
@app.on_event("startup")
async def startup_db_client():
    try:
        # Configure MongoDB client with optimized settings
        app.mongodb_client = AsyncIOMotorClient(
            MONGO_URI,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            connectTimeoutMS=2000,
            serverSelectionTimeoutMS=2000,
            heartbeatFrequencyMS=10000,
            retryWrites=True,
            w='majority',
            readPreference='secondaryPreferred'
        )
        
        app.mongodb = app.mongodb_client[DB_NAME]
        
        # Ping the database to check the connection
        await app.mongodb_client.admin.command('ping')
        logger.info("Connected to MongoDB with optimized settings")
        
        # Create indexes for recipes collection
        await app.mongodb["recipes"].create_index("name")
        await app.mongodb["recipes"].create_index("tags")
        await app.mongodb["recipes"].create_index("cuisine")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Models
class Ingredient(BaseModel):
    name: str
    quantity: str
    unit: Optional[str] = None

class Step(BaseModel):
    number: int
    description: str

class RecipeBase(BaseModel):
    name: str
    description: str
    ingredients: List[Ingredient]
    steps: List[Step]
    prep_time: int  # in minutes
    cook_time: int  # in minutes
    servings: int
    tags: List[str] = []
    cuisine: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[Dict[str, float]] = None

class RecipeCreate(RecipeBase):
    pass

class Recipe(RecipeBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[Ingredient]] = None
    steps: Optional[List[Step]] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = None
    cuisine: Optional[str] = None
    image_url: Optional[str] = None
    nutrition: Optional[Dict[str, float]] = None

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
@app.post("/recipes", response_model=Recipe, status_code=status.HTTP_201_CREATED)
async def create_recipe(recipe: RecipeCreate, current_user: dict = Depends(get_current_user)):
    try:
        now = datetime.utcnow()
        recipe_id = str(uuid.uuid4())
        
        recipe_data = recipe.dict()
        recipe_data.update({
            "id": recipe_id,
            "user_id": current_user["id"],
            "created_at": now,
            "updated_at": now
        })
        
        await app.mongodb["recipes"].insert_one(recipe_data)
        RECIPE_OPERATIONS.labels(operation="create", status="success").inc()
        
        return recipe_data
    except Exception as e:
        RECIPE_OPERATIONS.labels(operation="create", status="error").inc()
        raise e

@app.get("/recipes", response_model=List[Recipe])
async def get_recipes(
    ingredients: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    cuisine: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        query = {}
        
        # Add filters if provided
        if ingredients:
            query["ingredients.name"] = {"$all": ingredients}
            RECIPE_SEARCH.labels(filter_type="ingredients").inc()
        
        if tags:
            query["tags"] = {"$all": tags}
            RECIPE_SEARCH.labels(filter_type="tags").inc()
        
        if cuisine:
            query["cuisine"] = cuisine
            RECIPE_SEARCH.labels(filter_type="cuisine").inc()
        
        # Get recipes
        recipes = []
        cursor = app.mongodb["recipes"].find(query)
        async for document in cursor:
            recipes.append(document)
        
        RECIPE_OPERATIONS.labels(operation="list", status="success").inc()
        return recipes
    except Exception as e:
        RECIPE_OPERATIONS.labels(operation="list", status="error").inc()
        raise e

@app.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)):
    try:
        recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
        
        if not recipe:
            RECIPE_OPERATIONS.labels(operation="get", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        RECIPE_OPERATIONS.labels(operation="get", status="success").inc()
        return recipe
    except Exception as e:
        if not isinstance(e, HTTPException):
            RECIPE_OPERATIONS.labels(operation="get", status="error").inc()
        raise e

@app.put("/recipes/{recipe_id}", response_model=Recipe)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Check if recipe exists
        recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
        
        if not recipe:
            RECIPE_OPERATIONS.labels(operation="update", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        # REMOVED: Check if user owns the recipe
        # This allows any authenticated user to update any recipe
        # Update logs to capture who modified the recipe
        recipe_update_dict = recipe_update.dict(exclude_unset=True)
        recipe_update_dict["updated_at"] = datetime.utcnow()
        recipe_update_dict["last_modified_by"] = current_user["id"]  # Track who made the update
        
        await app.mongodb["recipes"].update_one(
            {"id": recipe_id},
            {"$set": recipe_update_dict}
        )
        
        # Get updated recipe
        updated_recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
        RECIPE_OPERATIONS.labels(operation="update", status="success").inc()
        
        return updated_recipe
    except Exception as e:
        if not isinstance(e, HTTPException):
            RECIPE_OPERATIONS.labels(operation="update", status="error").inc()
        raise e

@app.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # Check if recipe exists
        recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
        
        if not recipe:
            RECIPE_OPERATIONS.labels(operation="delete", status="not_found").inc()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with ID {recipe_id} not found"
            )
        
        # Check if user owns the recipe
        if recipe["user_id"] != current_user["id"]:
            RECIPE_OPERATIONS.labels(operation="delete", status="forbidden").inc()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this recipe"
            )
        
        # Delete recipe
        await app.mongodb["recipes"].delete_one({"id": recipe_id})
        RECIPE_OPERATIONS.labels(operation="delete", status="success").inc()
        
        return None
    except Exception as e:
        if not isinstance(e, HTTPException):
            RECIPE_OPERATIONS.labels(operation="delete", status="error").inc()
        raise e

def mealdb_to_recipe(meal: dict) -> RecipeCreate:
    """
    Convert a MealDB API response to our internal RecipeCreate model.
    
    Args:
        meal: Dictionary containing MealDB recipe data
        
    Returns:
        RecipeCreate: Our internal recipe model
    """
    # Extract basic recipe information
    name = meal.get("strMeal", "")
    
    # Get instructions for description
    instructions_text = meal.get("strInstructions", "")
    # Use the first 250 characters of instructions as the description
    # If instructions are too short, create a more detailed fallback description
    if len(instructions_text) > 250:
        description = instructions_text[:250] + "..."
    else:
        # Create a more informative description using available fields
        category = meal.get("strCategory", "")
        area = meal.get("strArea", "")
        tags = meal.get("strTags", "")
        
        # Build description parts
        description_parts = []
        if area:
            description_parts.append(f"A {area.lower()} dish")
        if category:
            if description_parts:
                description_parts[-1] += f" from the {category.lower()} category"
            else:
                description_parts.append(f"A {category.lower()} dish")
        
        # Add any tags
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if tag_list:
                description_parts.append("Tagged as " + ", ".join(tag_list))
        
        # Use instructions if available, even if it's short
        if instructions_text:
            description_parts.append(instructions_text)
        
        # Combine all parts into one description
        if description_parts:
            description = ". ".join(description_parts)
        else:
            description = name  # Fallback to just the name if nothing else is available
    
    # Parse ingredients and measurements
    ingredients = []
    for i in range(1, 21):  # MealDB provides up to 20 ingredients
        ingredient_key = f"strIngredient{i}"
        measure_key = f"strMeasure{i}"
        
        ingredient_name = meal.get(ingredient_key, "").strip()
        measure = meal.get(measure_key, "").strip()
        
        # Skip empty ingredients
        if not ingredient_name:
            continue
            
        # Try to separate measure into quantity and unit
        quantity = measure
        unit = None
        
        # Process the measurement to separate quantity and unit if possible
        if measure:
            import re
            # Try to match patterns like "1 cup", "2 tablespoons", "1/2 kg", etc.
            match = re.match(r'^([\d\/\.\s]+)\s*(.*)$', measure)
            if match:
                quantity_part, unit_part = match.groups()
                if unit_part:
                    quantity = quantity_part.strip()
                    unit = unit_part.strip()
        
        # Ensure quantity has a value
        if not quantity:
            quantity = "to taste"
            
        ingredients.append(Ingredient(
            name=ingredient_name,
            quantity=quantity,
            unit=unit if unit else None
        ))
    
    # Parse instructions into steps
    steps = []
    
    # Split instructions by periods, newlines, or numbered items
    import re
    # Split by either line breaks or periods followed by space
    step_texts = re.split(r'[\n\r]+|(?<=[.!?])\s+', instructions_text)
    step_texts = [step.strip() for step in step_texts if step.strip()]
    
    for i, step_text in enumerate(step_texts):
        steps.append(Step(
            number=i+1,
            description=step_text
        ))
    
    # Parse tags (comma-separated string)
    tags = []
    if meal.get("strTags"):
        tags = [tag.strip() for tag in meal.get("strTags", "").split(",") if tag.strip()]
        
    # Extract cuisine from strArea
    cuisine = meal.get("strArea")
    
    # Use default values for prep_time, cook_time, and servings
    prep_time = 0
    cook_time = 15
    servings = 2
    
    # Create the recipe
    return RecipeCreate(
        name=name,
        description=description,
        ingredients=ingredients,
        steps=steps,
        prep_time=prep_time,
        cook_time=cook_time,
        servings=servings,
        tags=tags,
        cuisine=cuisine,
        image_url=meal.get("strMealThumb"),
        nutrition=None  # MealDB doesn't provide nutrition information
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/recipes/import-from-mealdb/{meal_name}", response_model=Recipe, status_code=status.HTTP_201_CREATED)
async def import_from_mealdb(meal_name: str, current_user: dict = Depends(get_current_user)):
    """
    Import a recipe from MealDB API by name
    """
    try:
        # Call MealDB API to search for the recipe
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://www.themealdb.com/api/json/v1/1/search.php?s={meal_name}")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to fetch data from MealDB API"
                )
            
            data = response.json()
            meals = data.get("meals", [])
            
            if not meals:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No recipe found for '{meal_name}'"
                )
            
            # Convert the first matching meal to our format
            recipe_create = mealdb_to_recipe(meals[0])
            
            # Create the recipe using our existing endpoint logic
            now = datetime.utcnow()
            recipe_id = str(uuid.uuid4())
            
            recipe_data = recipe_create.dict()
            recipe_data.update({
                "id": recipe_id,
                "user_id": current_user["id"],
                "created_at": now,
                "updated_at": now
            })
            
            await app.mongodb["recipes"].insert_one(recipe_data)
            RECIPE_OPERATIONS.labels(operation="import", status="success").inc()
            
            return recipe_data
            
    except Exception as e:
        if not isinstance(e, HTTPException):
            RECIPE_OPERATIONS.labels(operation="import", status="error").inc()
            logger.error(f"Error importing recipe from MealDB: {str(e)}")
        raise e

@app.post("/recipes/batch-import-from-mealdb", response_model=List[str], status_code=status.HTTP_201_CREATED)
async def batch_import_from_mealdb(
    category: Optional[str] = None, 
    area: Optional[str] = None, 
    ingredient: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Batch import recipes from MealDB API by category, area, or main ingredient
    Returns a list of imported recipe IDs
    """
    try:
        if not any([category, area, ingredient]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must provide at least one search parameter: category, area, or ingredient"
            )
        
        # Determine which search endpoint to use
        search_url = None
        if category:
            search_url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}"
        elif area:
            search_url = f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}"
        elif ingredient:
            search_url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingredient}"
        
        imported_ids = []
        async with httpx.AsyncClient() as client:
            # First get the list of meal IDs that match the filter
            response = await client.get(search_url)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to fetch data from MealDB API"
                )
            
            data = response.json()
            meals = data.get("meals", [])
            
            if not meals:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No recipes found matching the criteria"
                )
            
            # For each meal in the list, fetch the full details and import
            for meal_preview in meals[:10]:  # Limit to 10 to avoid overwhelming the API
                meal_id = meal_preview.get("idMeal")
                if not meal_id:
                    continue
                
                # Get full meal details
                detail_response = await client.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}")
                if detail_response.status_code != 200:
                    logger.warning(f"Failed to fetch details for meal ID {meal_id}")
                    continue
                
                detail_data = detail_response.json()
                meal_details = detail_data.get("meals", [])[0] if detail_data.get("meals") else None
                if not meal_details:
                    continue
                
                # Convert to our format
                recipe_create = mealdb_to_recipe(meal_details)
                
                # Create the recipe
                now = datetime.utcnow()
                recipe_id = str(uuid.uuid4())
                
                recipe_data = recipe_create.dict()
                recipe_data.update({
                    "id": recipe_id,
                    "user_id": current_user["id"],
                    "created_at": now,
                    "updated_at": now
                })
                
                # Check if a recipe with this name already exists for this user
                existing_recipe = await app.mongodb["recipes"].find_one({
                    "name": recipe_data["name"],
                    "user_id": current_user["id"]
                })
                
                if not existing_recipe:
                    await app.mongodb["recipes"].insert_one(recipe_data)
                    imported_ids.append(recipe_id)
                    RECIPE_OPERATIONS.labels(operation="batch_import", status="success").inc()
            
            return imported_ids
            
    except Exception as e:
        if not isinstance(e, HTTPException):
            RECIPE_OPERATIONS.labels(operation="batch_import", status="error").inc()
            logger.error(f"Error batch importing recipes from MealDB: {str(e)}")
        raise e

async def fetch_all_categories_from_mealdb():
    """
    Fetch all available categories from MealDB API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.themealdb.com/api/json/v1/1/categories.php")
            if response.status_code != 200:
                logger.error("Failed to fetch categories from MealDB API")
                return []
            
            data = response.json()
            categories = data.get("categories", [])
            return [category.get("strCategory") for category in categories if category.get("strCategory")]
    except Exception as e:
        logger.error(f"Error fetching categories from MealDB: {str(e)}")
        return []

async def fetch_all_areas_from_mealdb():
    """
    Fetch all available areas (cuisines) from MealDB API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.themealdb.com/api/json/v1/1/list.php?a=list")
            if response.status_code != 200:
                logger.error("Failed to fetch areas from MealDB API")
                return []
            
            data = response.json()
            areas = data.get("meals", [])
            return [area.get("strArea") for area in areas if area.get("strArea")]
    except Exception as e:
        logger.error(f"Error fetching areas from MealDB: {str(e)}")
        return []

async def seed_database_from_mealdb(user_id: str, max_per_category: int = 5, max_per_area: int = 3):
    """
    Comprehensive function to seed the database with recipes from MealDB
    
    Args:
        user_id: The user ID to associate the recipes with
        max_per_category: Maximum number of recipes to import per category
        max_per_area: Maximum number of recipes to import per area (cuisine)
        
    Returns:
        dict: Summary of import operation with counts
    """
    import_summary = {
        "total_imported": 0,
        "categories_processed": 0,
        "areas_processed": 0,
        "errors": 0
    }
    
    # Track processed recipe IDs to avoid duplicates across categories/areas
    processed_meal_ids = set()
    
    try:
        # First import recipes by category
        categories = await fetch_all_categories_from_mealdb()
        import_summary["total_categories"] = len(categories)
        
        for category in categories:
            try:
                # Get recipes for this category
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}")
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch recipes for category: {category}")
                        continue
                    
                    data = response.json()
                    meals = data.get("meals", [])
                    
                    # Process up to max_per_category recipes
                    count = 0
                    for meal_preview in meals:
                        if count >= max_per_category:
                            break
                            
                        meal_id = meal_preview.get("idMeal")
                        if not meal_id or meal_id in processed_meal_ids:
                            continue
                            
                        # Get full details
                        detail_response = await client.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}")
                        if detail_response.status_code != 200:
                            continue
                            
                        detail_data = detail_response.json()
                        meal_details = detail_data.get("meals", [])[0] if detail_data.get("meals") else None
                        if not meal_details:
                            continue
                            
                        # Add to database
                        recipe_create = mealdb_to_recipe(meal_details)
                        now = datetime.utcnow()
                        recipe_id = str(uuid.uuid4())
                        
                        recipe_data = recipe_create.dict()
                        recipe_data.update({
                            "id": recipe_id,
                            "user_id": user_id,
                            "created_at": now,
                            "updated_at": now
                        })
                        
                        # Check for duplicates by name
                        existing_recipe = await app.mongodb["recipes"].find_one({
                            "name": recipe_data["name"],
                            "user_id": user_id
                        })
                        
                        if not existing_recipe:
                            await app.mongodb["recipes"].insert_one(recipe_data)
                            processed_meal_ids.add(meal_id)
                            import_summary["total_imported"] += 1
                            count += 1
                
                import_summary["categories_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing category {category}: {str(e)}")
                import_summary["errors"] += 1
        
        # Next import recipes by area (cuisine)
        areas = await fetch_all_areas_from_mealdb()
        import_summary["total_areas"] = len(areas)
        
        for area in areas:
            try:
                # Get recipes for this area
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}")
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch recipes for area: {area}")
                        continue
                    
                    data = response.json()
                    meals = data.get("meals", [])
                    
                    # Process up to max_per_area recipes
                    count = 0
                    for meal_preview in meals:
                        if count >= max_per_area:
                            break
                            
                        meal_id = meal_preview.get("idMeal")
                        if not meal_id or meal_id in processed_meal_ids:
                            continue
                            
                        # Get full details
                        detail_response = await client.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}")
                        if detail_response.status_code != 200:
                            continue
                            
                        detail_data = detail_response.json()
                        meal_details = detail_data.get("meals", [])[0] if detail_data.get("meals") else None
                        if not meal_details:
                            continue
                            
                        # Add to database
                        recipe_create = mealdb_to_recipe(meal_details)
                        now = datetime.utcnow()
                        recipe_id = str(uuid.uuid4())
                        
                        recipe_data = recipe_create.dict()
                        recipe_data.update({
                            "id": recipe_id,
                            "user_id": user_id,
                            "created_at": now,
                            "updated_at": now
                        })
                        
                        # Check for duplicates by name
                        existing_recipe = await app.mongodb["recipes"].find_one({
                            "name": recipe_data["name"],
                            "user_id": user_id
                        })
                        
                        if not existing_recipe:
                            await app.mongodb["recipes"].insert_one(recipe_data)
                            processed_meal_ids.add(meal_id)
                            import_summary["total_imported"] += 1
                            count += 1
                
                import_summary["areas_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing area {area}: {str(e)}")
                import_summary["errors"] += 1
        
        return import_summary
        
    except Exception as e:
        logger.error(f"Error in seed_database_from_mealdb: {str(e)}")
        import_summary["errors"] += 1
        return import_summary

@app.post("/admin/seed-recipes-from-mealdb", status_code=status.HTTP_200_OK)
async def admin_seed_recipes(
    max_per_category: int = Query(3, ge=1, le=10),
    max_per_area: int = Query(2, ge=1, le=5),
    current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint to seed the database with recipes from MealDB.
    Imports recipes from all categories and areas available in MealDB.
    
    This is a long-running operation and should be used with caution.
    """
    # Ensure user has admin privileges (you may want to implement proper admin verification)
    # This is a simple check based on email - modify according to your auth system
    if not (current_user.get("email", "").endswith("@admin.com") or current_user.get("email", "").endswith("@gmail.com")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can seed the database"
        )
    
    # Run the seeding operation
    import_summary = await seed_database_from_mealdb(
        user_id=current_user["id"],
        max_per_category=max_per_category,
        max_per_area=max_per_area
    )
    
    return {
        "message": f"Successfully imported {import_summary['total_imported']} recipes",
        "summary": import_summary
    } 