import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useMealPlanning } from '../hooks/useMealPlanning';
import { toast } from 'react-hot-toast';

// Mock recipe data
const MOCK_RECIPES = [
  {
    id: '1',
    title: 'Spaghetti Carbonara',
    description: 'A classic Italian pasta dish with eggs, cheese, pancetta, and black pepper.',
    ingredients: ['Spaghetti', 'Eggs', 'Pancetta', 'Parmesan cheese', 'Black pepper', 'Salt'],
    instructions: [
      'Cook spaghetti according to package instructions.',
      'In a bowl, whisk eggs and grated cheese.',
      'Cook pancetta until crispy.',
      'Combine pasta, egg mixture, and pancetta. Toss quickly.',
      'Season with black pepper and serve immediately.'
    ],
    prep_time_minutes: 10,
    cook_time_minutes: 15,
    servings: 4,
    tags: ['Italian', 'Pasta', 'Quick'],
    cuisine: 'Italian',
    difficulty: 'Easy',
    nutritional_info: {
      calories: 450,
      protein: 20,
      carbs: 50,
      fat: 18,
    },
  },
  {
    id: '2',
    title: 'Chicken Stir Fry',
    description: 'A quick and healthy stir fry with chicken and vegetables.',
    ingredients: ['Chicken breast', 'Bell peppers', 'Broccoli', 'Carrots', 'Soy sauce', 'Garlic', 'Ginger'],
    instructions: [
      'Slice chicken and vegetables.',
      'Heat oil in a wok or large pan.',
      'Stir-fry chicken until cooked through.',
      'Add vegetables and stir-fry until tender-crisp.',
      'Add sauce and toss to combine.'
    ],
    prep_time_minutes: 15,
    cook_time_minutes: 10,
    servings: 4,
    tags: ['Asian', 'Chicken', 'Quick', 'Healthy'],
    cuisine: 'Asian',
    difficulty: 'Easy',
    nutritional_info: {
      calories: 320,
      protein: 30,
      carbs: 15,
      fat: 12,
    },
  },
  {
    id: '3',
    title: 'Vegetable Curry',
    description: 'A flavorful vegetarian curry with mixed vegetables and spices.',
    ingredients: ['Potatoes', 'Carrots', 'Peas', 'Cauliflower', 'Curry powder', 'Coconut milk', 'Onion', 'Garlic'],
    instructions: [
      'Sauté onions and garlic until soft.',
      'Add curry powder and cook until fragrant.',
      'Add vegetables and stir to coat with spices.',
      'Pour in coconut milk and simmer until vegetables are tender.',
      'Serve with rice or naan bread.'
    ],
    prep_time_minutes: 20,
    cook_time_minutes: 30,
    servings: 6,
    tags: ['Indian', 'Vegetarian', 'Spicy'],
    cuisine: 'Indian',
    difficulty: 'Medium',
    nutritional_info: {
      calories: 280,
      protein: 8,
      carbs: 35,
      fat: 14,
    },
  },
  {
    id: '4',
    title: 'Greek Salad',
    description: 'A refreshing salad with tomatoes, cucumbers, olives, and feta cheese.',
    ingredients: ['Tomatoes', 'Cucumber', 'Red onion', 'Feta cheese', 'Kalamata olives', 'Olive oil', 'Lemon juice'],
    instructions: [
      'Chop tomatoes, cucumber, and red onion.',
      'Combine vegetables in a bowl.',
      'Add crumbled feta cheese and olives.',
      'Drizzle with olive oil and lemon juice.',
      'Season with salt and oregano, then toss to combine.'
    ],
    prep_time_minutes: 15,
    cook_time_minutes: 0,
    servings: 4,
    tags: ['Greek', 'Salad', 'Vegetarian', 'No-cook'],
    cuisine: 'Greek',
    difficulty: 'Easy',
    nutritional_info: {
      calories: 220,
      protein: 7,
      carbs: 10,
      fat: 18,
    },
  },
];

interface Recipe {
  id: string;
  title: string;
  description: string;
  ingredients: string[];
  instructions: string[];
  prep_time_minutes: number;
  cook_time_minutes: number;
  servings: number;
  tags: string[];
  cuisine: string;
  difficulty: string;
  nutritional_info?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
}

const RecipeDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [servings, setServings] = useState(4);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const forMealPlanId = searchParams.get('for_meal_plan');
  const { addRecipeToMealPlan, mealPlans } = useMealPlanning();

  useEffect(() => {
    // Simulate API call to fetch recipe
    setLoading(true);
    
    setTimeout(() => {
      const foundRecipe = MOCK_RECIPES.find(r => r.id === id);
      
      if (foundRecipe) {
        setRecipe(foundRecipe);
        setServings(foundRecipe.servings);
      } else {
        setError('Recipe not found');
      }
      
      setLoading(false);
    }, 500);
  }, [id]);

  const handleAddToMealPlan = async () => {
    if (!recipe) return;
    
    // If we have a meal plan ID from URL parameters, add directly to that meal plan
    if (forMealPlanId) {
      console.log(`Adding recipe ${recipe.id} to meal plan ${forMealPlanId}`);
      const mealPlan = mealPlans.find(plan => plan.id === forMealPlanId);
      
      if (!mealPlan) {
        console.error(`Meal plan with ID ${forMealPlanId} not found in:`, mealPlans);
        toast.error('Meal plan not found');
        return;
      }
      
      // For simplicity, let's add to the first day and first meal (breakfast)
      // In a full implementation, you'd show a UI to select the day and meal
      const recipeToAdd = {
        id: recipe.id,
        name: recipe.title,
        prep_time: recipe.prep_time_minutes,
        cook_time: recipe.cook_time_minutes,
        servings: recipe.servings,
        ingredients: recipe.ingredients
      };
      
      console.log('Adding recipe to meal plan:', recipeToAdd);
      
      const success = await addRecipeToMealPlan(
        forMealPlanId, 
        recipeToAdd, 
        "Breakfast" // Use the meal time string directly
      );
      
      console.log('Recipe addition result:', success);
      
      if (success) {
        toast.success('Recipe added to meal plan');
        navigate('/meal-plan');
      } else {
        toast.error('Failed to add recipe to meal plan');
      }
    } else {
      // If no meal plan ID, navigate to the meal plan page for creation
      navigate('/meal-plan', { 
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
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-3 text-gray-600">Loading recipe...</p>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">{error || 'Something went wrong'}</h3>
          <div className="mt-6">
            <Link
              to="/recipes"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Back to Recipes
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Calculate scaling factor for ingredients based on servings
  const scalingFactor = servings / recipe.servings;

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <div className="flex justify-between items-start">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">{recipe.title}</h1>
                  <p className="mt-1 max-w-2xl text-lg text-gray-500">{recipe.description}</p>
                </div>
                <Link
                  to="/recipes"
                  className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Back to Recipes
                </Link>
              </div>
            </div>
            
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-900">Ingredients</h2>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-700 mr-2">Servings:</span>
                      <div className="flex items-center">
                        <button
                          type="button"
                          onClick={() => setServings(Math.max(1, servings - 1))}
                          className="p-1 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300 focus:outline-none"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                          </svg>
                        </button>
                        <span className="mx-2 text-gray-900 font-medium">{servings}</span>
                        <button
                          type="button"
                          onClick={() => setServings(servings + 1)}
                          className="p-1 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300 focus:outline-none"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <ul className="space-y-2">
                    {recipe.ingredients.map((ingredient, index) => {
                      // Extract quantity if present (e.g., "2 cups flour" -> "2 cups")
                      const match = ingredient.match(/^(\d+(\.\d+)?(\s+\d+\/\d+)?(\s+[a-zA-Z]+)?)\s+(.+)$/);
                      
                      if (match) {
                        const [, quantity, , , , item] = match;
                        // Try to scale the quantity
                        const numericPart = quantity.trim().split(' ')[0];
                        const unitPart = quantity.trim().split(' ').slice(1).join(' ');
                        
                        let scaledQuantity;
                        try {
                          // Handle fractions like "1/2"
                          if (numericPart.includes('/')) {
                            const [numerator, denominator] = numericPart.split('/').map(Number);
                            scaledQuantity = (numerator / denominator) * scalingFactor;
                          } else {
                            scaledQuantity = parseFloat(numericPart) * scalingFactor;
                          }
                          
                          // Format to 1 decimal place if needed
                          scaledQuantity = scaledQuantity % 1 === 0 
                            ? scaledQuantity.toString() 
                            : scaledQuantity.toFixed(1);
                            
                          return (
                            <li key={index} className="text-gray-700">
                              <span className="font-medium">{scaledQuantity} {unitPart}</span> {item}
                            </li>
                          );
                        } catch (e) {
                          // If parsing fails, just show the original
                          return <li key={index} className="text-gray-700">{ingredient}</li>;
                        }
                      }
                      
                      return <li key={index} className="text-gray-700">{ingredient}</li>;
                    })}
                  </ul>
                  
                  <div className="mt-6">
                    <h3 className="text-lg font-medium text-gray-900">Nutrition (per serving)</h3>
                    {recipe.nutritional_info ? (
                      <div className="mt-2 grid grid-cols-4 gap-4 text-center">
                        <div className="bg-gray-50 rounded-lg p-3">
                          <span className="block text-sm font-medium text-gray-500">Calories</span>
                          <span className="block mt-1 text-lg font-semibold text-gray-900">
                            {recipe.nutritional_info.calories}
                          </span>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <span className="block text-sm font-medium text-gray-500">Protein</span>
                          <span className="block mt-1 text-lg font-semibold text-gray-900">
                            {recipe.nutritional_info.protein}g
                          </span>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <span className="block text-sm font-medium text-gray-500">Carbs</span>
                          <span className="block mt-1 text-lg font-semibold text-gray-900">
                            {recipe.nutritional_info.carbs}g
                          </span>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <span className="block text-sm font-medium text-gray-500">Fat</span>
                          <span className="block mt-1 text-lg font-semibold text-gray-900">
                            {recipe.nutritional_info.fat}g
                          </span>
                        </div>
                      </div>
                    ) : (
                      <p className="mt-2 text-sm text-gray-500 italic">Nutritional information not available</p>
                    )}
                  </div>
                </div>
                
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Instructions</h2>
                  <ol className="space-y-4">
                    {recipe.instructions.map((instruction, index) => (
                      <li key={index} className="flex">
                        <span className="flex-shrink-0 h-6 w-6 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-medium text-sm">
                          {index + 1}
                        </span>
                        <span className="ml-3 text-gray-700">{instruction}</span>
                      </li>
                    ))}
                  </ol>
                  
                  <div className="mt-6">
                    <h3 className="text-lg font-medium text-gray-900">Details</h3>
                    <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2">
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Prep Time</dt>
                        <dd className="text-sm text-gray-900">{recipe.prep_time_minutes} minutes</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Cook Time</dt>
                        <dd className="text-sm text-gray-900">{recipe.cook_time_minutes} minutes</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Total Time</dt>
                        <dd className="text-sm text-gray-900">{recipe.prep_time_minutes + recipe.cook_time_minutes} minutes</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Difficulty</dt>
                        <dd className="text-sm text-gray-900">{recipe.difficulty}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Cuisine</dt>
                        <dd className="text-sm text-gray-900">{recipe.cuisine}</dd>
                      </div>
                    </dl>
                  </div>
                  
                  <div className="mt-6">
                    <h3 className="text-lg font-medium text-gray-900">Tags</h3>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {recipe.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-8 flex justify-center space-x-4">
                <button
                  onClick={handleAddToMealPlan}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  {forMealPlanId ? 'Add to Current Meal Plan' : 'Add to Meal Plan'}
                </button>
                <Link
                  to="/shopping-list"
                  state={{ ingredients: recipe.ingredients }}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add to Shopping List
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecipeDetailPage; 