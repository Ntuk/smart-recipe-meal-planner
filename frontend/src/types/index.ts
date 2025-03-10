// Recipe types
export interface Recipe {
  id: string;
  title: string;
  description?: string;
  ingredients: string[];
  instructions: string[];
  prep_time_minutes: number;
  cook_time_minutes: number;
  servings: number;
  tags: string[];
  cuisine?: string;
  difficulty?: string;
  nutritional_info?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
}

export interface RecipeCreate {
  title: string;
  description?: string;
  ingredients: string[];
  instructions: string[];
  prep_time_minutes: number;
  cook_time_minutes: number;
  servings: number;
  tags: string[];
  cuisine?: string;
  difficulty?: string;
  nutritional_info?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
}

// Ingredient Scanner types
export interface IngredientList {
  ingredients: string[];
}

// Meal Plan types
export interface MealPlan {
  id: string;
  name: string;
  recipes: Recipe[];
  days: number;
  created_at?: string;
  dietary_preferences: string[];
}

export interface MealPlanCreate {
  name: string;
  days: number;
  dietary_preferences: string[];
  available_ingredients: string[];
  user_id?: string;
}

// Shopping List types
export interface ShoppingListItem {
  id: string;
  name: string;
  checked: boolean;
  category?: string;
}

export interface ShoppingList {
  id: string;
  meal_plan_id: string;
  name: string;
  items: ShoppingListItem[];
  created_at?: string;
}

export interface ShoppingListCreate {
  meal_plan_id: string;
  name: string;
  available_ingredients: string[];
  user_id?: string;
} 