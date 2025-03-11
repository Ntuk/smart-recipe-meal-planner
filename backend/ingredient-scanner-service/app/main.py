from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import io
import uuid
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pytesseract
from PIL import Image

# Load environment variables
load_dotenv()

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
    id: str
    user_id: str
    ingredients: List[IngredientItem]
    original_text: str
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

# Helper functions
def extract_ingredients_from_text(text: str) -> List[IngredientItem]:
    """
    Extract ingredients from text using simple heuristics.
    In a real application, this would use NLP or a more sophisticated algorithm.
    """
    ingredients = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Simple parsing logic - in a real app this would be more sophisticated
        parts = line.split(' ', 1)
        if len(parts) > 1 and parts[0].replace('.', '', 1).isdigit():
            # Assume first part is quantity
            quantity = parts[0]
            rest = parts[1].strip()
            
            # Try to extract unit
            unit_words = ['cup', 'cups', 'tbsp', 'tsp', 'tablespoon', 'teaspoon', 'oz', 'ounce', 'pound', 'lb', 'g', 'kg', 'ml', 'l']
            unit = None
            name = rest
            
            for unit_word in unit_words:
                if rest.lower().startswith(unit_word + ' '):
                    unit = unit_word
                    name = rest[len(unit_word):].strip()
                    break
                    
            ingredients.append(IngredientItem(name=name, quantity=quantity, unit=unit))
        else:
            # Just add as ingredient name
            ingredients.append(IngredientItem(name=line))
    
    return ingredients

# Routes
@app.post("/scan", response_model=ScanResult)
async def scan_ingredients(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # Check file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image)
        
        # Extract ingredients from text
        ingredients = extract_ingredients_from_text(text)
        
        # Save scan result
        scan_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        scan_data = {
            "id": scan_id,
            "user_id": current_user["id"],
            "ingredients": [ingredient.dict() for ingredient in ingredients],
            "original_text": text,
            "created_at": now
        }
        
        await app.mongodb["scans"].insert_one(scan_data)
        
        return scan_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )

@app.post("/manual-input", response_model=ScanResult)
async def manual_input(
    request: ManualInputRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Extract ingredients from text
        ingredients = extract_ingredients_from_text(request.text)
        
        # Save scan result
        scan_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        scan_data = {
            "id": scan_id,
            "user_id": current_user["id"],
            "ingredients": [ingredient.dict() for ingredient in ingredients],
            "original_text": request.text,
            "created_at": now
        }
        
        await app.mongodb["scans"].insert_one(scan_data)
        
        return scan_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text: {str(e)}"
        )

@app.get("/scans", response_model=List[ScanResult])
async def get_scans(current_user: dict = Depends(get_current_user)):
    scans = []
    cursor = app.mongodb["scans"].find({"user_id": current_user["id"]}).sort("created_at", -1)
    async for document in cursor:
        scans.append(document)
    
    return scans

@app.get("/scans/{scan_id}", response_model=ScanResult)
async def get_scan(scan_id: str, current_user: dict = Depends(get_current_user)):
    scan = await app.mongodb["scans"].find_one({"id": scan_id, "user_id": current_user["id"]})
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID {scan_id} not found"
        )
    
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