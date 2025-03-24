import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def update_fish_fofos():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Description for Fish fofos
    description = "Traditional Goan fish cakes made with white fish, spices, and herbs, formed into small patties and fried until golden brown. These flavorful seafood bites are crispy on the outside and soft on the inside, perfect as an appetizer or snack with chutney."
    
    # Update the recipe
    result = await recipe_collection.update_one(
        {"name": "Fish fofos"},
        {"$set": {"description": description}}
    )
    
    if result.modified_count > 0:
        print("Successfully updated description for Fish fofos")
    else:
        print("No update made - recipe not found or description already set")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_fish_fofos()) 