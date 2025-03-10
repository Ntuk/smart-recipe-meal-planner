import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Authentication Service API
export const authApi = {
  // Register a new user
  register: async (userData: { username: string; email: string; password: string }) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  // Login user
  login: async (credentials: { email: string; password: string }) => {
    const response = await api.post('/auth/login', credentials);
    // Store token in localStorage
    if (response.data.token) {
      localStorage.setItem('auth_token', response.data.token);
    }
    return response.data;
  },
  
  // Logout user
  logout: () => {
    localStorage.removeItem('auth_token');
  },
  
  // Get current user profile
  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },
  
  // Update user profile
  updateProfile: async (profileData: any) => {
    const response = await api.put('/auth/profile', profileData);
    return response.data;
  },
  
  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('auth_token');
  },
};

// Recipe Service API
export const recipeApi = {
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
    
    const response = await api.get('/recipes', { params });
    return response.data;
  },
  
  // Get a single recipe by ID
  getRecipe: async (id: string) => {
    const response = await api.get(`/recipes/${id}`);
    return response.data;
  },
  
  // Create a new recipe
  createRecipe: async (recipe: any) => {
    const response = await api.post('/recipes', recipe);
    return response.data;
  },
  
  // Update a recipe
  updateRecipe: async (id: string, recipe: any) => {
    const response = await api.put(`/recipes/${id}`, recipe);
    return response.data;
  },
  
  // Delete a recipe
  deleteRecipe: async (id: string) => {
    const response = await api.delete(`/recipes/${id}`);
    return response.data;
  },
};

// Ingredient Scanner Service API
export const ingredientScannerApi = {
  // Scan ingredients from an image
  scanIngredients: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/ingredients/scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  // Manual input of ingredients
  manualInput: async (text: string) => {
    const response = await api.post('/ingredients/manual-input', { text });
    return response.data;
  },
};

// Meal Planning Service API
export const mealPlanningApi = {
  // Create a meal plan
  createMealPlan: async (mealPlan: {
    name: string;
    days: number;
    dietary_preferences: string[];
    available_ingredients: string[];
    user_id?: string;
  }) => {
    const response = await api.post('/meal-plans', mealPlan);
    return response.data;
  },
  
  // Get a meal plan by ID
  getMealPlan: async (id: string) => {
    const response = await api.get(`/meal-plans/${id}`);
    return response.data;
  },
  
  // Get all meal plans
  getMealPlans: async (userId?: string) => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/meal-plans', { params });
    return response.data;
  },
  
  // Delete a meal plan
  deleteMealPlan: async (id: string) => {
    const response = await api.delete(`/meal-plans/${id}`);
    return response.data;
  },
};

// Shopping List Service API
export const shoppingListApi = {
  // Create a shopping list
  createShoppingList: async (shoppingList: {
    meal_plan_id: string;
    name: string;
    available_ingredients: string[];
    user_id?: string;
  }) => {
    const response = await api.post('/shopping-lists', shoppingList);
    return response.data;
  },
  
  // Get a shopping list by ID
  getShoppingList: async (id: string) => {
    const response = await api.get(`/shopping-lists/${id}`);
    return response.data;
  },
  
  // Get all shopping lists
  getShoppingLists: async (userId?: string) => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/shopping-lists', { params });
    return response.data;
  },
  
  // Update an item in a shopping list
  checkItem: async (shoppingListId: string, ingredient: string, checked: boolean) => {
    const response = await api.put(`/shopping-lists/${shoppingListId}/items/${encodeURIComponent(ingredient)}/check`, { checked });
    return response.data;
  },
  
  // Delete a shopping list
  deleteShoppingList: async (id: string) => {
    const response = await api.delete(`/shopping-lists/${id}`);
    return response.data;
  },
};

export default api; 