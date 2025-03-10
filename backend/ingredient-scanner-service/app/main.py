from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
import os
import io
import logging
from PIL import Image
import pytesseract
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Ingredient Scanner Service API", description="API for scanning ingredients from images")

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
class IngredientList(BaseModel):
    ingredients: List[str]

# Common food ingredients for better detection
COMMON_INGREDIENTS = [
    "salt", "pepper", "sugar", "flour", "oil", "butter", "milk", "eggs", "water",
    "chicken", "beef", "pork", "fish", "rice", "pasta", "tomato", "onion", "garlic",
    "carrot", "potato", "cheese", "yogurt", "cream", "lemon", "lime", "vinegar",
    "soy sauce", "olive oil", "vegetable oil", "bread", "honey", "maple syrup",
    "cinnamon", "vanilla", "chocolate", "nuts", "beans", "corn", "peas", "spinach",
    "lettuce", "cabbage", "mushroom", "bell pepper", "chili", "cumin", "oregano",
    "basil", "thyme", "rosemary", "parsley", "cilantro", "ginger", "turmeric"
]

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

# Helper function to extract ingredients from text
def extract_ingredients(text):
    # Convert to lowercase
    text = text.lower()
    
    # Split by common delimiters
    lines = re.split(r'[\n,;]', text)
    
    # Clean up lines
    lines = [line.strip() for line in lines if line.strip()]
    
    # Extract potential ingredients
    potential_ingredients = []
    
    for line in lines:
        # Check if line contains a common ingredient
        for ingredient in COMMON_INGREDIENTS:
            if ingredient in line:
                # Extract the ingredient with some context
                match = re.search(r'(\d+\s*[a-zA-Z]*\s*' + ingredient + r'|\b' + ingredient + r'\b)', line)
                if match:
                    potential_ingredients.append(match.group(0).strip())
                else:
                    potential_ingredients.append(ingredient)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ingredients = []
    for item in potential_ingredients:
        if item not in seen:
            seen.add(item)
            unique_ingredients.append(item)
    
    return unique_ingredients

# Routes
@app.get("/")
async def root():
    return {"message": "Ingredient Scanner Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/scan", response_model=IngredientList)
async def scan_ingredients(file: UploadFile = File(...)):
    # Check if the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read the image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Extract text from image using OCR
        text = pytesseract.image_to_string(image)
        
        # Extract ingredients from text
        ingredients = extract_ingredients(text)
        
        # If no ingredients found, return a helpful message
        if not ingredients:
            return {"ingredients": ["No ingredients detected. Try a clearer image or manually enter ingredients."]}
        
        return {"ingredients": ingredients}
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/manual-input", response_model=IngredientList)
async def manual_input(text: str):
    try:
        # Extract ingredients from text
        ingredients = extract_ingredients(text)
        
        # If no ingredients found, return a helpful message
        if not ingredients:
            return {"ingredients": ["No ingredients detected. Please check your input."]}
        
        return {"ingredients": ingredients}
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}") 