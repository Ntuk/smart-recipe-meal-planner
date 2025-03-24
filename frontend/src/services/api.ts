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
    try {
      console.log('Sending recipe data to API:', recipe);
      
      // Special note for development only:
      // Temporarily using a mock approach since we're having authentication issues
      // Replace with real API call once auth is fixed
      
      // Wait for a moment to simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Generate a random ID for the mock recipe
      const mockResponse = {
        ...recipe,
        id: `temp-${Date.now()}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      console.log('Mocked API response:', mockResponse);
      
      // Store the recipe in localStorage for persistence
      try {
        // Save as most recently created recipe
        localStorage.setItem('last_created_recipe', JSON.stringify(mockResponse));
        
        // Also add to user_created_recipes array
        const existingRecipesJson = localStorage.getItem('user_created_recipes');
        const existingRecipes = existingRecipesJson ? JSON.parse(existingRecipesJson) : [];
        existingRecipes.push(mockResponse);
        localStorage.setItem('user_created_recipes', JSON.stringify(existingRecipes));
        
        console.log('Recipe saved to localStorage');
      } catch (storageError) {
        console.error('Failed to save recipe to localStorage:', storageError);
      }
      
      return mockResponse;
      
      // Original implementation:
      // const response = await recipeApi.post('/recipes', recipe);
      // return response.data;
    } catch (error) {
      console.error('Error creating recipe:', error);
      throw error;
    }
  },
  
  // Update a recipe
  updateRecipe: async (id: string, recipe: any) => {
    try {
      console.log('Updating recipe in localStorage:', id, recipe);
      
      // Find and update the recipe in localStorage
      const userRecipesJson = localStorage.getItem('user_created_recipes');
      if (userRecipesJson) {
        const userRecipes = JSON.parse(userRecipesJson);
        const recipeIndex = userRecipes.findIndex((r: any) => r.id === id);
        
        if (recipeIndex !== -1) {
          // Keep the original id and timestamps
          const originalRecipe = userRecipes[recipeIndex];
          const updatedRecipe = {
            ...recipe,
            id: originalRecipe.id,
            created_at: originalRecipe.created_at,
            updated_at: new Date().toISOString()
          };
          
          // Replace the recipe in the array
          userRecipes[recipeIndex] = updatedRecipe;
          
          // Save back to localStorage
          localStorage.setItem('user_created_recipes', JSON.stringify(userRecipes));
          console.log('Recipe updated in localStorage');
          
          return updatedRecipe;
        } else if (id.startsWith('temp-')) {
          // If it's one of our temp IDs but not found in userRecipes,
          // it could be a mock recipe that we need to save as a new one
          const newRecipe = {
            ...recipe,
            id: id,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          };
          
          userRecipes.push(newRecipe);
          localStorage.setItem('user_created_recipes', JSON.stringify(userRecipes));
          console.log('Added modified mock recipe to localStorage');
          
          return newRecipe;
        }
      }
      
      // If we reach here, either userRecipes doesn't exist or the recipe wasn't found
      // For mock recipes or error cases, just return the recipe with an updated timestamp
      console.log('Creating/updating recipe without localStorage entry');
      return {
        ...recipe,
        id: id,
        updated_at: new Date().toISOString()
      };
      
      // Original implementation:
      // const response = await recipeApi.put(`/recipes/${id}`, recipe);
      // return response.data;
    } catch (error) {
      console.error('Error updating recipe:', error);
      throw error;
    }
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
      console.log('Sending update for meal plan:', id);
      console.log('Update data:', data);
      
      // Remove any undefined values and ensure all required fields are present
      const cleanData = JSON.parse(JSON.stringify(data));
      
      // Send the data directly - let the backend handle MongoDB formatting
      console.log('Sending update data:', cleanData);
      
      const response = await mealPlanningApi.put(`/api/v1/meal-plans/${id}`, cleanData);
      
      // Log the full response for debugging
      console.log('Update meal plan response:', response.data);
      
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