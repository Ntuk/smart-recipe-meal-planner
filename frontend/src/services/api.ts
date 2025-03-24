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
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );
});

// Add response interceptor for debugging
[mealPlanningApi].forEach(instance => {
  instance.interceptors.response.use(
    (response) => {
      console.log(`API Response for ${response.config.url}:`, response.data);
      return response;
    },
    (error) => {
      console.error(`API Error for ${error.config?.url}:`, error);
      return Promise.reject(error);
    }
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
  
  // Get a specific recipe by ID
  getRecipe: async (id: string) => {
    const response = await recipeApi.get(`/recipes/${id}`);
    return response.data;
  },
  
  // Create a new recipe
  createRecipe: async (recipe: any) => {
    try {
      console.log('Sending recipe data to API:', recipe);
      
      // Format the recipe data for the backend API
      const recipeData = {
        name: recipe.name,
        description: recipe.description,
        ingredients: recipe.ingredients.map((ing: any) => ({
          name: ing.name,
          quantity: ing.quantity || '',
          unit: ing.unit || ''
        })),
        steps: recipe.steps.map((step: string, index: number) => ({
          number: index + 1,
          description: step
        })),
        prep_time: recipe.prep_time,
        cook_time: recipe.cook_time,
        servings: recipe.servings,
        tags: recipe.tags,
        cuisine: recipe.cuisine || 'Other',
        difficulty: recipe.difficulty || 'Medium'
      };
      
      const response = await recipeApi.post('/recipes', recipeData);
      console.log('Recipe saved to database:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error creating recipe:', error);
      throw error;
    }
  },
  
  // Update a recipe
  updateRecipe: async (id: string, recipe: any) => {
    try {
      console.log('Updating recipe in database:', id, recipe);
      
      // Format the recipe data for the backend API
      const recipeData = {
        name: recipe.name || recipe.title,
        description: recipe.description,
        ingredients: recipe.ingredients.map((ing: any) => {
          if (typeof ing === 'string') {
            // Parse string ingredient into components
            const match = ing.match(/^(\d+(\.\d+)?(\s+\d+\/\d+)?(\s+[a-zA-Z]+)?)\s+(.+)$/);
            if (match) {
              const [, quantity, , , , name] = match;
              const unitMatch = quantity.match(/\d+(\.\d+)?\s+([a-zA-Z]+)/);
              const unit = unitMatch ? unitMatch[2] : '';
              const numericPart = quantity.replace(unit, '').trim();
              return {
                name: name.trim(),
                quantity: numericPart,
                unit: unit
              };
            }
            return { name: ing, quantity: '', unit: '' };
          } else {
            return {
              name: ing.name,
              quantity: ing.quantity || '',
              unit: ing.unit || ''
            };
          }
        }),
        steps: Array.isArray(recipe.instructions) ? 
          recipe.instructions.map((step: string, index: number) => ({
            number: index + 1,
            description: step
          })) :
          [],
        prep_time: parseInt(recipe.prep_time) || parseInt(recipe.prep_time_minutes) || 0,
        cook_time: parseInt(recipe.cook_time) || parseInt(recipe.cook_time_minutes) || 0,
        servings: parseInt(recipe.servings) || 1,
        tags: recipe.tags,
        cuisine: recipe.cuisine || 'Other',
        difficulty: recipe.difficulty || 'Medium'
      };
      
      // Call the API to update the recipe
      const response = await recipeApi.put(`/recipes/${id}`, recipeData);
      console.log('Recipe updated in database:', response.data);
      return response.data;
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
  getMealPlans: async (userId: string) => {
    try {
      const response = await mealPlanningApi.get(`/api/v1/meal-plans?user_id=${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching meal plans:', error);
      throw error;
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
    days: Array<{
      date: string;
      meals: Array<{
        name: string;
        time?: string;
        recipes: any[];
      }>;
    }>;
    dietary_preferences?: string[];
    available_ingredients?: string[];
    start_date: string;
    end_date: string;
    skip_recipe_assignment?: boolean;
  }) => {
    try {
      // Ensure all recipe arrays are initialized to empty arrays
      const sanitizedMealPlan = {
        ...mealPlan,
        days: mealPlan.days.map(day => ({
          ...day,
          meals: day.meals.map(meal => ({
            ...meal,
            recipes: [] // Always send empty recipes array
          }))
        })),
        skip_recipe_assignment: true // Always skip recipe assignment from backend
      };
      
      console.log('Sending minimal meal plan:', sanitizedMealPlan);
      
      // Set the Authorization header with the token
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      mealPlanningApi.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      console.log('Using auth token:', token);
      
      const response = await mealPlanningApi.post('/api/v1/meal-plans', sanitizedMealPlan);
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
  updateMealPlan: async (id: string, updateData: any) => {
    try {
      console.log(`Updating meal plan ${id} with:`, updateData);
      
      // Set the Authorization header with the token
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('No authentication token found for meal plan update');
        throw new Error('No authentication token found');
      }
      
      mealPlanningApi.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      const response = await mealPlanningApi.put(`/api/v1/meal-plans/${id}`, updateData);
      console.log('Meal plan update response:', response.data);
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