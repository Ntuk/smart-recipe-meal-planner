import axios from 'axios';
import { MealPlan } from '../types';

// Create an axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create service-specific axios instances
const authApi = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

const recipeApi = axios.create({
  baseURL: 'http://localhost:8001',
  headers: {
    'Content-Type': 'application/json',
  },
});

const ingredientScannerApi = axios.create({
  baseURL: 'http://localhost:8002',
  headers: {
    'Content-Type': 'application/json',
  },
});

const mealPlanningApi = axios.create({
  baseURL: 'http://localhost:8003',
  headers: {
    'Content-Type': 'application/json',
  },
});

const shoppingListApi = axios.create({
  baseURL: 'http://localhost:8004',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token for all instances
[api, authApi, recipeApi, ingredientScannerApi, mealPlanningApi, shoppingListApi].forEach(instance => {
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );
});

// Authentication Service API
export const authApiService = {
  // Register a new user
  register: async (userData: { username: string; email: string; password: string }) => {
    const response = await authApi.post('/register', userData);
    // Store token in localStorage
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    return response.data;
  },
  
  // Login user
  login: async (credentials: { email: string; password: string }) => {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    const response = await authApi.post('/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    // Store token in localStorage
    if (response.data.access_token) {
        localStorage.setItem('auth_token', response.data.access_token);
    }
    return response.data;
  },
  
  // Logout user
  logout: () => {
    localStorage.removeItem('auth_token');
  },
  
  // Get current user profile
  getProfile: async () => {
    const response = await authApi.get('/profile');
    return response.data;
  },
  
  // Update user profile
  updateProfile: async (profileData: any) => {
    const response = await authApi.put('/profile', profileData);
    return response.data;
  },
  
  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('auth_token');
  },
};

// Recipe Service API
export const recipeApiService = {
  // Get all recipes with optional filters
  getRecipes: async (filters?: { ingredients?: string[]; tags?: string[]; cuisine?: string }) => {
    let params = {};
    
    if (filters) {
      if (filters.ingredients && filters.ingredients.length > 0) {
        params = { ...params, ingredients: filters.ingredients.join(',') };
      }
      
      if (filters.tags && filters.tags.length > 0) {
        params = { ...params, tags: filters.tags.join(',') };
      }
      
      if (filters.cuisine) {
        params = { ...params, cuisine: filters.cuisine };
      }
    }
    
    const response = await recipeApi.get('/recipes', { params });
    return response.data;
  },
  
  // Get a single recipe by ID
  getRecipe: async (id: string) => {
    const response = await recipeApi.get(`/recipes/${id}`);
    return response.data;
  },
  
  // Create a new recipe
  createRecipe: async (recipe: any) => {
    const response = await recipeApi.post('/recipes', recipe);
    return response.data;
  },
  
  // Update a recipe
  updateRecipe: async (id: string, recipe: any) => {
    const response = await recipeApi.put(`/recipes/${id}`, recipe);
    return response.data;
  },
  
  // Delete a recipe
  deleteRecipe: async (id: string) => {
    const response = await recipeApi.delete(`/recipes/${id}`);
    return response.data;
  },
};

// Ingredient Scanner Service API
export const ingredientScannerApiService = {
  // Scan ingredients from an image
  scanIngredients: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await ingredientScannerApi.post('/scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  // Manual input of ingredients
  manualInput: async (text: string) => {
    const response = await ingredientScannerApi.post('/manual-input', { text });
    return response.data;
  },
};

// Meal Planning Service API
export const mealPlanningApiService = {
  // Get all meal plans
  getMealPlans: async (userId?: string) => {
    const params = userId ? { user_id: userId } : {};
    try {
      console.log('Fetching meal plans...');
      // Use the root endpoint which is already set up to return all meal plans
      const response = await mealPlanningApi.get('/api/v1/meal-plans/', { params });
      console.log('Meal plans response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching meal plans:', error);
      if (axios.isAxiosError(error)) {
        console.error('Response status:', error.response?.status);
        console.error('Response data:', error.response?.data);
      }
      return [];
    }
  },
  
  // Get a meal plan by ID
  getMealPlan: async (id: string) => {
    const response = await mealPlanningApi.get(`/api/v1/meal-plans/${id}`);
    return response.data;
  },
  
  // Create a meal plan
  createMealPlan: async (mealPlan: {
    name: string;
    start_date: string;
    end_date: string;
    days: Array<{
      date: string;
      meals: Array<{
        name: string;
        time?: string;
        recipes: Array<{
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
        }>;
        notes?: string;
      }>;
      notes?: string;
    }>;
    notes?: string;
    dietary_preferences?: string[];
    available_ingredients?: string[];
  }) => {
    try {
      console.log('Auth token:', localStorage.getItem('auth_token'));
      const response = await mealPlanningApi.post('/api/v1/meal-plans', mealPlan);
      console.log('Response status:', response.status);
      console.log('Response data:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error creating meal plan:', error);
      if (axios.isAxiosError(error)) {
        console.error('Response status:', error.response?.status);
        console.error('Response data:', error.response?.data);
      }
      throw error;
    }
  },
  
  // Delete a meal plan
  deleteMealPlan: async (id: string) => {
    const response = await mealPlanningApi.delete(`/api/v1/meal-plans/${id}`);
    return response.data;
  },
  
  // Update a meal plan
  updateMealPlan: async (id: string, data: any): Promise<MealPlan> => {
    try {
      console.log('Sending formatted update:', data);
      
      // Format the data to match the backend's expectations
      const formattedUpdate = {
        days: data.days.map((day: any) => ({
          date: typeof day.date === 'string' ? day.date : new Date(day.date).toISOString().split('T')[0],
          meals: day.meals.map((meal: any) => ({
            name: meal.name,
            time: meal.time || '',
            recipes: (meal.recipes || []).map((recipe: any) => ({
              id: recipe.id,
              name: recipe.name,
              prep_time: Number(recipe.prep_time),
              cook_time: Number(recipe.cook_time),
              servings: Number(recipe.servings),
              image_url: recipe.image_url || '',
              ingredients: Array.isArray(recipe.ingredients) 
                ? recipe.ingredients.map((ing: any) => 
                    typeof ing === 'string' ? ing : (ing.name || ''))
                : []
            })),
            notes: meal.notes || ''
          })),
          notes: day.notes || ''
        }))
      };
      
      // Remove any undefined values and ensure all required fields are present
      const cleanFormattedUpdate = JSON.parse(JSON.stringify(formattedUpdate));
      console.log('Formatted update data:', cleanFormattedUpdate);
      
      // Ensure the data is properly formatted for MongoDB
      const mongoUpdate = {
        $set: cleanFormattedUpdate
      };
      
      const response = await mealPlanningApi.put(`/api/v1/meal-plans/${id}`, mongoUpdate);
      return response.data;
    } catch (error) {
      console.error('Error updating meal plan:', error);
      if (axios.isAxiosError(error)) {
        console.error('Response status:', error.response?.status);
        console.error('Response data:', error.response?.data);
      }
      throw error;
    }
  },
};

// Shopping List Service API
export const shoppingListApiService = {
  // Create a shopping list
  createShoppingList: async (shoppingList: {
    name: string;
    items: Array<{
      name: string;
      quantity?: string | null;
      unit?: string | null;
      checked: boolean;
    }>;
    meal_plan_id?: string;
    notes?: string;
    user_id?: string;
  }) => {
    const response = await shoppingListApi.post('/shopping-lists', shoppingList);
    return response.data;
  },
  
  // Get a shopping list by ID
  getShoppingList: async (id: string) => {
    const response = await shoppingListApi.get(`/shopping-lists/${id}`);
    return response.data;
  },
  
  // Get all shopping lists
  getShoppingLists: async (userId?: string) => {
    const params = userId ? { user_id: userId } : {};
    const response = await shoppingListApi.get('/shopping-lists', { params });
    return response.data;
  },
  
  // Update an item in a shopping list
  checkItem: async (shoppingListId: string, ingredient: string, checked: boolean) => {
    const response = await shoppingListApi.put(`/shopping-lists/${shoppingListId}/items/${encodeURIComponent(ingredient)}/check`, { checked });
    return response.data;
  },
  
  // Delete a shopping list
  deleteShoppingList: async (id: string) => {
    const response = await shoppingListApi.delete(`/shopping-lists/${id}`);
    return response.data;
  },
};

export default api; 