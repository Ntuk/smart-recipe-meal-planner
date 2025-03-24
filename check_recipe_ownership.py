import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")

async def check_recipe_ownership():
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Get all recipes
    recipes = await db["recipes"].find().to_list(1000)
    
    print(f"Found {len(recipes)} recipes in the database")
    
    # Count unique user IDs
    user_ids = set(recipe["user_id"] for recipe in recipes)
    print(f"Recipes are owned by {len(user_ids)} different users")
    
    for user_id in user_ids:
        count = sum(1 for recipe in recipes if recipe["user_id"] == user_id)
        print(f"User ID: {user_id} owns {count} recipes")
    
    # Check recipe IDs in network error
    recipe_id = "1f044a91-c338-4aef-9cb0-2dc9358b9ff4"  # From the network error
    found_recipe = await db["recipes"].find_one({"id": recipe_id})
    
    if found_recipe:
        print(f"\nFound recipe with ID {recipe_id}")
        print(f"Name: {found_recipe.get('name')}")
        print(f"Owner: {found_recipe.get('user_id')}")
    else:
        print(f"\nRecipe with ID {recipe_id} not found")
    
    # Get information about the user from localStorage
    print("\nTo check the current user, inspect the JWT token from localStorage in the browser")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_recipe_ownership()) 