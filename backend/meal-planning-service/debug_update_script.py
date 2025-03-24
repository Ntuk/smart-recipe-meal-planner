#!/usr/bin/env python3
import pymongo
import datetime
import logging
import json
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection details
MONGODB_URI = "mongodb://admin:password@mongodb:27017/"
DB_NAME = "recipe_app"
COLLECTION_NAME = "meal_plans"

def main():
    """
    Debug script to directly update a meal plan with a recipe
    """
    try:
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        client = pymongo.MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Meal plan ID
        meal_plan_id = "f99bdd0b-b573-44ca-a70e-70c44fbfcc02"
        
        # First, get the current meal plan
        logger.info(f"Fetching meal plan with ID: {meal_plan_id}")
        meal_plan = collection.find_one({"id": meal_plan_id})
        
        if not meal_plan:
            logger.error(f"Meal plan with ID {meal_plan_id} not found")
            return
        
        logger.info(f"Found meal plan: {meal_plan['name']}")
        
        # The recipe we want to add
        recipe_to_add = {
            'id': '5',
            'name': 'Debug Test Recipe',
            'prep_time': 30,
            'cook_time': 45,
            'servings': 4,
            'image_url': '',
            'ingredients': ['Test Ingredient 1', 'Test Ingredient 2', 'Test Ingredient 3']
        }
        
        # Get the days array from the meal plan
        days = meal_plan.get('days', [])
        logger.info(f"Current days structure: {json.dumps(days, default=str)}")
        
        # Check if we have the days we need
        if len(days) >= 1:
            # Add the recipe to dinner on the first day (2025-03-23)
            day = days[0]  # First day
            if 'meals' in day and len(day['meals']) >= 3:
                # We add to the dinner meal (index 2 - assuming breakfast, lunch, dinner order)
                dinner = day['meals'][2]
                
                # Add the recipe to the dinner's recipes array
                if 'recipes' not in dinner or not isinstance(dinner['recipes'], list):
                    dinner['recipes'] = []
                
                dinner['recipes'].append(recipe_to_add)
                logger.info(f"Added recipe to dinner on {day.get('date')}")
            else:
                logger.error(f"Could not find meals in day structure: {day}")
        else:
            logger.error("Not enough days in the meal plan")
        
        # Prepare the update operation
        update_operation = {
            "$set": {
                "days": days,
                "updated_at": datetime.datetime.utcnow()
            }
        }
        
        # Log the update operation
        logger.info(f"Update operation: {json.dumps(update_operation, default=str)}")
        
        # Perform the update
        result = collection.update_one({"id": meal_plan_id}, update_operation)
        
        # Log the result
        logger.info(f"Update result: matched={result.matched_count}, modified={result.modified_count}")
        
        # Verify the update
        updated_meal_plan = collection.find_one({"id": meal_plan_id})
        
        # Count the recipes
        recipe_count = 0
        for day in updated_meal_plan.get('days', []):
            for meal in day.get('meals', []):
                recipes = meal.get('recipes', [])
                recipe_count += len(recipes)
                if recipes:
                    logger.info(f"Found {len(recipes)} recipes in {meal.get('name')} on {day.get('date')}")
                    for recipe in recipes:
                        logger.info(f"  - Recipe: {recipe.get('name')}")
        
        logger.info(f"Total recipes found after update: {recipe_count}")
        
        logger.info("Debug update completed successfully")
        
    except Exception as e:
        logger.error(f"Error in debug script: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
if __name__ == "__main__":
    main() 