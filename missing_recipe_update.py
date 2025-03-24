import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def update_missing_recipes():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Remaining recipes to update
    missing_descriptions = {
        "Chicken Couscous": "A fragrant North African dish featuring tender chicken served over fluffy couscous, seasoned with aromatic spices, herbs, and vegetables. This complete meal balances savory flavors with subtle sweetness.",
        
        "Bigos (Hunters Stew)": "A hearty Polish hunter's stew combining various meats with sauerkraut, fresh cabbage, mushrooms, and dried fruits. This national dish of Poland develops deeper flavor when reheated over several days.",
        
        "Migas": "A traditional Spanish or Portuguese dish made from leftover bread or tortas, fried with garlic, paprika, and other ingredients. Different regions have their own variations, often including chorizo or bacon.",
        
        "Cashew Ghoriba Biscuits": "Delicate Moroccan shortbread cookies made with ground cashews, flavored with cinnamon and orange blossom water. These crumbly, melt-in-your-mouth treats are perfect with mint tea.",
        
        "Chivito uruguayo": "Uruguay's national sandwich featuring thin slices of steak, mozzarella, tomatoes, lettuce, and mayonnaise on a soft roll. Often topped with bacon, olives, and eggs for a substantial meal.",
        
        "Beef Banh Mi Bowls with Sriracha Mayo, Carrot & Pickled Cucumber": "A deconstructed version of the Vietnamese banh mi sandwich, featuring marinated beef, pickled vegetables, and spicy sriracha mayo over rice instead of bread. All the vibrant flavors of the classic sandwich in bowl form."
    }
    
    update_count = 0
    
    # Update each recipe
    for recipe_name, description in missing_descriptions.items():
        result = await recipe_collection.update_one(
            {"name": recipe_name},
            {"$set": {"description": description}}
        )
        if result.modified_count > 0:
            print(f"Updated description for: {recipe_name}")
            update_count += 1
    
    print(f"Total recipes updated: {update_count}")
    client.close()

if __name__ == "__main__":
    asyncio.run(update_missing_recipes()) 