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
from .rabbitmq_utils import RabbitMQClient
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import threading

# Prometheus metrics
REQUESTS = Counter('ingredient_scanner_service_requests_total', 'Total requests to the ingredient scanner service', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('ingredient_scanner_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint'])
SCAN_OPERATIONS = Counter('ingredient_scanner_service_operations_total', 'Total scan operations', ['operation', 'status'])
OCR_LATENCY = Histogram('ingredient_scanner_service_ocr_duration_seconds', 'OCR processing time in seconds')

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
RABBITMQ_URI = os.getenv("RABBITMQ_URI", "amqp://admin:password@rabbitmq:5672/")

# Initialize FastAPI app
app = FastAPI(title="Ingredient Scanner Service", description="Service for scanning and extracting ingredients from images")

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Request monitoring middleware
@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Security
security = HTTPBearer()

# Initialize RabbitMQ client
rabbitmq_client = RabbitMQClient(RABBITMQ_URI)

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
        
        # Create indexes for scanned ingredients collection
        await app.mongodb["scanned_ingredients"].create_index("user_id")
        await app.mongodb["scanned_ingredients"].create_index("scanned_at")
        
        # Setup RabbitMQ exchanges and queues
        if await rabbitmq_client.connect():
            await rabbitmq_client.setup_ingredient_scanner_queues()
        else:
            logger.warning("Failed to connect to RabbitMQ during startup. Will retry on demand.")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    
    # Close RabbitMQ connection
    await rabbitmq_client.close()

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
    
    # Words to filter out (common OCR errors, website URLs, headers, etc.)
    filter_words = [
        "for the", "recipe", "ingredients", "method", "instructions", 
        "directions", "steps", ".com", "www.", "http", "copyright",
        "all rights reserved", "preparation", "cooking time", "serves",
        "yield", "notes", "tips", "source", "author", "published"
    ]
    
    # Process each valid line
    for line in valid_lines:
        line = line.strip()
        
        # Skip if line contains any filter words
        if any(word.lower() in line.lower() for word in filter_words):
            continue
            
        # Skip if line looks like a URL or email
        if re.search(r'[.@]', line) or re.search(r'www|http|\.com', line.lower()):
            continue
            
        # Skip if line is too long (likely a sentence, not an ingredient)
        if len(line.split()) > 5:
            continue
            
        # Skip if line contains too many numbers (likely a measurement or step number)
        if len(re.findall(r'\d', line)) > 3:
            continue
            
        # Skip if line is just punctuation or special characters
        if not re.search(r'[a-zA-Z]', line):
            continue
            
        # Clean up the ingredient name
        ingredient_name = line.strip()
        ingredient_name = re.sub(r'^[-•*+]+\s*', '', ingredient_name)  # Remove bullet points
        ingredient_name = ingredient_name.strip()
        
        # Add as an ingredient if it's not empty after cleaning
        if ingredient_name:
            ingredients.append(IngredientItem(
                name=ingredient_name.strip().title(),
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
        logger.info(f"Received scan request from user {current_user['id']}")
        logger.info(f"File content type: {file.content_type}")
        
        # Process image and extract text
        contents = await file.read()
        logger.info(f"Read {len(contents)} bytes from uploaded file")
        
        try:
            image = Image.open(io.BytesIO(contents))
            logger.info(f"Opened image with size: {image.size} and mode: {image.mode}")
        except Exception as e:
            logger.error(f"Error opening image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Enhance image for better OCR
        try:
            image = image.convert('L')  # Convert to grayscale
            logger.info("Converted image to grayscale")
            image = image.filter(ImageFilter.SHARPEN)
            logger.info("Applied sharpening filter")
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            logger.info("Enhanced image contrast")
        except Exception as e:
            logger.error(f"Error enhancing image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing image"
            )
        
        # Perform OCR
        try:
            text = pytesseract.image_to_string(image)
            logger.info(f"OCR extracted text: {text[:100]}...")  # Log first 100 chars
        except Exception as e:
            logger.error(f"Error performing OCR: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error performing OCR"
            )
        
        # Extract ingredients from text
        try:
            ingredients = extract_ingredients_from_text(text)
            logger.info(f"Extracted {len(ingredients)} ingredients")
            for i, ingredient in enumerate(ingredients):
                logger.info(f"Ingredient {i+1}: {ingredient.name}")
        except Exception as e:
            logger.error(f"Error extracting ingredients: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error extracting ingredients"
            )
        
        # Store scan result
        try:
            scan_id = str(uuid.uuid4())
            scan_result = {
                "scan_id": scan_id,
                "user_id": current_user["id"],
                "ingredients": [ingredient.dict() for ingredient in ingredients],
                "created_at": datetime.utcnow()
            }
            
            await app.mongodb["scans"].insert_one(scan_result)
            logger.info(f"Stored scan result in MongoDB with ID: {scan_id}")
        except Exception as e:
            logger.error(f"Error storing scan result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error storing scan result"
            )
        
        # Publish to RabbitMQ for async processing
        try:
            if rabbitmq_client.is_connected():
                await rabbitmq_client.publish_scan_result(scan_result)
                logger.info("Published scan result to RabbitMQ")
            else:
                logger.warning("RabbitMQ not connected, skipping message publish")
        except Exception as e:
            logger.error(f"Error publishing to RabbitMQ: {str(e)}")
            # Don't raise an exception here, as this is not critical for the main functionality
        
        SCAN_OPERATIONS.labels(operation="scan", status="success").inc()
        return scan_result
    except Exception as e:
        SCAN_OPERATIONS.labels(operation="scan", status="error").inc()
        logger.error(f"Error processing scan: {str(e)}")
        logger.exception("Detailed exception information:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/manual-input", response_model=ScanResult)
async def manual_input(request: ManualInputRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Manually input ingredients for processing.
    """
    try:
        # Get the auth token directly from the credentials
        auth_token = credentials.credentials
        logger.info(f"Auth token received: {bool(auth_token)}")
        
        # Get the current user
        current_user = await get_current_user(credentials)
        logger.info(f"Current user ID: {current_user['id']}")
        
        logger.info(f"Processing manual input request: {request.text}")
        # Generate a scan ID
        scan_id = str(uuid.uuid4())
        
        # Process the ingredients
        ingredients = [{"name": ingredient.strip()} for ingredient in request.text.split(",")]
        logger.info(f"Processed ingredients: {ingredients}")
        
        # Create scan result with string datetime for JSON serialization
        created_at = datetime.utcnow()
        scan_result = {
            "scan_id": scan_id,
            "user_id": current_user["id"],
            "token": auth_token,  # Include the user's token directly from the authorization header
            "ingredients": ingredients,
            "created_at": created_at.isoformat()  # Convert to ISO format string for JSON
        }
        logger.info(f"Created scan result: {scan_result}")
        
        # Define the scan result for MongoDB (with datetime object)
        mongodb_scan_result = {
            "scan_id": scan_id,
            "user_id": current_user["id"],
            "token": auth_token,
            "ingredients": ingredients,
            "created_at": created_at  # Keep as datetime for MongoDB
        }
        
        # Store the scan result
        try:
            await app.mongodb["scans"].insert_one(mongodb_scan_result)
            logger.info(f"Stored scan result in MongoDB: {scan_id}")
        except Exception as mongo_err:
            logger.error(f"MongoDB error: {str(mongo_err)}")
            raise
        
        # Publish the scan result to RabbitMQ
        logger.info("Attempting to publish scan result to RabbitMQ")
        try:
            if not rabbitmq_client.is_connected():
                logger.warning("RabbitMQ client not connected, attempting to connect...")
                connect_result = await rabbitmq_client.connect()
                logger.info(f"RabbitMQ connect result: {connect_result}")
                if not connect_result:
                    logger.error("Failed to connect to RabbitMQ")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to connect to message broker"
                    )
            
            logger.info(f"Publishing to RabbitMQ with URI: {rabbitmq_client.connection_url}")
            success = await rabbitmq_client.publish_scan_result(scan_result)
            logger.info(f"RabbitMQ publish result: {success}")
            if not success:
                logger.error("Failed to publish scan result to RabbitMQ")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to publish message to message broker"
                )
        except Exception as rabbitmq_err:
            logger.error(f"RabbitMQ error: {str(rabbitmq_err)}")
            raise
            
        logger.info("Successfully published scan result to RabbitMQ")
        
        SCAN_OPERATIONS.labels(operation="manual_input", status="success").inc()
        # Create return object from the MongoDB result
        return_scan_result = {
            "scan_id": scan_id,
            "ingredients": [IngredientItem(**ingredient) for ingredient in ingredients],
            "created_at": created_at
        }
        return return_scan_result
        
    except Exception as e:
        SCAN_OPERATIONS.labels(operation="manual_input", status="error").inc()
        logger.error(f"Error processing manual input: {str(e)}")
        logger.exception("Detailed exception information:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing manual input"
        )

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

@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Test endpoint for file upload."""
    try:
        logger.info(f"Received test upload request")
        logger.info(f"File content type: {file.content_type}")
        
        contents = await file.read()
        logger.info(f"Read {len(contents)} bytes from uploaded file")
        
        return {
            "message": "File uploaded successfully",
            "content_type": file.content_type,
            "size": len(contents)
        }
    except Exception as e:
        logger.error(f"Error in test upload: {str(e)}")
        logger.exception("Detailed exception information:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing file upload"
        ) 