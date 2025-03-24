// Recipe types
export interface IngredientItem {
  name: string;
  quantity?: string;
  unit?: string;
}

export type RecipeIngredient = string | IngredientItem;

export interface Recipe {
  id: string;
  title: string;
  description?: string;
  ingredients: RecipeIngredient[];
  instructions: string[];
  prep_time_minutes: number;
  cook_time_minutes: number;
  servings: number;
  tags: string[];
  cuisine?: string;
  difficulty?: string;
  image_url?: string;
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
  ingredients: RecipeIngredient[];
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
export interface MealPlanRecipe {
  id: string;
  name: string;
  prep_time: number;
  cook_time: number;
  servings: number;
  image_url?: string;
  ingredients?: Array<{
    name: string;
    quantity?: string;
    unit?: string;
  }>;
}

export interface MealPlanMeal {
  name: string;
  time?: string;
  recipes: MealPlanRecipe[];
  notes?: string;
}

export interface MealPlanDay {
  date: string;
  meals: MealPlanMeal[];
  notes?: string;
}

export interface MealPlan {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  days: MealPlanDay[];
  dietary_preferences?: string[];
  available_ingredients?: string[];
  notes?: string;
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