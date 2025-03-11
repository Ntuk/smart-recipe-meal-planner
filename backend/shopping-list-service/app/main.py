from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@localhost:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")
MEAL_PLANNING_SERVICE_URL = os.getenv("MEAL_PLANNING_SERVICE_URL", "http://localhost:8003")

# Initialize FastAPI app
app = FastAPI(title="Shopping List Service", description="Service for managing shopping lists")

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
    
    # Create indexes for shopping lists collection
    await app.mongodb["shopping_lists"].create_index("user_id")
    await app.mongodb["shopping_lists"].create_index("meal_plan_id")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Models
class ShoppingListItem(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    checked: bool = False

class ShoppingListBase(BaseModel):
    name: str
    items: List[ShoppingListItem]
    meal_plan_id: Optional[str] = None
    notes: Optional[str] = None

class ShoppingListCreate(ShoppingListBase):
    pass

class ShoppingList(ShoppingListBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class ShoppingListUpdate(BaseModel):
    name: Optional[str] = None
    items: Optional[List[ShoppingListItem]] = None
    notes: Optional[str] = None

class ItemCheckUpdate(BaseModel):
    checked: bool

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
async def get_meal_plan_ingredients(meal_plan_id: str, token: str):
    """Get ingredients from a meal plan"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{MEAL_PLANNING_SERVICE_URL}/meal-plans/{meal_plan_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                meal_plan = response.json()
                # Extract ingredients from recipes in the meal plan
                ingredients = []
                for day in meal_plan.get("days", []):
                    for meal in day.get("meals", []):
                        for recipe in meal.get("recipes", []):
                            for ingredient in recipe.get("ingredients", []):
                                # Convert to shopping list item
                                ingredients.append(
                                    ShoppingListItem(
                                        name=ingredient.get("name", ""),
                                        quantity=ingredient.get("quantity", ""),
                                        unit=ingredient.get("unit", "")
                                    )
                                )
                return ingredients
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Meal plan with ID {meal_plan_id} not found"
                )
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Meal planning service unavailable",
            )

# Routes
@app.post("/shopping-lists", response_model=ShoppingList, status_code=status.HTTP_201_CREATED)
async def create_shopping_list(
    shopping_list: ShoppingListCreate,
    current_user: dict = Depends(get_current_user)
):
    now = datetime.utcnow()
    shopping_list_id = str(uuid.uuid4())
    
    # If meal_plan_id is provided, get ingredients from the meal plan
    items = shopping_list.items
    if shopping_list.meal_plan_id:
        token = None
        for header in security.model.scheme_name:
            if header.lower() == "authorization":
                token = header.split(" ")[1]
                break
        
        if token:
            try:
                meal_plan_ingredients = await get_meal_plan_ingredients(shopping_list.meal_plan_id, token)
                # Merge with provided items
                item_names = {item.name.lower() for item in items}
                for ingredient in meal_plan_ingredients:
                    if ingredient.name.lower() not in item_names:
                        items.append(ingredient)
            except Exception as e:
                # Continue with provided items if meal plan ingredients can't be fetched
                pass
    
    shopping_list_data = shopping_list.dict()
    shopping_list_data.update({
        "id": shopping_list_id,
        "user_id": current_user["id"],
        "items": [item.dict() for item in items],
        "created_at": now,
        "updated_at": now
    })
    
    await app.mongodb["shopping_lists"].insert_one(shopping_list_data)
    
    return shopping_list_data

@app.get("/shopping-lists", response_model=List[ShoppingList])
async def get_shopping_lists(current_user: dict = Depends(get_current_user)):
    shopping_lists = []
    cursor = app.mongodb["shopping_lists"].find({"user_id": current_user["id"]}).sort("created_at", -1)
    async for document in cursor:
        shopping_lists.append(document)
    
    return shopping_lists

@app.get("/shopping-lists/{shopping_list_id}", response_model=ShoppingList)
async def get_shopping_list(shopping_list_id: str, current_user: dict = Depends(get_current_user)):
    shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id, "user_id": current_user["id"]})
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping list with ID {shopping_list_id} not found"
        )
    
    return shopping_list

@app.put("/shopping-lists/{shopping_list_id}", response_model=ShoppingList)
async def update_shopping_list(
    shopping_list_id: str,
    shopping_list_update: ShoppingListUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Check if shopping list exists
    shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id, "user_id": current_user["id"]})
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping list with ID {shopping_list_id} not found"
        )
    
    # Update shopping list
    update_data = shopping_list_update.dict(exclude_unset=True)
    if "items" in update_data:
        update_data["items"] = [item.dict() for item in shopping_list_update.items]
    
    update_data["updated_at"] = datetime.utcnow()
    
    await app.mongodb["shopping_lists"].update_one(
        {"id": shopping_list_id},
        {"$set": update_data}
    )
    
    # Get updated shopping list
    updated_shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id})
    
    return updated_shopping_list

@app.put("/shopping-lists/{shopping_list_id}/items/{item_name}/check", response_model=ShoppingList)
async def check_item(
    shopping_list_id: str,
    item_name: str,
    update: ItemCheckUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Check if shopping list exists
    shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id, "user_id": current_user["id"]})
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping list with ID {shopping_list_id} not found"
        )
    
    # Find the item in the shopping list
    item_found = False
    for item in shopping_list["items"]:
        if item["name"].lower() == item_name.lower():
            item["checked"] = update.checked
            item_found = True
    
    if not item_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_name} not found in shopping list"
        )
    
    # Update shopping list
    await app.mongodb["shopping_lists"].update_one(
        {"id": shopping_list_id},
        {
            "$set": {
                "items": shopping_list["items"],
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Get updated shopping list
    updated_shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id})
    
    return updated_shopping_list

@app.delete("/shopping-lists/{shopping_list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list(shopping_list_id: str, current_user: dict = Depends(get_current_user)):
    # Check if shopping list exists
    shopping_list = await app.mongodb["shopping_lists"].find_one({"id": shopping_list_id, "user_id": current_user["id"]})
    
    if not shopping_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shopping list with ID {shopping_list_id} not found"
        )
    
    # Delete shopping list
    await app.mongodb["shopping_lists"].delete_one({"id": shopping_list_id})
    
    return None

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 