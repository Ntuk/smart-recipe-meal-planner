import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def update_recipe_descriptions():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
    db = client["recipe_app"]
    recipe_collection = db["recipes"]
    
    # Get all recipes
    recipes = await recipe_collection.find().to_list(length=None)
    print(f"Found {len(recipes)} recipes")
    
    # Dictionary of new descriptions for recipes we already know about
    new_descriptions = {
        "Spaghetti Carbonara": "A classic Italian pasta dish with eggs, cheese, pancetta, and black pepper.",
        "Chicken Stir Fry": "A quick and healthy stir fry with chicken and vegetables.",
        "Vegetable Curry": "A flavorful vegetarian curry with mixed vegetables and spices.",
        "Greek Salad": "A refreshing salad with tomatoes, cucumbers, olives, and feta cheese.",
        "Energizing fruit smoothie": "A refreshing blend of nutrient-rich fruits combined with yogurt or plant milk for a quick energy boost. This vibrant smoothie packs antioxidants, vitamins, and natural sugars to fuel your day, perfect for breakfast or a post-workout refreshment.",
        "Beef and Mustard Pie": "A hearty British pie filled with tender beef chunks in a rich gravy flavored with mustard, topped with golden puff pastry. Perfect comfort food for cold days.",
        "Beef and Oyster pie": "A traditional British dish combining tender beef and fresh oysters in a savory gravy, encased in a flaky pastry crust. The oysters add a subtle seafood flavor that complements the rich beef.",
        "Apple & Blackberry Crumble": "A warm dessert featuring sweet-tart apples and juicy blackberries topped with a crisp, buttery crumble. Serve with custard or ice cream for the perfect ending to any meal.",
        "Ayam Percik": "A Malaysian grilled chicken dish marinated in a spicy sauce of lemongrass, ginger, and coconut milk, then grilled to perfection. The resulting chicken is fragrant, juicy and full of flavor.",
        "Apam balik": "A Malaysian folded pancake dessert filled with crushed peanuts, sugar, and sometimes corn or banana. It has a crispy exterior and soft, sweet interior for a delightful contrast of textures.",
        "Bean & Sausage Hotpot": "A comforting one-pot meal with savory sausages, hearty beans, and vegetables in a rich tomato sauce. This rustic dish is perfect for family dinners on chilly evenings.",
        "Callaloo Jamaican Style": "A traditional Caribbean dish made with leafy callaloo (similar to spinach), simmered with onions, garlic, tomatoes and often seafood. This nutritious and flavorful stew is a staple in Jamaican cuisine.",
        "Chilli prawn linguine": "Al dente linguine pasta tossed with succulent prawns in a spicy tomato sauce with garlic, chili, and fresh herbs. The perfect balance of seafood freshness and piquant heat.",
        "Fettuccine Alfredo": "Silky fettuccine pasta coated in a rich, creamy sauce made with butter, heavy cream, and Parmesan cheese. This indulgent Italian-American classic is simple yet luxurious.",
        "Bubble & Squeak": "A traditional British dish made from leftover vegetables, primarily potatoes and cabbage, pan-fried until crispy on the outside and tender inside. Named for the sounds it makes while cooking.",
        "BBQ Pork Sloppy Joes": "Tender pulled pork simmered in tangy barbecue sauce, served on soft buns. This messy, delicious sandwich is packed with smoky flavor and perfect for casual gatherings.",
        "Baked salmon with fennel & tomatoes": "Fresh salmon fillets baked with aromatic fennel, juicy tomatoes, and herbs. The vegetables create a fragrant bed that infuses the fish with their flavors for a light, healthy meal.",
        "Cajun spiced fish tacos": "Flaky white fish seasoned with bold Cajun spices, served in warm tortillas with crunchy slaw, fresh lime, and creamy sauce. These tacos offer a perfect balance of heat, acidity, and texture.",
        "Blini Pancakes": "Light, fluffy Russian pancakes made with buckwheat flour and yeast for a distinctive flavor. Traditionally topped with sour cream and caviar, these small pancakes make elegant appetizers.",
        "Boulangère Potatoes": "A French dish of thinly sliced potatoes layered with onions and herbs, baked in stock until tender. Less rich than dauphinoise, this dish was traditionally cooked in the baker's oven as families headed to church.",
        "Broccoli & Stilton soup": "A luxurious, creamy soup combining tender broccoli with the distinctive flavor of Stilton cheese. This velvety starter is both comforting and elegant, perfect with crusty bread.",
        "Clam chowder": "A hearty New England soup featuring tender clams, potatoes, and onions in a rich, creamy broth. This classic seafood dish offers comfort in every spoonful.",
        "Roast fennel and aubergine paella": "A vegetarian twist on the Spanish classic, featuring roasted fennel and aubergine with saffron-infused rice. The vegetables develop a delicious caramelized flavor that complements the aromatic rice.",
        # Adding more recipes from the latest screenshot
        "Vegan Chocolate Cake": "A rich, moist chocolate cake made without any animal products. This decadent dessert uses plant-based ingredients to create a chocolatey treat that's just as satisfying as traditional versions.",
        "Baingan Bharta": "A North Indian dish of smoky, mashed eggplant cooked with aromatic spices, tomatoes, and onions. The eggplant is traditionally roasted over an open flame to impart a distinctive charred flavor.",
        "Beetroot Soup (Borscht)": "A vibrant Eastern European soup with deep red color from beets, complemented by cabbage, potatoes, and sometimes meat. Often topped with a dollop of sour cream, it's both hearty and refreshing.",
        "Bread omelette": "A satisfying breakfast combining fluffy eggs with slices of bread cooked together. Popular in many countries, this simple yet filling dish often includes herbs, cheese, or vegetables for added flavor.",
        "Breakfast Potatoes": "Crispy diced potatoes seasoned with herbs and spices, often pan-fried with onions and bell peppers. These savory potatoes make the perfect side dish for any morning meal.",
        "Mbuzi Choma (Roasted Goat)": "A traditional East African dish of marinated goat meat, slow-roasted to perfection. This celebratory dish is known for its tender texture and rich, savory flavor, often served with a spicy relish.",
        "Banana Pancakes": "Fluffy pancakes with sweet banana flavor throughout. The mashed bananas add natural sweetness and moisture to these breakfast treats, often served with maple syrup or honey.",
        "BeaverTails": "A Canadian pastry shaped like a beaver's tail, fried and topped with various sweet toppings like cinnamon sugar, chocolate spread, or fruit. These hand-stretched pastries are a popular festival treat.",
        "Beef Lo Mein": "A Chinese stir-fried noodle dish with tender strips of beef, colorful vegetables, and a savory sauce. The noodles are soft yet slightly chewy, absorbing the rich flavors of the sauce.",
        "Burek": "A Balkan pastry made of thin flaky dough filled with meat, cheese, or vegetables. This savory pie has a crisp exterior and a juicy filling, making it a popular street food and family meal.",
        "Bitterballen (Dutch meatballs)": "Traditional Dutch crispy fried meatballs with a soft, savory meat filling inside. These small, round snacks are typically made with a thick ragout, breaded and deep-fried until golden brown.",
        "Egyptian Fatteh": "A layered Middle Eastern dish with toasted pita bread, rice, meat (often lamb), and a garlicky yogurt sauce. Topped with toasted nuts, this comforting dish is both creamy and crunchy.",
        "Beef Asado": "A Filipino-style braised beef dish simmered in a flavorful tomato-based sauce with soy sauce and citrus. The meat becomes tender and absorbs the sweet-savory flavors of the marinade.",
        "Beef Bourguignon": "A classic French stew featuring beef slowly braised in red wine with carrots, onions, mushrooms, and herbs. This rich, hearty dish exemplifies French country cooking at its finest.",
        "Chicken Quinoa Greek Salad": "A protein-packed salad combining tender chicken, nutritious quinoa, and traditional Greek salad ingredients like feta, olives, and cucumber. Dressed with a lemon-herb vinaigrette for a fresh finish.",
        "Chicken Handi": "A North Indian curry where chicken is cooked in a rich, creamy tomato-based gravy with aromatic spices. Traditionally prepared in a clay pot called 'handi', which infuses the dish with rustic flavors.",
        "Boxty Breakfast": "A traditional Irish potato pancake that combines both mashed and grated potatoes for a unique texture. Often served with bacon, eggs, and sausage for a hearty start to the day.",
        "Budino Di Ricotta": "An Italian dessert similar to cheesecake but lighter in texture, made with ricotta cheese and often flavored with citrus, vanilla, or chocolate. This creamy pudding has ancient Roman origins.",
        "Brown Stew Chicken": "A Caribbean dish of chicken pieces browned then simmered in a rich gravy flavored with browning sauce, herbs, and spices. The long cooking process yields incredibly tender meat and a deeply flavorful sauce.",
        "Chicken Karaage": "Japanese fried chicken marinated in ginger, garlic, and soy sauce, then coated in potato starch and deep-fried. The result is juicy chicken with an ultra-crispy exterior, perfect as an appetizer or main dish.",
        "Home-made Mandazi": "East African fried bread similar to a donut, lightly sweetened and sometimes flavored with cardamom or coconut. These triangular treats have a slightly crisp exterior and soft, airy interior."
    }
    
    update_count = 0
    
    # Update descriptions for recipes that match the names in our dictionary
    for recipe in recipes:
        recipe_name = recipe.get("name")
        current_description = recipe.get("description")
        
        # Check if the recipe needs a description update
        needs_update = False
        
        # If the recipe is in our dictionary, use that description
        if recipe_name in new_descriptions:
            new_description = new_descriptions[recipe_name]
            needs_update = True
        # If the recipe description is missing, identical to name, or very short, generate a generic one
        elif not current_description or current_description.strip() == recipe_name or len(current_description.strip()) < 10:
            category = recipe.get("category", "dish")
            new_description = f"A delicious {category.lower()} featuring {recipe_name.lower()}. This flavorful recipe combines quality ingredients for a satisfying meal."
            needs_update = True
        else:
            # Description exists and seems fine
            continue
            
        if needs_update and current_description != new_description:
            result = await recipe_collection.update_one(
                {"_id": recipe["_id"]},
                {"$set": {"description": new_description}}
            )
            if result.modified_count > 0:
                print(f"Updated description for: {recipe_name}")
                update_count += 1
    
    print(f"Total recipes updated: {update_count}")
    client.close()

if __name__ == "__main__":
    asyncio.run(update_recipe_descriptions()) 