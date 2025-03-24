import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_ingredients_in_meal_plans():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    collection = db["meal_plans"]
    
    # Find all meal plans
    meal_plans = await collection.find().to_list(None)
    
    for meal_plan in meal_plans:
        print(f"Processing meal plan: {meal_plan['id']}")
        modified = False
        
        # Process each day, meal, recipe
        if "days" in meal_plan:
            for day in meal_plan["days"]:
                if "meals" in day:
                    for meal in day["meals"]:
                        if "recipes" in meal:
                            for recipe in meal["recipes"]:
                                if "ingredients" in recipe:
                                    # Check if ingredients need modification
                                    if any(isinstance(ingredient, dict) for ingredient in recipe["ingredients"]):
                                        # Convert all ingredients to strings
                                        recipe["ingredients"] = [
                                            ingredient.get("name", str(ingredient)) if isinstance(ingredient, dict) else ingredient
                                            for ingredient in recipe["ingredients"]
                                        ]
                                        modified = True
                                        print(f"Fixed ingredients for recipe: {recipe['name']}")
        
        # Update the document if modified
        if modified:
            print(f"Updating meal plan: {meal_plan['id']}")
            # Make a deep copy to avoid MongoDB comparison issues
            meal_plan_copy = meal_plan.copy()
            if '_id' in meal_plan_copy:
                meal_plan_id = meal_plan_copy['_id']
                result = await collection.replace_one({"_id": meal_plan_id}, meal_plan_copy)
                print(f"Updated: {result.modified_count}")
        else:
            print(f"No changes needed for meal plan: {meal_plan['id']}")
    
    print("Finished fixing meal plans!")

# Run the async function
if __name__ == "__main__":
    asyncio.run(fix_ingredients_in_meal_plans())
