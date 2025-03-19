import { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { useMealPlanning } from '../hooks/useMealPlanning';
import { MealPlan, MealPlanDay, MealPlanMeal, MealPlanRecipe } from '../types';
import { useTranslation } from 'react-i18next';
import { useIngredientTranslation } from '../hooks/useIngredientTranslation';
import { toast } from 'react-hot-toast';

// Remove mock recipe data

interface LocationState {
  ingredients?: string[];
  selectedRecipe?: {
    id: string;
    name: string;
    prep_time: number;
    cook_time: number;
    servings: number;
  };
}

const MealPlanPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState;
  const { createMealPlan, fetchMealPlans, mealPlans, deleteMealPlan, addRecipeToMealPlan } = useMealPlanning();
  const { t } = useTranslation();
  const { translateIngredientName } = useIngredientTranslation();
  
  const [availableIngredients, setAvailableIngredients] = useState<string[]>(state?.ingredients || []);
  const [dietaryPreferences, setDietaryPreferences] = useState<string[]>([]);
  const [days, setDays] = useState(7);
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [planName, setPlanName] = useState(t('mealPlan.defaultName', 'My Meal Plan'));
  const [missingIngredients, setMissingIngredients] = useState<string[]>([]);
  const [showPlanForm, setShowPlanForm] = useState(false);
  const [selectedMealTime, setSelectedMealTime] = useState<string>("Breakfast");

  // Load existing meal plans when component mounts
  useEffect(() => {
    console.log("Fetching meal plans on mount...");
    fetchMealPlans().then(() => {
      console.log("Meal plans fetched, checking if we should show form or list...");
    });
  }, [fetchMealPlans]);

  // Set showPlanForm to false when meal plans are loaded and there are plans
  useEffect(() => {
    if (mealPlans.length > 0) {
      setShowPlanForm(false);
    }
  }, [mealPlans]);

  // If there's a selected recipe in the state, show the plan form
  useEffect(() => {
    if (state?.selectedRecipe) {
      setShowPlanForm(true);
    }
  }, [state?.selectedRecipe]);

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

  // Handle showing meal plan form
  const handleNewPlan = () => {
    setShowPlanForm(true);
    setMealPlan(null);
  };

  // Handle viewing a saved meal plan
  const handleViewMealPlan = (plan: MealPlan) => {
    console.log("Viewing meal plan details:", plan);
    console.log("Days in plan:", plan.days);
    if (plan.days) {
      plan.days.forEach((day, i) => {
        console.log(`Day ${i+1} meals:`, day.meals);
        day.meals.forEach((meal, j) => {
          console.log(`Day ${i+1}, Meal ${j+1} recipes:`, meal.recipes);
        });
      });
    }
    setMealPlan(plan);
    setShowPlanForm(false);
  };

  // Handle deleting a meal plan
  const handleDeleteMealPlan = async (id: string) => {
    if (window.confirm(t('mealPlan.confirmDelete', 'Are you sure you want to delete this meal plan?'))) {
      await deleteMealPlan(id);
      fetchMealPlans();
    }
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
      
      // If we have a selected recipe, add it to the meal plan
      if (state?.selectedRecipe && response.id) {
        console.log('Adding selected recipe to new meal plan:', state.selectedRecipe);
        await addRecipeToMealPlan(
          response.id,
          state.selectedRecipe,
          selectedMealTime // Pass the selected meal time directly
        );
      }
      
      // Set the meal plan data
      setMealPlan(response);
      setShowPlanForm(false);
      
      // Calculate missing ingredients from all recipes across all days
      const allRequiredIngredients = new Set<string>(
        response.days.flatMap((day: MealPlanDay) => 
          day.meals.flatMap((meal: MealPlanMeal) => 
            meal.recipes.flatMap((recipe: MealPlanRecipe) => 
              recipe.ingredients?.map(i => i.name.toLowerCase()) || []
            )
          )
        )
      );
      
      const availableIngredientsLower = availableIngredients.map(i => i.toLowerCase());
      const missingIngredientsArray = Array.from(allRequiredIngredients)
        .filter((ingredient: string) => !availableIngredientsLower.some(avail => 
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

  // Add function to handle adding recipes to a plan
  const handleAddRecipesToPlan = (mealTime?: string) => {
    if (!mealPlan?.id) return;
    
    // Navigate to recipes page with meal plan context
    navigate('/recipes', {
      state: {
        forMealPlan: mealPlan.id,
        mealTime: mealTime || 'Breakfast', // Default to breakfast if not specified
        currentMealPlan: mealPlan // Pass the current meal plan for context
      }
    });
  };

  // Add meal time selection modal
  const [showMealTimeModal, setShowMealTimeModal] = useState(false);

  const renderMealTimeModal = () => (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Select Meal Time</h3>
        <div className="space-y-2">
          {['Breakfast', 'Lunch', 'Dinner'].map((mealTime) => (
            <button
              key={mealTime}
              onClick={() => {
                handleAddRecipesToPlan(mealTime);
                setShowMealTimeModal(false);
              }}
              className="w-full text-left px-4 py-2 hover:bg-gray-100 rounded-md"
            >
              {mealTime}
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowMealTimeModal(false)}
          className="mt-4 w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
        >
          Cancel
        </button>
      </div>
    </div>
  );

  // Render existing meal plans list
  const renderMealPlansList = () => {
    if (mealPlans.length === 0) {
      return (
        <div className="bg-white shadow sm:rounded-lg p-6 text-center">
          <p className="text-gray-500">{t('mealPlan.noPlans', 'You have no meal plans yet.')}</p>
          <button
            onClick={handleNewPlan}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {t('mealPlan.createNew', 'Create New Plan')}
          </button>
        </div>
      );
    }
    
    return (
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
          <h2 className="text-lg font-medium text-gray-900">{t('mealPlan.savedPlans', 'Your Meal Plans')}</h2>
          <button
            onClick={handleNewPlan}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {t('mealPlan.createNew', 'Create New Plan')}
          </button>
        </div>
        <div className="border-t border-gray-200">
          <ul className="divide-y divide-gray-200">
            {mealPlans.map((plan) => (
              <li key={plan.id} className="px-4 py-4 sm:px-6 flex items-center justify-between">
                <div>
                  <h3 className="text-md font-medium text-blue-600">{plan.name}</h3>
                  <p className="text-sm text-gray-500">
                    {new Date(plan.start_date).toLocaleDateString()} to {new Date(plan.end_date).toLocaleDateString()}
                  </p>
                  {plan.notes !== undefined && <p className="text-sm text-gray-500 mt-1">{plan.notes}</p>}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleViewMealPlan(plan)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {t('common.view', 'View')}
                  </button>
                  <button
                    onClick={() => handleDeleteMealPlan(plan.id)}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    {t('common.delete', 'Delete')}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  // Add meal time selection to the form
  const renderPlanForm = () => (
    <div className="bg-white shadow sm:rounded-lg p-6">
      <div className="space-y-6">
        <div>
          <label htmlFor="plan-name" className="block text-sm font-medium text-gray-700">
            {t('mealPlan.planName', 'Plan Name')}
          </label>
          <input
            type="text"
            id="plan-name"
            value={planName}
            onChange={(e) => setPlanName(e.target.value)}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        <div>
          <label htmlFor="days" className="block text-sm font-medium text-gray-700">
            {t('mealPlan.numberOfDays', 'Number of Days')}
          </label>
          <input
            type="number"
            id="days"
            min="1"
            max="30"
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        {state?.selectedRecipe && (
          <div>
            <label htmlFor="meal-time" className="block text-sm font-medium text-gray-700">
              {t('mealPlan.mealTime', 'When to add')} {state.selectedRecipe.name}?
            </label>
            <select
              id="meal-time"
              value={selectedMealTime}
              onChange={(e) => setSelectedMealTime(e.target.value)}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            >
              <option value="Breakfast">Breakfast</option>
              <option value="Lunch">Lunch</option>
              <option value="Dinner">Dinner</option>
            </select>
          </div>
        )}

        <div>
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

        <div className="mt-8 flex justify-between">
          <button
            type="button"
            onClick={() => {
              setMealPlan(null);
              setShowPlanForm(false);
            }}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {t('common.cancel', 'Cancel')}
          </button>
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
    </div>
  );

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
            
            {showPlanForm ? (
              renderPlanForm()
            ) : (
              mealPlan ? (
                <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold text-gray-900">{mealPlan.name}</h2>
                    <button
                      onClick={() => {
                        setMealPlan(null);
                        setShowPlanForm(false);
                      }}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      {t('common.backToList', 'Back to List')}
                    </button>
                  </div>
                  
                  <div className="mt-2 text-sm text-gray-500">
                    <p>
                      {new Date(mealPlan.start_date).toLocaleDateString()} to {new Date(mealPlan.end_date).toLocaleDateString()}
                    </p>
                    {mealPlan.notes && <p className="mt-1">{mealPlan.notes}</p>}
                  </div>
                  
                  <div className="mt-6">
                    {(mealPlan.days && mealPlan.days.some(day => day.meals.some(meal => meal.recipes && meal.recipes.length > 0))) ? (
                      <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                        {mealPlan.days.flatMap((day: MealPlanDay, dayIndex: number) => 
                          day.meals.flatMap((meal: MealPlanMeal, mealIndex: number) => 
                            meal.recipes.map((recipe: MealPlanRecipe) => (
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
                                      {recipe.ingredients?.map((ingredient: any, idx: number) => (
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
                    ) : (
                      <div className="bg-white p-6 rounded-lg shadow">
                        <h3 className="text-lg font-medium text-gray-900">Meal Schedule</h3>
                        <div className="mt-4">
                          {mealPlan.days && mealPlan.days.map((day, dayIndex) => (
                            <div key={dayIndex} className="mb-6 border-b pb-4">
                              <h4 className="font-medium">Day {dayIndex + 1}: {new Date(day.date).toLocaleDateString()}</h4>
                              {day.meals.map((meal, mealIndex) => (
                                <div key={mealIndex} className="ml-4 mt-2">
                                  <h5 className="font-medium">{meal.name} {meal.time && `(${meal.time})`}</h5>
                                  {meal.recipes && meal.recipes.length > 0 ? (
                                    <ul className="list-disc ml-6">
                                      {meal.recipes.map((recipe, recipeIndex) => (
                                        <li key={recipeIndex}>{recipe.name}</li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p className="text-sm text-gray-500 ml-6">No recipes scheduled</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                        <div className="mt-4 flex justify-center">
                          <button
                            onClick={() => setShowMealTimeModal(true)}
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none"
                          >
                            Add Recipes to this Plan
                          </button>
                        </div>
                      </div>
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
              ) : (
                // Show list of meal plans
                renderMealPlansList()
              )
            )}
          </div>
        </div>
      </div>
      {showMealTimeModal && renderMealTimeModal()}
    </div>
  );
};

export default MealPlanPage; 