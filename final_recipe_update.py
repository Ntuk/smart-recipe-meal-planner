import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def update_final_recipes():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Final recipes to update
    final_updates = {
        "Beef Rendang": "A rich and spicy Indonesian beef stew made with coconut milk and a blend of aromatic spices. The beef is slowly simmered until tender and the sauce reduces to a thick, flavorful coating.",
        "Corba": "A traditional Turkish soup made with red lentils, vegetables, and spices. This hearty, comforting soup is often seasoned with mint and served with lemon wedges for a bright finish."
    }
    
    update_count = 0
    
    # Update each recipe
    for recipe_name, description in final_updates.items():
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
    asyncio.run(update_final_recipes()) 