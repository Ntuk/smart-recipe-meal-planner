import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
import sys

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

async def update_recipe_from_form(recipe_id, form_data):
    # Parse form data
    title = form_data.get("title", "")
    description = form_data.get("description", "")
    tags = form_data.get("tags", [])
    difficulty = form_data.get("difficulty", "Easy")
    
    # Create update object
    update_data = {
        "name": title,
        "description": description,
        "tags": tags,
        "difficulty": difficulty
    }
    
    # Add numeric fields if provided
    if "prep_time" in form_data and form_data["prep_time"] is not None:
        update_data["prep_time"] = form_data["prep_time"]
    
    if "cook_time" in form_data and form_data["cook_time"] is not None:
        update_data["cook_time"] = form_data["cook_time"]
    
    if "servings" in form_data and form_data["servings"] is not None:
        update_data["servings"] = form_data["servings"]
    
    # Add ingredients if provided
    if "ingredients" in form_data and form_data["ingredients"]:
        update_data["ingredients"] = form_data["ingredients"]
    
    # Add steps if provided
    if "steps" in form_data and form_data["steps"]:
        update_data["steps"] = form_data["steps"]
    
    return await update_recipe_direct(recipe_id, update_data)

# Example usage
if __name__ == "__main__":
    # Check if recipe ID was provided
    if len(sys.argv) < 2:
        print("Usage: python update_recipe_direct.py <recipe_id>")
        sys.exit(1)
    
    recipe_id = sys.argv[1]
    
    # Example form data - you would normally get this from user input
    form_data = {
        "title": "15-minute chicken & halloumi burgers",
        "description": "Quick and delicious chicken burgers with halloumi cheese, perfect for a weeknight dinner. These juicy burgers are packed with flavor and ready in just 15 minutes.",
        "tags": ["Chicken", "Quick", "Burger"],
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
    
    # Update the recipe
    asyncio.run(update_recipe_from_form(recipe_id, form_data)) 