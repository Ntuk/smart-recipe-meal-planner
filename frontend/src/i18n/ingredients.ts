// This file contains translations for common ingredients
// The key is the English name of the ingredient (as stored in the database)
// The value is an object with translations for each supported language

export const ingredientTranslations: Record<string, Record<string, string>> = {
  // Dairy & Eggs
  "milk": {
    en: "Milk",
    fi: "Maito",
    sv: "Mjölk"
  },
  "butter": {
    en: "Butter",
    fi: "Voi",
    sv: "Smör"
  },
  "cheese": {
    en: "Cheese",
    fi: "Juusto",
    sv: "Ost"
  },
  "egg": {
    en: "Egg",
    fi: "Kananmuna",
    sv: "Ägg"
  },
  "yogurt": {
    en: "Yogurt",
    fi: "Jogurtti",
    sv: "Yoghurt"
  },
  
  // Meat & Seafood
  "chicken": {
    en: "Chicken",
    fi: "Kana",
    sv: "Kyckling"
  },
  "beef": {
    en: "Beef",
    fi: "Naudanliha",
    sv: "Nötkött"
  },
  "pork": {
    en: "Pork",
    fi: "Sianliha",
    sv: "Fläsk"
  },
  "fish": {
    en: "Fish",
    fi: "Kala",
    sv: "Fisk"
  },
  "salmon": {
    en: "Salmon",
    fi: "Lohi",
    sv: "Lax"
  },
  
  // Produce
  "apple": {
    en: "Apple",
    fi: "Omena",
    sv: "Äpple"
  },
  "banana": {
    en: "Banana",
    fi: "Banaani",
    sv: "Banan"
  },
  "tomato": {
    en: "Tomato",
    fi: "Tomaatti",
    sv: "Tomat"
  },
  "potato": {
    en: "Potato",
    fi: "Peruna",
    sv: "Potatis"
  },
  "onion": {
    en: "Onion",
    fi: "Sipuli",
    sv: "Lök"
  },
  "garlic": {
    en: "Garlic",
    fi: "Valkosipuli",
    sv: "Vitlök"
  },
  "carrot": {
    en: "Carrot",
    fi: "Porkkana",
    sv: "Morot"
  },
  
  // Grains & Pasta
  "rice": {
    en: "Rice",
    fi: "Riisi",
    sv: "Ris"
  },
  "pasta": {
    en: "Pasta",
    fi: "Pasta",
    sv: "Pasta"
  },
  "bread": {
    en: "Bread",
    fi: "Leipä",
    sv: "Bröd"
  },
  "flour": {
    en: "Flour",
    fi: "Jauho",
    sv: "Mjöl"
  },
  
  // Spices & Seasonings
  "salt": {
    en: "Salt",
    fi: "Suola",
    sv: "Salt"
  },
  "pepper": {
    en: "Pepper",
    fi: "Pippuri",
    sv: "Peppar"
  },
  "sugar": {
    en: "Sugar",
    fi: "Sokeri",
    sv: "Socker"
  },
  
  // Oils & Sauces
  "oil": {
    en: "Oil",
    fi: "Öljy",
    sv: "Olja"
  },
  "olive oil": {
    en: "Olive Oil",
    fi: "Oliiviöljy",
    sv: "Olivolja"
  },
  "vinegar": {
    en: "Vinegar",
    fi: "Etikka",
    sv: "Vinäger"
  },
  
  // Canned & Jarred
  "beans": {
    en: "Beans",
    fi: "Pavut",
    sv: "Bönor"
  },
  "tomato sauce": {
    en: "Tomato Sauce",
    fi: "Tomaattikastike",
    sv: "Tomatsås"
  }
};

// Helper function to translate an ingredient name
export const translateIngredient = (ingredientName: string, language: string): string => {
  // Handle undefined or null ingredient names
  if (!ingredientName) {
    return '';
  }
  
  // Convert to lowercase for case-insensitive matching
  const lowerCaseIngredient = ingredientName.toLowerCase();
  
  // Check if we have a translation for this ingredient
  if (ingredientTranslations[lowerCaseIngredient]) {
    // Return the translation for the requested language, or fall back to English
    return ingredientTranslations[lowerCaseIngredient][language] || 
           ingredientTranslations[lowerCaseIngredient].en || 
           ingredientName;
  }
  
  // If no translation is found, return the original ingredient name
  return ingredientName;
}; 