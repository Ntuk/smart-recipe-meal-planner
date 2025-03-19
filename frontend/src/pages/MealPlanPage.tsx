import { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useMealPlanning } from '../hooks/useMealPlanning';
import { MealPlan } from '../types';
import { useTranslation } from 'react-i18next';
import { useIngredientTranslation } from '../hooks/useIngredientTranslation';
import { toast } from 'react-hot-toast';

// Remove mock recipe data

interface LocationState {
  ingredients?: string[];
}

const MealPlanPage = () => {
  const location = useLocation();
  const state = location.state as LocationState;
  const { createMealPlan } = useMealPlanning();
  const { t } = useTranslation();
  const { translateIngredientName } = useIngredientTranslation();
  
  const [availableIngredients, setAvailableIngredients] = useState<string[]>(state?.ingredients || []);
  const [dietaryPreferences, setDietaryPreferences] = useState<string[]>([]);
  const [days, setDays] = useState(7);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [planName, setPlanName] = useState(t('mealPlan.defaultName', 'My Meal Plan'));
  const [missingIngredients, setMissingIngredients] = useState<string[]>([]);

  // Dietary preferences options
  const dietaryOptions = [
    { id: 'vegetarian', label: t('mealPlan.dietaryOptions.vegetarian', 'Vegetarian') },
    { id: 'vegan', label: t('mealPlan.dietaryOptions.vegan', 'Vegan') },
    { id: 'glutenFree', label: t('mealPlan.dietaryOptions.glutenFree', 'Gluten-Free') },
    { id: 'dairyFree', label: t('mealPlan.dietaryOptions.dairyFree', 'Dairy-Free') },
    { id: 'keto', label: t('mealPlan.dietaryOptions.keto', 'Keto') },
    { id: 'lowCarb', label: t('mealPlan.dietaryOptions.lowCarb', 'Low-Carb') },
    { id: 'paleo', label: t('mealPlan.dietaryOptions.paleo', 'Paleo') },
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
      // Create start and end dates
      const startDate = new Date();
      const endDate = new Date();
      endDate.setDate(startDate.getDate() + days - 1);
      
      // Create meal plan data with proper structure
      const mealPlanData = {
        name: planName,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        days: Array.from({ length: days }, (_, i) => {
          const date = new Date(startDate);
          date.setDate(startDate.getDate() + i);
          return {
            date: date.toISOString().split('T')[0],
            meals: [
              {
                name: "Breakfast",
                time: "08:00",
                recipes: []
              },
              {
                name: "Lunch",
                time: "12:00",
                recipes: []
              },
              {
                name: "Dinner",
                time: "18:00",
                recipes: []
              }
            ]
          };
        }),
        dietary_preferences: dietaryPreferences,
        available_ingredients: availableIngredients,
        notes: `Meal plan for ${days} days with ${dietaryPreferences.length ? dietaryPreferences.join(', ') + ' preferences' : 'no specific preferences'}`
      };
      
      console.log('Submitting meal plan data:', mealPlanData);
      
      // Call the API to create a meal plan
      console.log('Making API call to create meal plan...');
      const response = await createMealPlan(mealPlanData);
      console.log('API response:', response);
      
      if (!response) {
        throw new Error('Failed to create meal plan');
      }
      
      // Set the meal plan data
      setMealPlan(response);
      
      // Calculate missing ingredients from all recipes across all days
      const allRequiredIngredients = new Set(
        response.days.flatMap(day => 
          day.meals.flatMap(meal => 
            meal.recipes.flatMap(recipe => 
              recipe.ingredients?.map(i => i.name.toLowerCase()) || []
            )
          )
        )
      );
      
      const availableIngredientsLower = availableIngredients.map(i => i.toLowerCase());
      const missingIngredientsArray = Array.from(allRequiredIngredients)
        .filter(ingredient => !availableIngredientsLower.some(avail => 
          ingredient.includes(avail) || avail.includes(ingredient)
        ));
      
      setMissingIngredients(missingIngredientsArray);
    } catch (error) {
      console.error('Failed to generate meal plan:', error);
      toast.error(t('mealPlan.generateError', 'Failed to generate meal plan'));
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
              <h1 className="text-2xl font-bold text-gray-900">{t('mealPlan.title')}</h1>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                {t('mealPlan.description', 'Create a personalized meal plan based on your ingredients and preferences')}
              </p>
            </div>
            
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{t('mealPlan.planSettings', 'Plan Settings')}</h3>
                  
                  <div className="mt-4">
                    <label htmlFor="plan-name" className="block text-sm font-medium text-gray-700">
                      {t('mealPlan.planName')}
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
                      {t('mealPlan.days')}
                    </label>
                    <select
                      id="days"
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                      value={days}
                      onChange={(e) => setDays(parseInt(e.target.value))}
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 14].map((d) => (
                        <option key={d} value={d}>
                          {d} {d === 1 ? t('mealPlan.day', 'day') : t('mealPlan.days')}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="mt-4">
                    <span className="block text-sm font-medium text-gray-700">
                      {t('mealPlan.dietaryPreferences', 'Dietary Preferences')}
                    </span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {dietaryOptions.map((option) => (
                        <button
                          key={option.id}
                          type="button"
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            dietaryPreferences.includes(option.id)
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                          }`}
                          onClick={() => handleDietaryToggle(option.id)}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{t('mealPlan.availableIngredients', 'Available Ingredients')}</h3>
                  
                  <form onSubmit={handleAddIngredient} className="mt-4">
                    <div className="flex rounded-md shadow-sm">
                      <input
                        type="text"
                        id="new-ingredient"
                        className="focus:ring-blue-500 focus:border-blue-500 flex-1 block w-full rounded-none rounded-l-md sm:text-sm border-gray-300"
                        placeholder={t('mealPlan.enterIngredient', 'Enter an ingredient')}
                      />
                      <button
                        type="submit"
                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-r-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        {t('common.add')}
                      </button>
                    </div>
                  </form>
                  
                  {availableIngredients.length > 0 ? (
                    <div className="mt-4">
                      <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
                        {availableIngredients.map((ingredient, index) => (
                          <li key={index} className="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
                            <div className="w-0 flex-1 flex items-center">
                              <span className="ml-2 flex-1 w-0 truncate">
                                {translateIngredientName(ingredient)}
                              </span>
                            </div>
                            <div className="ml-4 flex-shrink-0">
                              <button
                                type="button"
                                className="font-medium text-red-600 hover:text-red-500"
                                onClick={() => handleRemoveIngredient(ingredient)}
                              >
                                {t('common.delete')}
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <p className="mt-4 text-sm text-gray-500 italic">
                      {t('mealPlan.noIngredientsAdded', 'No ingredients added yet')}
                    </p>
                  )}
                </div>
              </div>
              
              <div className="mt-8 flex justify-end">
                <button
                  type="button"
                  onClick={handleGeneratePlan}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {isLoading ? t('common.loading') : t('mealPlan.generatePlan', 'Generate Plan')}
                </button>
              </div>
            </div>
            
            {mealPlan && (
              <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                <h2 className="text-xl font-bold text-gray-900">{planName}</h2>
                
                <div className="mt-6 grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                  {mealPlan.days.flatMap((day, dayIndex) => 
                    day.meals.flatMap((meal, mealIndex) => 
                      meal.recipes.map((recipe) => (
                        <div key={`${day.date}-${mealIndex}-${recipe.id}`} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                          <div className="p-5">
                            <div className="flex justify-between items-start">
                              <h3 className="text-lg font-medium text-gray-900">{recipe.name}</h3>
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {t('mealPlan.day', 'Day')} {dayIndex + 1} - {meal.name || `Meal ${mealIndex + 1}`}
                              </span>
                            </div>
                            <p className="mt-1 text-sm text-gray-500">
                              {t('mealPlan.prepTime', 'Prep time')}: {recipe.prep_time} {t('mealPlan.minutes', 'minutes')} | 
                              {t('mealPlan.cookTime', 'Cook time')}: {recipe.cook_time} {t('mealPlan.minutes', 'minutes')} | 
                              {t('mealPlan.servings', 'Servings')}: {recipe.servings}
                            </p>
                            <div className="mt-4">
                              <h4 className="text-sm font-medium text-gray-900">{t('recipes.ingredients')}:</h4>
                              <ul className="mt-2 text-sm text-gray-500 list-disc list-inside">
                                {recipe.ingredients?.map((ingredient, idx) => (
                                  <li key={idx} className={availableIngredients.some(i => 
                                    i.toLowerCase().includes(ingredient.name.toLowerCase()) || 
                                    ingredient.name.toLowerCase().includes(i.toLowerCase())
                                  ) ? '' : 'text-red-500'}>
                                    {translateIngredientName(ingredient.name)}
                                    {!availableIngredients.some(i => 
                                      i.toLowerCase().includes(ingredient.name.toLowerCase()) || 
                                      ingredient.name.toLowerCase().includes(i.toLowerCase())
                                    ) && ` (${t('mealPlan.missing', 'missing')})`}
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <div className="mt-5">
                              <Link
                                to={`/recipes/${recipe.id}`}
                                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                              >
                                {t('recipes.viewRecipe')}
                              </Link>
                            </div>
                          </div>
                        </div>
                      ))
                    )
                  )}
                </div>
                
                {missingIngredients.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-lg font-medium text-gray-900">{t('shoppingList.title')}</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {t('mealPlan.missingIngredientsDescription', 'These ingredients are needed for your meal plan but aren\'t in your available ingredients.')}
                    </p>
                    <div className="mt-4 bg-red-50 p-4 rounded-md">
                      <ul className="list-disc pl-5 space-y-1">
                        {missingIngredients.map((ingredient, index) => (
                          <li key={index} className="text-sm text-red-700">
                            {translateIngredientName(ingredient.charAt(0).toUpperCase() + ingredient.slice(1))}
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
                        {t('mealPlan.generateShoppingList')}
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