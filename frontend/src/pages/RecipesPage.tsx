import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMealPlanning } from '../hooks/useMealPlanning';
import { Recipe, IngredientItem, RecipeIngredient } from '../types';
import { toast } from 'react-hot-toast';
import { recipeApiService } from '../services/api';
import FormInput from '../components/FormInput';

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
          typeof ing === 'string' ? ing : (ing.name ? ing : { name: 'Unknown' })
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
  
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Fetch recipes from API when component mounts
  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        setIsLoading(true);
        
        // First fetch recipes from the API
        try {
          const apiRecipes = await recipeApiService.getRecipes();
          
          if (Array.isArray(apiRecipes) && apiRecipes.length > 0) {
            // Convert API format to our app's Recipe format
            const formattedApiRecipes = apiRecipes.map(convertApiRecipeToAppFormat);
            setRecipes(formattedApiRecipes);
          }
        } catch (apiError) {
          console.error('Error fetching recipes from API:', apiError);
          
          // Check localStorage for user-created recipes as a fallback
          const storedRecipesJson = localStorage.getItem('user_created_recipes');
          if (storedRecipesJson) {
            const storedRecipes = JSON.parse(storedRecipesJson);
            if (Array.isArray(storedRecipes) && storedRecipes.length > 0) {
              // Convert to our app's Recipe format
              const formattedRecipes = storedRecipes.map(convertApiRecipeToAppFormat);
              setRecipes(formattedRecipes);
            }
          }
        }
        
        // Also check for the most recently created recipe
        const lastCreatedRecipeJson = localStorage.getItem('last_created_recipe');
        if (lastCreatedRecipeJson) {
          const lastCreatedRecipe = JSON.parse(lastCreatedRecipeJson);
          
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
        console.error('Error loading recipes:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchRecipes();
  }, []);

  // Get unique cuisines, difficulties, and tags from recipes
  const cuisines = [...new Set(recipes.map(recipe => recipe.cuisine))];
  const difficulties = [...new Set(recipes.map(recipe => recipe.difficulty))];
  const allTags = [...new Set(recipes.flatMap(recipe => recipe.tags))];

  // Helper function to get ingredient name regardless of format
  const getIngredientName = (ingredient: RecipeIngredient): string => {
    return typeof ingredient === 'string' ? ingredient : ingredient.name;
  };

  // Filter recipes based on search term and filters
  const filteredRecipes = recipes.filter(recipe => {
    const matchesSearch = searchQuery === '' || 
      recipe.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      recipe.ingredients.some(ingredient => 
        getIngredientName(ingredient).toLowerCase().includes(searchQuery.toLowerCase())
      );
    
    const matchesTags = selectedTags.length === 0 || 
      selectedTags.every(tag => recipe.tags.includes(tag));
    
    return matchesSearch && matchesTags;
  });

  // Handle adding recipe to meal plan
  const handleAddToMealPlan = async (recipe: Recipe) => {
    if (!state?.forMealPlan || !state?.mealTime) {
      navigate('/meal-plans', {
        state: {
          selectedRecipe: {
            id: recipe.id,
            name: recipe.title,
            prep_time: recipe.prep_time_minutes,
            cook_time: recipe.cook_time_minutes,
            servings: recipe.servings
          }
        }
      });
      return;
    }

    try {
      // Convert ingredients to the format expected by the meal planning service
      const ingredientsForMealPlan = recipe.ingredients.map(ing => 
        typeof ing === 'string' ? { name: ing } : ing
      );

      const success = await addRecipeToMealPlan(
        state.forMealPlan,
        {
          id: recipe.id,
          name: recipe.title,
          prep_time: recipe.prep_time_minutes,
          cook_time: recipe.cook_time_minutes,
          servings: recipe.servings,
          ingredients: ingredientsForMealPlan
        },
        state.mealTime,
        state.selectedDay
      );

      if (success) {
        toast.success(t('recipes.addedToMealPlan', 'Recipe added to meal plan'));
        
        if (state.forMealPlan) {
          navigate(`/meal-plans/${state.forMealPlan}`, { replace: true });
        } else {
          navigate('/meal-plans', { replace: true });
        }
      }
    } catch (error) {
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

  // Search icon SVG
  const SearchIcon = () => (
    <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
    </svg>
  );

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
            <Link
              to="/recipes/new"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {t('recipes.createNew', 'Create Recipe')}
            </Link>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mt-6 bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="sm:col-span-2">
              <FormInput
                label={t('common.search')}
                id="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('recipes.searchPlaceholder')}
                icon={<SearchIcon />}
              />
            </div>

            <div className="sm:col-span-2">
              <span className="block text-sm font-medium text-gray-700 mb-1">{t('recipes.tags')}</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => handleTagToggle(tag)}
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      selectedTags.includes(tag)
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200 border border-gray-200'
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
          {isLoading ? (
            <div className="col-span-3 flex justify-center items-center py-12">
              <p className="text-gray-500">{t('common.loading')}</p>
            </div>
          ) : filteredRecipes.length > 0 ? (
            filteredRecipes.map((recipe) => (
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
            ))
          ) : (
            <div className="col-span-3 bg-white overflow-hidden shadow rounded-lg p-6 text-center">
              <p className="text-gray-500">
                {t('recipes.noRecipesFound', 'No recipes found. Try creating a new recipe or adjusting your search filters.')}
              </p>
              <div className="mt-4">
                <Link
                  to="/recipes/new"
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {t('recipes.createNew', 'Create Recipe')}
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecipesPage; 