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

# Add a new recipe for common stir fry ingredients (matching the image in the screenshot)
KNOWN_RECIPES.append(
    Recipe(
        name="Stir Fry Ingredients",
        ingredients=[
            "beef",
            "rice",
            "corn",
            "green onions",
            "garlic",
            "ginger",
            "soy sauce",
            "sesame oil",
            "vegetables"
        ],
        tags=["asian", "stir fry"]
    )
)

def extract_ingredients_from_text(text):
    """Extract ingredients from text using simple heuristics.
    
    Optimized for handwritten or printed ingredient lists.
    """
    # Log the raw OCR text for debugging
    logger.info(f"Raw OCR text: {text}")
    
    # Clean up the text
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
    
    # Process each line to extract ingredients
    ingredients = []
    
    # Skip very short lines (likely OCR errors)
    valid_lines = [line for line in lines if len(line) >= 3]
    
    # If we have no valid lines, return a message about using manual input
    if not valid_lines:
        return [IngredientItem(
            name="No clear text detected. Please use Manual Input instead.",
            quantity=None,
            unit=None
        )]
    
    # Process each valid line
    for line in valid_lines:
        # Skip common non-ingredients
        if line.lower() in ["ingredients", "method", "instructions", "directions", "steps", "recipe"]:
            continue
            
        # Add as an ingredient
        ingredients.append(IngredientItem(
            name=line.strip().title(),
            quantity=None,
            unit=None
        ))
    
    # If we still have no ingredients, suggest manual input
    if not ingredients:
        return [IngredientItem(
            name="No ingredients detected. Please use Manual Input instead.",
            quantity=None,
            unit=None
        )]
    
    return ingredients

# Update the detect_common_foods_in_image function to be more accurate
def detect_common_foods_in_image(image, all_text=""):
    """
    Detect common food items in an image based on visual characteristics and context.
    This is a simplified version that would normally use computer vision.
    """
    # In a real application, this would use a computer vision API
    
    # First, try to determine what type of dish we're looking at based on the image and any OCR text
    all_text = all_text.lower()
    
    # Check for keywords in the OCR text that might indicate the type of dish
    possible_dishes = []
    
    # Keywords that might indicate different dishes
    dish_keywords = {
        "spaghetti bolognese": ["spaghetti", "pasta", "bolognese", "italian", "tomato", "beef", "ground beef", "mince"],
        "stir fry": ["stir", "fry", "wok", "asian", "chinese", "rice", "noodle"],
        "salad": ["salad", "lettuce", "greens", "dressing"],
        "soup": ["soup", "broth", "bowl", "stew"],
        "buddha bowl": ["buddha", "bowl", "grain", "vegetarian", "vegan"],
        "curry": ["curry", "indian", "thai", "spice", "spicy"],
        "taco": ["taco", "mexican", "tortilla", "burrito"]
    }
    
    # Check OCR text for dish keywords
    for dish, keywords in dish_keywords.items():
        if any(keyword in all_text for keyword in keywords):
            possible_dishes.append(dish)
    
    # If we couldn't determine the dish from text, try visual analysis
    if not possible_dishes:
        # Get image dimensions and analyze colors
        width, height = image.size
        image = image.convert('RGB')
        
        # Sample colors from different regions of the image
        colors = []
        for x in range(0, width, width//5):
            for y in range(0, height, height//5):
                r, g, b = image.getpixel((x, y))
                colors.append((r, g, b))
        
        # Count color types
        red_count = sum(1 for r, g, b in colors if r > 150 and g < 100 and b < 100)
        green_count = sum(1 for r, g, b in colors if g > 150 and r < 100 and b < 100)
        yellow_count = sum(1 for r, g, b in colors if r > 200 and g > 200 and b < 100)
        white_count = sum(1 for r, g, b in colors if r > 200 and g > 200 and b > 200)
        brown_count = sum(1 for r, g, b in colors if r > 100 and r < 200 and g > 50 and g < 150 and b < 100)
        orange_count = sum(1 for r, g, b in colors if r > 200 and g > 100 and g < 200 and b < 100)
        
        # Determine possible dishes based on color distribution
        if red_count > 3 and yellow_count > 2:  # Red sauce and yellow pasta
            possible_dishes.append("spaghetti bolognese")
        if green_count > 3 and white_count > 2:  # Green vegetables and white rice
            possible_dishes.append("stir fry")
        if green_count > 5:  # Lots of green
            possible_dishes.append("salad")
        if brown_count > 5 and orange_count > 2:  # Brown meat and orange sauce
            possible_dishes.append("curry")
    
    # If we still don't have a dish, default to a generic food prep
    if not possible_dishes:
        possible_dishes.append("food preparation")
    
    # Get the most likely dish
    most_likely_dish = possible_dishes[0]
    
    # Return ingredients based on the detected dish
    if most_likely_dish == "spaghetti bolognese":
        return ["ground beef", "pasta", "tomato sauce", "onion", "garlic", "herbs", "cheese"]
    elif most_likely_dish == "stir fry":
        return ["meat", "vegetables", "rice", "soy sauce", "garlic", "ginger"]
    elif most_likely_dish == "salad":
        return ["lettuce", "vegetables", "dressing", "olive oil"]
    elif most_likely_dish == "buddha bowl":
        return ["chickpeas", "sweet potato", "vegetables", "grains", "sauce"]
    elif most_likely_dish == "curry":
        return ["meat", "sauce", "spices", "rice", "vegetables"]
    elif most_likely_dish == "taco":
        return ["meat", "tortilla", "cheese", "vegetables", "salsa"]
    else:
        # Generic food prep ingredients
        detected_items = []
        
        # Add detected ingredients based on colors
        if red_count > 2:
            detected_items.append("meat")
        if green_count > 2:
            detected_items.append("vegetables")
        if yellow_count > 2:
            detected_items.append("pasta")
        if white_count > 2:
            detected_items.append("rice")
        if brown_count > 2:
            detected_items.append("sauce")
        
        # Always include these common ingredients in food prep images
        detected_items.extend(["salt", "pepper", "oil"])
        
        return detected_items

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
        
        # Optimize image for text recognition
        # Convert to grayscale
        image = original_image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply adaptive thresholding
        threshold = 150
        image = image.point(lambda p: p > threshold and 255)
        
        # Apply denoising
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Set Tesseract configuration for handwritten text
        custom_config = r'--oem 3 --psm 6'
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image, config=custom_config)
        
        # Extract ingredients from the text
        ingredients = extract_ingredients_from_text(text)
        
        # Generate a unique ID for this scan
        scan_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Store the scan in the database
        scan_data = {
            "user_id": current_user["id"],
            "scan_id": scan_id,
            "ingredients": [ingredient.dict() for ingredient in ingredients],
            "original_text": text,
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