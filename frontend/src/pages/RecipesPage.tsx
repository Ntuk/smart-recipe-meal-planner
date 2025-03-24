import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMealPlanning } from '../hooks/useMealPlanning';
import { Recipe } from '../types';
import { toast } from 'react-hot-toast';

// Mock recipe data
const MOCK_RECIPES = [
  {
    id: '1',
    title: 'Spaghetti Carbonara',
    description: 'A classic Italian pasta dish with eggs, cheese, pancetta, and black pepper.',
    ingredients: ['Spaghetti', 'Eggs', 'Pancetta', 'Parmesan cheese', 'Black pepper', 'Salt'],
    instructions: ['Cook spaghetti according to package instructions', 'Mix eggs and cheese', 'Cook pancetta', 'Combine all ingredients'],
    prep_time_minutes: 10,
    cook_time_minutes: 15,
    servings: 4,
    tags: ['Italian', 'Pasta', 'Quick'],
    cuisine: 'Italian',
    difficulty: 'Easy',
  },
  {
    id: '2',
    title: 'Chicken Stir Fry',
    description: 'A quick and healthy stir fry with chicken and vegetables.',
    ingredients: ['Chicken breast', 'Bell peppers', 'Broccoli', 'Carrots', 'Soy sauce', 'Garlic', 'Ginger'],
    prep_time_minutes: 15,
    cook_time_minutes: 10,
    servings: 4,
    tags: ['Asian', 'Chicken', 'Quick', 'Healthy'],
    cuisine: 'Asian',
    difficulty: 'Easy',
  },
  {
    id: '3',
    title: 'Vegetable Curry',
    description: 'A flavorful vegetarian curry with mixed vegetables and spices.',
    ingredients: ['Potatoes', 'Carrots', 'Peas', 'Cauliflower', 'Curry powder', 'Coconut milk', 'Onion', 'Garlic'],
    prep_time_minutes: 20,
    cook_time_minutes: 30,
    servings: 6,
    tags: ['Indian', 'Vegetarian', 'Spicy'],
    cuisine: 'Indian',
    difficulty: 'Medium',
  },
  {
    id: '4',
    title: 'Greek Salad',
    description: 'A refreshing salad with tomatoes, cucumbers, olives, and feta cheese.',
    ingredients: ['Tomatoes', 'Cucumber', 'Red onion', 'Feta cheese', 'Kalamata olives', 'Olive oil', 'Lemon juice'],
    prep_time_minutes: 15,
    cook_time_minutes: 0,
    servings: 4,
    tags: ['Greek', 'Salad', 'Vegetarian', 'No-cook'],
    cuisine: 'Greek',
    difficulty: 'Easy',
  },
];

interface LocationState {
  forMealPlan?: string;
  mealTime?: string;
  currentMealPlan?: any;
  selectedDay?: number;
}

// Helper function to convert from API recipe format to our app's Recipe format
const convertApiRecipeToAppFormat = (apiRecipe: any): Recipe => {
  return {
    id: apiRecipe.id || `temp-${Date.now()}`,
    title: apiRecipe.name || apiRecipe.title || 'Untitled Recipe',
    description: apiRecipe.description || '',
    ingredients: Array.isArray(apiRecipe.ingredients) 
      ? apiRecipe.ingredients.map((ing: any) => 
          typeof ing === 'string' ? ing : ing.name || ''
        )
      : [],
    instructions: Array.isArray(apiRecipe.steps) 
      ? apiRecipe.steps 
      : (apiRecipe.instructions || []),
    prep_time_minutes: apiRecipe.prep_time || apiRecipe.prep_time_minutes || 0,
    cook_time_minutes: apiRecipe.cook_time || apiRecipe.cook_time_minutes || 0,
    servings: apiRecipe.servings || 4,
    tags: Array.isArray(apiRecipe.tags) ? apiRecipe.tags : [],
    cuisine: apiRecipe.cuisine || 'Other',
    difficulty: apiRecipe.difficulty || 'Medium',
  };
};

const RecipesPage = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState;
  const { addRecipeToMealPlan } = useMealPlanning();
  
  const [recipes, setRecipes] = useState<Recipe[]>(MOCK_RECIPES);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Check localStorage for user-created recipes when component mounts
  useEffect(() => {
    try {
      const storedRecipesJson = localStorage.getItem('user_created_recipes');
      if (storedRecipesJson) {
        const storedRecipes = JSON.parse(storedRecipesJson);
        if (Array.isArray(storedRecipes) && storedRecipes.length > 0) {
          console.log('Found user-created recipes in localStorage:', storedRecipes);
          
          // Convert API format to our app's Recipe format and add to recipes state
          const formattedRecipes = storedRecipes.map(convertApiRecipeToAppFormat);
          setRecipes(prev => {
            // Filter out any recipes that might be duplicates by ID
            const existingIds = prev.map(r => r.id);
            const newRecipes = formattedRecipes.filter(r => !existingIds.includes(r.id));
            return [...prev, ...newRecipes];
          });
        }
      }
      
      // Also check for the most recently created recipe
      const lastCreatedRecipeJson = localStorage.getItem('last_created_recipe');
      if (lastCreatedRecipeJson) {
        const lastCreatedRecipe = JSON.parse(lastCreatedRecipeJson);
        console.log('Found last created recipe in localStorage:', lastCreatedRecipe);
        
        // Convert to app format and add if it's not already in the list
        const formattedRecipe = convertApiRecipeToAppFormat(lastCreatedRecipe);
        setRecipes(prev => {
          if (!prev.some(r => r.id === formattedRecipe.id)) {
            return [...prev, formattedRecipe];
          }
          return prev;
        });
        
        // Clear the last created recipe from localStorage to avoid duplication
        localStorage.removeItem('last_created_recipe');
      }
    } catch (error) {
      console.error('Error loading recipes from localStorage:', error);
    }
  }, []);

  // Get unique cuisines, difficulties, and tags from recipes
  const cuisines = [...new Set(recipes.map(recipe => recipe.cuisine))];
  const difficulties = [...new Set(recipes.map(recipe => recipe.difficulty))];
  const allTags = [...new Set(recipes.flatMap(recipe => recipe.tags))];

  // Filter recipes based on search term and filters
  const filteredRecipes = recipes.filter(recipe => {
    const matchesSearch = searchQuery === '' || 
      recipe.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      recipe.ingredients.some(ingredient => ingredient.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesTags = selectedTags.length === 0 || 
      selectedTags.every(tag => recipe.tags.includes(tag));
    
    return matchesSearch && matchesTags;
  });

  // Handle adding recipe to meal plan
  const handleAddToMealPlan = async (recipe: Recipe) => {
    console.log('Adding recipe to meal plan:', recipe);
    console.log('Current state:', state);
    
    if (!state?.forMealPlan || !state?.mealTime) {
      console.log('No meal plan context, navigating to create new plan');
      navigate('/meal-plans', {
        state: {
          selectedRecipe: {
            id: recipe.id,
            name: recipe.title,
            prep_time: recipe.prep_time_minutes,
            cook_time: recipe.cook_time_minutes,
            servings: recipe.servings,
            ingredients: recipe.ingredients
          }
        }
      });
      return;
    }

    try {
      console.log('Adding recipe to existing meal plan:', state.forMealPlan);
      console.log('Meal time:', state.mealTime);
      console.log('Selected day index:', state.selectedDay);
      
      // Add recipe to existing meal plan
      const success = await addRecipeToMealPlan(
        state.forMealPlan,
        {
          id: recipe.id,
          name: recipe.title,
          prep_time: recipe.prep_time_minutes,
          cook_time: recipe.cook_time_minutes,
          servings: recipe.servings,
          ingredients: recipe.ingredients
        },
        state.mealTime, // Pass the meal time string
        state.selectedDay // Pass the selected day index
      );

      if (success) {
        toast.success(t('recipes.addedToMealPlan', 'Recipe added to meal plan'));
        
        // Use direct navigation to the meal plan page by ID instead of state
        // This ensures we land on the meal plan view even if state is lost
        if (state.forMealPlan) {
          navigate(`/meal-plans/${state.forMealPlan}`, { replace: true });
        } else {
          navigate('/meal-plans', { replace: true });
        }
      }
    } catch (error) {
      console.error('Failed to add recipe to meal plan:', error);
      toast.error(t('recipes.addToMealPlanError', 'Failed to add recipe to meal plan'));
    }
  };

  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag) 
        : [...prev, tag]
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {state?.forMealPlan 
                  ? t('recipes.addToMealPlan', 'Add Recipe to Meal Plan') 
                  : t('recipes.title', 'Recipes')}
              </h1>
              {state?.forMealPlan && (
                <p className="mt-1 text-sm text-gray-500">
                  {t('recipes.selectForMealTime', 'Select a recipe to add to {{mealTime}}', { mealTime: state.mealTime })}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mt-6 bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="sm:col-span-2">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700">
                {t('common.search')}
              </label>
              <input
                type="text"
                id="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder={t('recipes.searchPlaceholder')}
              />
            </div>

            <div className="sm:col-span-2">
              <span className="block text-sm font-medium text-gray-700">{t('recipes.tags')}</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => handleTagToggle(tag)}
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      selectedTags.includes(tag)
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Recipe Grid */}
        <div className="mt-6 grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {filteredRecipes.map((recipe) => (
            <div key={recipe.id} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900">{recipe.title}</h3>
                <p className="mt-1 text-sm text-gray-500">{recipe.description}</p>
                <div className="mt-4 flex space-x-2">
                  <Link
                    to={`/recipes/${recipe.id}`}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {t('recipes.viewRecipe', 'View Recipe')}
                  </Link>
                  <button
                    onClick={() => handleAddToMealPlan(recipe)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    {state?.forMealPlan 
                      ? t('recipes.addToMealTime', 'Add to {{mealTime}}', { mealTime: state.mealTime })
                      : t('recipes.addToMealPlan', 'Add to Meal Plan')}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecipesPage; 