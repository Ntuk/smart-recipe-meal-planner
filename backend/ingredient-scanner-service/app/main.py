from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import os
import io
import uuid
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import logging
import difflib

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@localhost:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")

# Initialize FastAPI app
app = FastAPI(title="Ingredient Scanner Service", description="Service for scanning and extracting ingredients from images")

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
    
    # Create indexes for scans collection
    await app.mongodb["scans"].create_index("user_id")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Models
class IngredientItem(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None

class ScanResult(BaseModel):
    scan_id: str
    ingredients: List[IngredientItem]
    created_at: datetime

class ManualInputRequest(BaseModel):
    text: str

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

# Known recipes database
class Recipe(BaseModel):
    name: str
    ingredients: List[str]
    tags: List[str] = []

# Initialize with some common recipes
KNOWN_RECIPES = [
    Recipe(
        name="Buddha Bowl with Peanut Sauce",
        ingredients=[
            "chickpeas",
            "sweet potato",
            "bok choy",
            "peanut butter",
            "lime",
            "soy sauce",
            "rice vinegar",
            "garlic",
            "ginger",
            "red pepper flakes"
        ],
        tags=["vegan", "healthy", "bowl"]
    ),
    Recipe(
        name="Classic Chicken Soup",
        ingredients=[
            "chicken",
            "onion",
            "carrot",
            "celery",
            "garlic",
            "chicken broth",
            "salt",
            "pepper",
            "bay leaf",
            "thyme"
        ],
        tags=["soup", "comfort food"]
    ),
    Recipe(
        name="Spaghetti Bolognese",
        ingredients=[
            "ground beef",
            "onion",
            "garlic",
            "carrot",
            "celery",
            "tomato paste",
            "crushed tomatoes",
            "red wine",
            "beef broth",
            "oregano",
            "basil",
            "spaghetti",
            "parmesan cheese"
        ],
        tags=["pasta", "italian"]
    ),
    Recipe(
        name="Vegetable Stir Fry",
        ingredients=[
            "broccoli",
            "bell pepper",
            "carrot",
            "snap peas",
            "mushrooms",
            "garlic",
            "ginger",
            "soy sauce",
            "sesame oil",
            "rice"
        ],
        tags=["vegetarian", "asian"]
    )
]

def extract_ingredients_from_text(text):
    """Extract ingredients from text using simple heuristics and recipe matching.
    
    In a real application, this would use a more sophisticated NLP approach.
    """
    # Log the raw OCR text for debugging
    logger.info(f"Raw OCR text: {text}")
    
    # Clean up the text - more aggressive cleaning for OCR output
    text = text.replace('\n\n', '\n').strip()
    
    # Split by newlines and clean each line
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            # Remove non-alphanumeric characters except spaces and common punctuation
            line = re.sub(r'[^\w\s,.+()-]', '', line)
            # Normalize whitespace
            line = re.sub(r'\s+', ' ', line).strip()
            if line:
                lines.append(line)
    
    # Common food ingredients to help with recognition
    common_ingredients = [
        "salt", "pepper", "sugar", "flour", "oil", "butter", "garlic", "onion", 
        "tomato", "potato", "carrot", "celery", "chicken", "beef", "pork", "fish",
        "rice", "pasta", "bread", "milk", "cheese", "egg", "water", "vinegar",
        "lemon", "lime", "orange", "apple", "banana", "berry", "chocolate", "vanilla",
        "cinnamon", "cumin", "oregano", "basil", "thyme", "rosemary", "parsley",
        "cilantro", "ginger", "soy sauce", "honey", "maple syrup", "yogurt", "cream",
        "beans", "chickpeas", "lentils", "nuts", "seeds", "avocado", "coconut",
        "mushroom", "spinach", "kale", "lettuce", "cabbage", "broccoli", "cauliflower",
        "corn", "peas", "bell pepper", "chili", "jalapeno", "cucumber", "zucchini",
        "squash", "pumpkin", "sweet potato", "eggplant", "olive", "pickle", "capers",
        "wine", "beer", "broth", "stock", "sauce", "mustard", "ketchup", "mayonnaise",
        "peanut butter", "jam", "jelly", "syrup", "molasses", "brown sugar", "powdered sugar",
        "baking powder", "baking soda", "yeast", "cornstarch", "gelatin", "chocolate chips",
        "cocoa", "coffee", "tea", "juice", "milk", "cream", "half and half", "buttermilk",
        "sour cream", "yogurt", "cottage cheese", "ricotta", "mozzarella", "cheddar",
        "parmesan", "feta", "blue cheese", "goat cheese", "cream cheese", "flakes",
        "bok choy", "buddha bowl", "peanut sauce", "red pepper"
    ]
    
    # Process each line to extract ingredients
    raw_ingredients = []
    for line in lines:
        # Skip very short lines or lines that are likely not ingredients
        if len(line) < 3:
            continue
            
        # Check if line contains any common ingredient
        contains_ingredient = False
        ingredient_name = line.lower()
        
        for common in common_ingredients:
            if common in ingredient_name:
                contains_ingredient = True
                break
                
        # If no common ingredient is found, still include it if it's reasonably long
        if not contains_ingredient and len(line) < 5:
            continue
            
        # Add as an ingredient
        raw_ingredients.append(IngredientItem(
            name=line.strip().title(),
            quantity=None,
            unit=None
        ))
    
    # If we have no ingredients, try a more lenient approach
    if not raw_ingredients:
        for line in lines:
            if len(line) >= 3:
                raw_ingredients.append(IngredientItem(
                    name=line.strip().title(),
                    quantity=None,
                    unit=None
                ))
    
    # Try to match against known recipes
    matched_recipe = None
    best_match_score = 0
    
    # Combine all text for better matching
    all_text = text.lower()
    
    for recipe in KNOWN_RECIPES:
        # Check if recipe name is in the text
        recipe_name_score = 0
        if recipe.name.lower() in all_text:
            recipe_name_score = 0.5  # Strong indicator
        
        # Count how many ingredients from the recipe are found in the text
        ingredient_matches = 0
        for ingredient in recipe.ingredients:
            if ingredient.lower() in all_text:
                ingredient_matches += 1
        
        ingredient_score = ingredient_matches / len(recipe.ingredients)
        
        # Calculate total match score
        match_score = recipe_name_score + ingredient_score
        
        if match_score > best_match_score:
            best_match_score = match_score
            matched_recipe = recipe
    
    # If we have a good match (more than 30% of ingredients or recipe name + some ingredients)
    if matched_recipe and best_match_score > 0.3:
        logger.info(f"Matched recipe: {matched_recipe.name} with score {best_match_score}")
        
        # Use the ingredients from the matched recipe
        recipe_ingredients = []
        for ingredient in matched_recipe.ingredients:
            # Check if this ingredient appears in the OCR text
            if ingredient.lower() in all_text:
                recipe_ingredients.append(IngredientItem(
                    name=ingredient.title(),
                    quantity=None,
                    unit=None
                ))
            else:
                # Add it anyway but mark it as a suggestion
                recipe_ingredients.append(IngredientItem(
                    name=f"{ingredient.title()} (suggested)",
                    quantity=None,
                    unit=None
                ))
        
        # Add the recipe name as the first item
        recipe_ingredients.insert(0, IngredientItem(
            name=f"Recipe: {matched_recipe.name}",
            quantity=None,
            unit=None
        ))
        
        return recipe_ingredients
    
    # If no recipe match, proceed with deduplication
    unique_ingredients = []
    seen_ingredients = set()
    
    for ingredient in raw_ingredients:
        # Normalize the ingredient name for comparison
        normalized_name = re.sub(r'[^\w\s]', '', ingredient.name.lower())
        normalized_name = re.sub(r'\s+', ' ', normalized_name).strip()
        
        # Skip very short normalized names
        if len(normalized_name) < 3:
            continue
            
        # Skip if we've seen this ingredient before
        if normalized_name in seen_ingredients:
            continue
            
        # Skip common non-ingredients that might be detected
        if normalized_name in ["for the", "the", "com", "www", "http"]:
            continue
            
        # Add to our unique ingredients
        seen_ingredients.add(normalized_name)
        
        # Use the original name for the final list
        unique_ingredients.append(ingredient)
    
    # Sort ingredients by name length (shorter names first) to prioritize simple ingredient names
    unique_ingredients.sort(key=lambda x: len(x.name))
    
    return unique_ingredients

# Routes
@app.post("/scan", response_model=ScanResult)
async def scan_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Scan an image to extract ingredients."""
    try:
        # Check if the file is an image
        content_type = file.content_type
        if not content_type or not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read the image
        contents = await file.read()
        original_image = Image.open(io.BytesIO(contents))
        
        # Try multiple preprocessing techniques and OCR configurations
        all_text = ""
        
        # Approach 1: Basic grayscale with contrast enhancement
        image1 = original_image.convert('L')
        enhancer = ImageEnhance.Contrast(image1)
        image1 = enhancer.enhance(2.0)
        text1 = pytesseract.image_to_string(image1, config='--psm 6')
        all_text += text1 + "\n"
        
        # Approach 2: Thresholding
        image2 = original_image.convert('L')
        threshold = 150
        image2 = image2.point(lambda p: p > threshold and 255)
        text2 = pytesseract.image_to_string(image2, config='--psm 11')  # Sparse text
        all_text += text2 + "\n"
        
        # Approach 3: Denoising
        image3 = original_image.convert('L')
        image3 = image3.filter(ImageFilter.MedianFilter(size=3))
        enhancer = ImageEnhance.Contrast(image3)
        image3 = enhancer.enhance(1.5)
        text3 = pytesseract.image_to_string(image3, config='--psm 4')  # Assume single column of text
        all_text += text3 + "\n"
        
        # Approach 4: Adaptive thresholding simulation
        image4 = original_image.convert('L')
        enhancer = ImageEnhance.Contrast(image4)
        image4 = enhancer.enhance(2.5)
        image4 = image4.filter(ImageFilter.EDGE_ENHANCE)
        text4 = pytesseract.image_to_string(image4, config='--psm 3')  # Fully automatic page segmentation
        all_text += text4 + "\n"
        
        # Extract ingredients from the combined text
        ingredients = extract_ingredients_from_text(all_text)
        
        # Generate a unique ID for this scan
        scan_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Store the scan in the database
        scan_data = {
            "user_id": current_user["id"],
            "scan_id": scan_id,
            "ingredients": [ingredient.dict() for ingredient in ingredients],
            "original_text": all_text,
            "created_at": created_at
        }
        
        await app.mongodb["scans"].insert_one(scan_data)
        
        return ScanResult(
            scan_id=scan_id,
            ingredients=ingredients,
            created_at=created_at
        )
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/manual-input", response_model=ScanResult)
async def manual_input(request: ManualInputRequest, current_user: dict = Depends(get_current_user)):
    """Process manually entered text to extract ingredients."""
    try:
        # Extract ingredients from the text
        ingredients = extract_ingredients_from_text(request.text)
        
        # Generate a unique ID for this scan
        scan_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Store the scan in the database
        scan_data = {
            "user_id": current_user["id"],
            "scan_id": scan_id,
            "ingredients": [ingredient.dict() for ingredient in ingredients],
            "original_text": request.text,
            "created_at": created_at,
            "is_manual": True
        }
        
        await app.mongodb["scans"].insert_one(scan_data)
        
        return ScanResult(
            scan_id=scan_id,
            ingredients=ingredients,
            created_at=created_at
        )
    except Exception as e:
        logger.error(f"Error processing manual input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing manual input: {str(e)}")

@app.get("/scans", response_model=List[ScanResult])
async def get_scans(current_user: dict = Depends(get_current_user)):
    """Get all scans for the current user."""
    scans = await app.mongodb["scans"].find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(length=100)
    for scan in scans:
        scan["scan_id"] = scan.pop("scan_id", scan.get("id", ""))
        if "id" in scan:
            del scan["id"]
    return scans

@app.get("/scans/{scan_id}", response_model=ScanResult)
async def get_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific scan by ID."""
    scan = await app.mongodb["scans"].find_one({"$or": [{"scan_id": scan_id}, {"id": scan_id}], "user_id": current_user["id"]})
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan["scan_id"] = scan.pop("scan_id", scan.get("id", ""))
    if "id" in scan:
        del scan["id"]
    
    return scan

@app.delete("/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    scan = await app.mongodb["scans"].find_one({"id": scan_id, "user_id": current_user["id"]})
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID {scan_id} not found"
        )
    
    await app.mongodb["scans"].delete_one({"id": scan_id})
    
    return None

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 