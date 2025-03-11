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

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@localhost:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")

# Initialize FastAPI app
app = FastAPI(title="Recipe Service", description="Recipe management service for Smart Recipe & Meal Planner")

# Security
security = HTTPBearer()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    
    # Create indexes for recipes collection
    await app.mongodb["recipes"].create_index("name")
    await app.mongodb["recipes"].create_index("tags")
    await app.mongodb["recipes"].create_index("cuisine")

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
    
    return recipe_data

@app.get("/recipes", response_model=List[Recipe])
async def get_recipes(
    ingredients: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    cuisine: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    
    # Add filters if provided
    if ingredients:
        query["ingredients.name"] = {"$all": ingredients}
    
    if tags:
        query["tags"] = {"$all": tags}
    
    if cuisine:
        query["cuisine"] = cuisine
    
    # Get recipes
    recipes = []
    cursor = app.mongodb["recipes"].find(query)
    async for document in cursor:
        recipes.append(document)
    
    return recipes

@app.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)):
    recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found"
        )
    
    return recipe

@app.put("/recipes/{recipe_id}", response_model=Recipe)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Check if recipe exists
    recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found"
        )
    
    # Check if user owns the recipe
    if recipe["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this recipe"
        )
    
    # Update recipe
    update_data = recipe_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await app.mongodb["recipes"].update_one(
        {"id": recipe_id},
        {"$set": update_data}
    )
    
    # Get updated recipe
    updated_recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
    
    return updated_recipe

@app.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)):
    # Check if recipe exists
    recipe = await app.mongodb["recipes"].find_one({"id": recipe_id})
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with ID {recipe_id} not found"
        )
    
    # Check if user owns the recipe
    if recipe["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this recipe"
        )
    
    # Delete recipe
    await app.mongodb["recipes"].delete_one({"id": recipe_id})
    
    return None

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 