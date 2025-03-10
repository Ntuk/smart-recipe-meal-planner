from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Recipe Service API", description="API for managing recipes")

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

class RecipeBase(BaseModel):
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

class RecipeCreate(RecipeBase):
    pass

class Recipe(RecipeBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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

# Routes
@app.get("/")
async def root():
    return {"message": "Recipe Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/recipes", response_model=Recipe)
async def create_recipe(recipe: RecipeCreate, db=Depends(get_database)):
    recipe_dict = recipe.dict()
    result = await db.recipes.insert_one(recipe_dict)
    created_recipe = await db.recipes.find_one({"_id": result.inserted_id})
    return created_recipe

@app.get("/recipes", response_model=List[Recipe])
async def get_recipes(
    ingredients: Optional[str] = None,
    tags: Optional[str] = None,
    cuisine: Optional[str] = None,
    db=Depends(get_database)
):
    query = {}
    
    if ingredients:
        ingredient_list = ingredients.split(',')
        query["ingredients"] = {"$in": ingredient_list}
    
    if tags:
        tag_list = tags.split(',')
        query["tags"] = {"$in": tag_list}
    
    if cuisine:
        query["cuisine"] = cuisine
    
    recipes = await db.recipes.find(query).to_list(100)
    return recipes

@app.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str, db=Depends(get_database)):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID format")
    
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe

@app.put("/recipes/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: str, recipe: RecipeCreate, db=Depends(get_database)):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID format")
    
    recipe_dict = recipe.dict()
    
    result = await db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$set": recipe_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    updated_recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    return updated_recipe

@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str, db=Depends(get_database)):
    if not ObjectId.is_valid(recipe_id):
        raise HTTPException(status_code=400, detail="Invalid recipe ID format")
    
    result = await db.recipes.delete_one({"_id": ObjectId(recipe_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return {"message": "Recipe deleted successfully"} 