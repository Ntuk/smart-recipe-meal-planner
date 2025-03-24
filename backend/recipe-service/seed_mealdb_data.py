import asyncio
import httpx
import uuid
from datetime import datetime
import json
import argparse
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Recipe models - simplified from main.py
class Ingredient:
    def __init__(self, name: str, quantity: str, unit: Optional[str] = None):
        self.name = name
        self.quantity = quantity
        self.unit = unit
    
    def to_dict(self):
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit
        }

class Step:
    def __init__(self, number: int, description: str):
        self.number = number
        self.description = description
    
    def to_dict(self):
        return {
            "number": self.number,
            "description": self.description
        }

class RecipeCreate:
    def __init__(self, name: str, description: str, ingredients: List[Ingredient],
                 steps: List[Step], prep_time: int, cook_time: int, servings: int,
                 tags: List[str] = None, cuisine: Optional[str] = None,
                 image_url: Optional[str] = None, nutrition: Optional[Dict[str, float]] = None):
        self.name = name
        self.description = description
        self.ingredients = ingredients
        self.steps = steps
        self.prep_time = prep_time
        self.cook_time = cook_time
        self.servings = servings
        self.tags = tags or []
        self.cuisine = cuisine
        self.image_url = image_url
        self.nutrition = nutrition
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "steps": [s.to_dict() for s in self.steps],
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "servings": self.servings,
            "tags": self.tags,
            "cuisine": self.cuisine,
            "image_url": self.image_url,
            "nutrition": self.nutrition
        }

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
    description = meal.get("strMeal", "") + " - " + meal.get("strCategory", "")
    
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
    instructions = meal.get("strInstructions", "")
    steps = []
    
    # Split instructions by periods, newlines, or numbered items
    import re
    # Split by either line breaks or periods followed by space
    step_texts = re.split(r'[\n\r]+|(?<=[.!?])\s+', instructions)
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

async def seed_database_from_mealdb(mongodb_uri, db_name, user_id, max_per_category=5, max_per_area=3):
    """
    Comprehensive function to seed the database with recipes from MealDB
    """
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[db_name]
    
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
        logger.info(f"Found {len(categories)} categories")
        
        for category in categories:
            try:
                logger.info(f"Processing category: {category}")
                # Get recipes for this category
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}")
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch recipes for category: {category}")
                        continue
                    
                    data = response.json()
                    meals = data.get("meals", [])
                    logger.info(f"Found {len(meals)} meals in category {category}")
                    
                    # Process up to max_per_category recipes
                    count = 0
                    for meal_preview in meals:
                        if count >= max_per_category:
                            break
                            
                        meal_id = meal_preview.get("idMeal")
                        if not meal_id or meal_id in processed_meal_ids:
                            continue
                            
                        # Get full details
                        logger.info(f"Fetching details for meal {meal_id}")
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
                        
                        recipe_data = recipe_create.to_dict()
                        recipe_data.update({
                            "id": recipe_id,
                            "user_id": user_id,
                            "created_at": now,
                            "updated_at": now
                        })
                        
                        # Check for duplicates by name
                        existing_recipe = await db["recipes"].find_one({
                            "name": recipe_data["name"],
                            "user_id": user_id
                        })
                        
                        if not existing_recipe:
                            await db["recipes"].insert_one(recipe_data)
                            processed_meal_ids.add(meal_id)
                            import_summary["total_imported"] += 1
                            count += 1
                            logger.info(f"Imported recipe: {recipe_data['name']}")
                
                import_summary["categories_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing category {category}: {str(e)}")
                import_summary["errors"] += 1
        
        # Next import recipes by area (cuisine)
        areas = await fetch_all_areas_from_mealdb()
        import_summary["total_areas"] = len(areas)
        logger.info(f"Found {len(areas)} cuisine areas")
        
        for area in areas:
            try:
                logger.info(f"Processing area: {area}")
                # Get recipes for this area
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?a={area}")
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch recipes for area: {area}")
                        continue
                    
                    data = response.json()
                    meals = data.get("meals", [])
                    logger.info(f"Found {len(meals)} meals in area {area}")
                    
                    # Process up to max_per_area recipes
                    count = 0
                    for meal_preview in meals:
                        if count >= max_per_area:
                            break
                            
                        meal_id = meal_preview.get("idMeal")
                        if not meal_id or meal_id in processed_meal_ids:
                            continue
                            
                        # Get full details
                        logger.info(f"Fetching details for meal {meal_id}")
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
                        
                        recipe_data = recipe_create.to_dict()
                        recipe_data.update({
                            "id": recipe_id,
                            "user_id": user_id,
                            "created_at": now,
                            "updated_at": now
                        })
                        
                        # Check for duplicates by name
                        existing_recipe = await db["recipes"].find_one({
                            "name": recipe_data["name"],
                            "user_id": user_id
                        })
                        
                        if not existing_recipe:
                            await db["recipes"].insert_one(recipe_data)
                            processed_meal_ids.add(meal_id)
                            import_summary["total_imported"] += 1
                            count += 1
                            logger.info(f"Imported recipe: {recipe_data['name']}")
                
                import_summary["areas_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing area {area}: {str(e)}")
                import_summary["errors"] += 1
        
        return import_summary
        
    except Exception as e:
        logger.error(f"Error in seed_database_from_mealdb: {str(e)}")
        import_summary["errors"] += 1
        return import_summary
    finally:
        await client.aclose()

async def main():
    parser = argparse.ArgumentParser(description='Seed recipe database with MealDB data')
    parser.add_argument('--mongo-uri', default='mongodb://admin:password@localhost:27017', help='MongoDB connection string')
    parser.add_argument('--db-name', default='recipe_app', help='Database name')
    parser.add_argument('--user-id', required=True, help='User ID to associate recipes with')
    parser.add_argument('--max-per-category', type=int, default=3, help='Maximum recipes per category')
    parser.add_argument('--max-per-area', type=int, default=2, help='Maximum recipes per area')
    
    args = parser.parse_args()
    
    logger.info("Starting MealDB seeding process")
    result = await seed_database_from_mealdb(
        mongodb_uri=args.mongo_uri,
        db_name=args.db_name,
        user_id=args.user_id,
        max_per_category=args.max_per_category,
        max_per_area=args.max_per_area
    )
    
    logger.info(f"Seeding complete. Summary: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main()) 