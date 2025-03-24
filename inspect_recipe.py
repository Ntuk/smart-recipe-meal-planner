import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def inspect_recipe():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Get all recipes
    recipes = await recipe_collection.find().limit(2).to_list(length=None)
    
    if not recipes:
        print("No recipes found in the database")
        return
    
    # Print detailed information about the first recipe
    print(f"Found {len(recipes)} recipes")
    
    for i, recipe in enumerate(recipes):
        print(f"\n--- RECIPE {i+1} DETAILS ---")
        # Convert ObjectId to string for JSON serialization
        if "_id" in recipe and hasattr(recipe["_id"], "__str__"):
            recipe["_id"] = str(recipe["_id"])
            
        # Pretty print the entire recipe
        print(json.dumps(recipe, indent=2, default=str))
        
        # Specifically check tags and categories
        print("\nSpecific Fields:")
        print(f"Tags: {recipe.get('tags', [])}")
        print(f"Cuisine: {recipe.get('cuisine', 'Not specified')}")
        print(f"Category: {recipe.get('category', 'Not specified')}")
        
        # Check steps structure
        steps = recipe.get('steps', [])
        if steps:
            print("\nSteps structure:")
            step_sample = steps[0]
            print(f"Step type: {type(step_sample)}")
            if isinstance(step_sample, dict):
                print(f"Step keys: {step_sample.keys()}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(inspect_recipe()) 