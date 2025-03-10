import { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useCreateMealPlan } from '../hooks/useMealPlanning';
import { MealPlan, Recipe } from '../types';

// Remove mock recipe data

interface LocationState {
  ingredients?: string[];
}

const MealPlanPage = () => {
  const location = useLocation();
  const state = location.state as LocationState;
  const createMealPlanMutation = useCreateMealPlan();
  
  const [availableIngredients, setAvailableIngredients] = useState<string[]>(state?.ingredients || []);
  const [dietaryPreferences, setDietaryPreferences] = useState<string[]>([]);
  const [days, setDays] = useState(7);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [planName, setPlanName] = useState('My Meal Plan');
  const [missingIngredients, setMissingIngredients] = useState<string[]>([]);

  // Dietary preferences options
  const dietaryOptions = [
    'Vegetarian',
    'Vegan',
    'Gluten-Free',
    'Dairy-Free',
    'Keto',
    'Low-Carb',
    'Paleo',
  ];

  // Handle dietary preference toggle
  const handleDietaryToggle = (preference: string) => {
    setDietaryPreferences(prev => 
      prev.includes(preference) 
        ? prev.filter(p => p !== preference) 
        : [...prev, preference]
    );
  };

  // Handle ingredient removal
  const handleRemoveIngredient = (ingredient: string) => {
    setAvailableIngredients(prev => prev.filter(i => i !== ingredient));
  };

  // Handle ingredient addition
  const handleAddIngredient = (e: React.FormEvent) => {
    e.preventDefault();
    const input = (document.getElementById('new-ingredient') as HTMLInputElement);
    const newIngredient = input.value.trim();
    
    if (newIngredient && !availableIngredients.includes(newIngredient)) {
      setAvailableIngredients(prev => [...prev, newIngredient]);
      input.value = '';
    }
  };

  // Generate meal plan
  const handleGeneratePlan = async () => {
    setIsLoading(true);
    
    try {
      // Create meal plan data
      const mealPlanData = {
        name: planName,
        days: days,
        dietary_preferences: dietaryPreferences,
        available_ingredients: availableIngredients
      };
      
      // Call the API to create a meal plan
      const response = await createMealPlanMutation.mutateAsync(mealPlanData);
      
      // Set the meal plan data
      setMealPlan(response);
      
      // Calculate missing ingredients
      const allRequiredIngredients = new Set(
        response.recipes.flatMap(recipe => recipe.ingredients.map(i => i.toLowerCase()))
      );
      
      const availableIngredientsLower = availableIngredients.map(i => i.toLowerCase());
      const missingIngredientsArray = Array.from(allRequiredIngredients)
        .filter(ingredient => !availableIngredientsLower.some(avail => 
          ingredient.includes(avail) || avail.includes(ingredient)
        ));
      
      setMissingIngredients(missingIngredientsArray);
    } catch (error) {
      console.error('Failed to generate meal plan:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h1 className="text-2xl font-bold text-gray-900">Generate Meal Plan</h1>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Create a personalized meal plan based on your ingredients and preferences
              </p>
            </div>
            
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Plan Settings</h3>
                  
                  <div className="mt-4">
                    <label htmlFor="plan-name" className="block text-sm font-medium text-gray-700">
                      Plan Name
                    </label>
                    <input
                      type="text"
                      id="plan-name"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      value={planName}
                      onChange={(e) => setPlanName(e.target.value)}
                    />
                  </div>
                  
                  <div className="mt-4">
                    <label htmlFor="days" className="block text-sm font-medium text-gray-700">
                      Number of Days
                    </label>
                    <select
                      id="days"
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                      value={days}
                      onChange={(e) => setDays(parseInt(e.target.value))}
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 14].map((d) => (
                        <option key={d} value={d}>
                          {d} {d === 1 ? 'day' : 'days'}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="mt-4">
                    <span className="block text-sm font-medium text-gray-700 mb-2">
                      Dietary Preferences
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {dietaryOptions.map((option) => (
                        <button
                          key={option}
                          type="button"
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            dietaryPreferences.includes(option)
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                          }`}
                          onClick={() => handleDietaryToggle(option)}
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Available Ingredients</h3>
                  
                  <form onSubmit={handleAddIngredient} className="mt-4">
                    <div className="flex">
                      <input
                        type="text"
                        id="new-ingredient"
                        className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="Add an ingredient"
                      />
                      <button
                        type="submit"
                        className="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Add
                      </button>
                    </div>
                  </form>
                  
                  <div className="mt-4">
                    {availableIngredients.length > 0 ? (
                      <div className="bg-gray-50 p-4 rounded-md">
                        <ul className="space-y-2">
                          {availableIngredients.map((ingredient, index) => (
                            <li key={index} className="flex justify-between items-center">
                              <span className="text-sm text-gray-700">{ingredient}</span>
                              <button
                                type="button"
                                className="text-red-600 hover:text-red-900"
                                onClick={() => handleRemoveIngredient(ingredient)}
                              >
                                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                                  <path
                                    fillRule="evenodd"
                                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              </button>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 italic">
                        No ingredients added yet. Add some ingredients to generate a meal plan.
                      </p>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="mt-8 flex justify-center">
                <button
                  type="button"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  onClick={handleGeneratePlan}
                  disabled={isLoading || availableIngredients.length === 0}
                >
                  {isLoading ? 'Generating...' : 'Generate Meal Plan'}
                </button>
              </div>
            </div>
            
            {mealPlan && (
              <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                <h2 className="text-xl font-bold text-gray-900">{planName}</h2>
                
                <div className="mt-6 grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                  {mealPlan.recipes.map((recipe, index) => (
                    <div key={recipe.id} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                      <div className="p-5">
                        <div className="flex justify-between items-start">
                          <h3 className="text-lg font-medium text-gray-900">{recipe.title}</h3>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Day {index + 1}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-500">{recipe.description}</p>
                        <div className="mt-4">
                          <h4 className="text-sm font-medium text-gray-900">Ingredients:</h4>
                          <ul className="mt-2 text-sm text-gray-500 list-disc list-inside">
                            {recipe.ingredients.map((ingredient, idx) => (
                              <li key={idx} className={availableIngredients.some(i => 
                                i.toLowerCase().includes(ingredient.toLowerCase()) || 
                                ingredient.toLowerCase().includes(i.toLowerCase())
                              ) ? '' : 'text-red-500'}>
                                {ingredient}
                                {!availableIngredients.some(i => 
                                  i.toLowerCase().includes(ingredient.toLowerCase()) || 
                                  ingredient.toLowerCase().includes(i.toLowerCase())
                                ) && ' (missing)'}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div className="mt-5">
                          <Link
                            to={`/recipes/${recipe.id}`}
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            View Recipe
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {missingIngredients.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-lg font-medium text-gray-900">Shopping List</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      These ingredients are needed for your meal plan but aren't in your available ingredients.
                    </p>
                    <div className="mt-4 bg-red-50 p-4 rounded-md">
                      <ul className="list-disc pl-5 space-y-1">
                        {missingIngredients.map((ingredient, index) => (
                          <li key={index} className="text-sm text-red-700">
                            {ingredient.charAt(0).toUpperCase() + ingredient.slice(1)}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="mt-4">
                      <Link
                        to="/shopping-list"
                        state={{ ingredients: missingIngredients }}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        Generate Shopping List
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MealPlanPage; 