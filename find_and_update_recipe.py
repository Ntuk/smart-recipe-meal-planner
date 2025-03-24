import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
import sys

async def find_recipe_by_name(name):
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Find the recipe by name (case-insensitive)
    # Using regex for a more flexible search
    regex_pattern = {"$regex": f"^{name}$", "$options": "i"}
    recipe = await recipe_collection.find_one({"name": regex_pattern})
    
    if not recipe:
        # Try a more flexible search if exact match not found
        regex_pattern = {"$regex": name, "$options": "i"}
        recipe = await recipe_collection.find_one({"name": regex_pattern})
        
    client.close()
    return recipe

async def update_recipe_direct(recipe_id, updated_data):
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Find the recipe by id
    recipe = await recipe_collection.find_one({"id": recipe_id})
    
    if not recipe:
        print(f"Error: Recipe with ID {recipe_id} not found")
        return False
    
    # Update the recipe
    try:
        # Print original recipe for comparison
        print("\nOriginal Recipe:")
        print(json.dumps({k: v for k, v in recipe.items() if k != '_id'}, indent=2, default=str))
        
        # Update the recipe
        result = await recipe_collection.update_one(
            {"id": recipe_id},
            {"$set": updated_data}
        )
        
        if result.modified_count == 0:
            print("No changes made to the recipe")
            return False
        
        # Get the updated recipe
        updated_recipe = await recipe_collection.find_one({"id": recipe_id})
        
        # Print updated recipe
        print("\nUpdated Recipe:")
        print(json.dumps({k: v for k, v in updated_recipe.items() if k != '_id'}, indent=2, default=str))
        
        print(f"\nSuccess: Recipe {recipe_id} updated successfully")
        return True
    except Exception as e:
        print(f"Error updating recipe: {str(e)}")
        return False
    finally:
        client.close()

async def main(recipe_name=None):
    # If no name provided, list all recipes
    if not recipe_name:
        client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
        db = client["recipe_app"]
        recipe_collection = db["recipes"]
        
        recipes = await recipe_collection.find().to_list(length=None)
        print("Available recipes:")
        for i, recipe in enumerate(recipes):
            print(f"{i+1}. {recipe.get('name')} (ID: {recipe.get('id')})")
        
        client.close()
        return
    
    # Find the recipe by name
    recipe = await find_recipe_by_name(recipe_name)
    
    if not recipe:
        print(f"Recipe with name '{recipe_name}' not found")
        return
    
    print(f"Found recipe: {recipe.get('name')} (ID: {recipe.get('id')})")
    
    # Prompt for update
    choice = input("Do you want to update this recipe? (y/n): ")
    if choice.lower() != 'y':
        print("Update cancelled")
        return
    
    # For this example, we'll update the description and tags for chicken & halloumi burgers
    if "halloumi" in recipe.get('name', '').lower():
        form_data = {
            "description": "Quick and delicious chicken burgers with halloumi cheese, perfect for a weeknight dinner. These juicy burgers are packed with flavor and ready in just 15 minutes.",
            "tags": ["Chicken", "Quick", "Burger", "Halloumi"],
            "difficulty": "Easy",
            "prep_time": 5,
            "cook_time": 10,
            "servings": 2,
            "ingredients": [
                {
                    "name": "Chicken Breasts",
                    "quantity": "2",
                    "unit": ""
                },
                {
                    "name": "Oil",
                    "quantity": "1",
                    "unit": "tbsp"
                },
                {
                    "name": "Hotsauce",
                    "quantity": "4",
                    "unit": "tbsp"
                },
                {
                    "name": "Lemon Juice",
                    "quantity": "1/2",
                    "unit": ""
                },
                {
                    "name": "Buns",
                    "quantity": "2",
                    "unit": ""
                },
                {
                    "name": "Halloumi",
                    "quantity": "250",
                    "unit": "g"
                },
                {
                    "name": "Lettuce",
                    "quantity": "2",
                    "unit": "leaves"
                },
                {
                    "name": "Tomato",
                    "quantity": "1",
                    "unit": ""
                }
            ],
            "steps": [
                {
                    "number": 1,
                    "description": "Put the chicken breasts between two pieces of baking parchment and use a rolling pin to gently bash them until they are approximately 1cm thick. Cut each chicken breast into two even pieces."
                },
                {
                    "number": 2,
                    "description": "If you're using a frying pan, heat two frying pans over medium-high heat, with one of them containing oil. Fry the chicken in the oiled pan for 3-4 mins on each side until they are cooked through."
                },
                {
                    "number": 3,
                    "description": "Meanwhile, slice the halloumi into 4 pieces and fry in the dry pan for 2 mins on each side until golden."
                },
                {
                    "number": 4,
                    "description": "Mix the hot sauce with the lemon juice and set aside."
                },
                {
                    "number": 5,
                    "description": "Slice the buns in half and lightly toast them. Build your burgers with lettuce, chicken, halloumi, tomato slices, and the hot sauce mixture."
                }
            ]
        }
    else:
        # Generic update with just tags and description
        description = input("Enter a new description (or press Enter to skip): ")
        tags_input = input("Enter tags separated by commas (or press Enter to skip): ")
        
        form_data = {}
        if description:
            form_data["description"] = description
        
        if tags_input:
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
            if tags:
                form_data["tags"] = tags
    
    # Update the recipe
    await update_recipe_direct(recipe.get('id'), form_data)

if __name__ == "__main__":
    # Get recipe name from command line or list all recipes
    recipe_name = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(recipe_name)) 