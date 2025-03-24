import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_recipe_descriptions():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Get all recipes
    recipes = await recipe_collection.find().to_list(length=None)
    print(f"Found {len(recipes)} recipes in total")
    
    # Check each recipe's description
    missing_desc = []
    short_desc = []
    name_as_desc = []
    good_desc = []
    
    for recipe in recipes:
        recipe_name = recipe.get("name", "Unknown")
        description = recipe.get("description", "")
        
        # Check description status
        if not description or description.strip() == "":
            missing_desc.append(recipe_name)
        elif description.strip() == recipe_name:
            name_as_desc.append(recipe_name)
        elif len(description.strip()) < 20:
            short_desc.append(recipe_name)
        else:
            good_desc.append(recipe_name)
    
    # Print results
    print("\n--- DESCRIPTION STATUS REPORT ---")
    print(f"Recipes with good descriptions: {len(good_desc)} ({len(good_desc)/len(recipes)*100:.1f}%)")
    
    if missing_desc:
        print(f"\nRecipes with missing descriptions: {len(missing_desc)}")
        for name in missing_desc:
            print(f"- {name}")
    
    if name_as_desc:
        print(f"\nRecipes using name as description: {len(name_as_desc)}")
        for name in name_as_desc:
            print(f"- {name}")
    
    if short_desc:
        print(f"\nRecipes with very short descriptions: {len(short_desc)}")
        for name in short_desc:
            print(f"- {name}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_recipe_descriptions()) 