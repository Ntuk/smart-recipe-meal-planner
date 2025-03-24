import { useState, useEffect } from 'react';
import { useLocation, Link, useNavigate, useParams } from 'react-router-dom';
import { useMealPlanning } from '../hooks/useMealPlanning';
import { MealPlan, MealPlanDay, MealPlanMeal, MealPlanRecipe } from '../types';
import { useTranslation } from 'react-i18next';
import { useIngredientTranslation } from '../hooks/useIngredientTranslation';
import { toast } from 'react-hot-toast';
import FormInput from '../components/FormInput';

interface LocationState {
  ingredients?: string[];
  selectedRecipe?: {
    id: string;
    name: string;
    prep_time: number;
    cook_time: number;
    servings: number;
  };
  viewMealPlan?: MealPlan;
}

const MealPlanPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams(); // Get the meal plan ID from URL if present
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
  const [newIngredient, setNewIngredient] = useState('');

  // Load existing meal plans when component mounts
  useEffect(() => {
    fetchMealPlans();
  }, [fetchMealPlans]);

  // Load the specific meal plan when an ID is provided in the URL
  useEffect(() => {
    if (id) {
      const planFromId = mealPlans.find(plan => plan.id === id);
      if (planFromId) {
        setMealPlan(planFromId);
        setShowPlanForm(false);
        
        // Extract all unique ingredients from the recipes
        const allIngredients = new Set<string>();
        
        if (planFromId.days) {
          planFromId.days.forEach(day => {
            day.meals.forEach(meal => {
              meal.recipes.forEach(recipe => {
                if (recipe.ingredients) {
                  recipe.ingredients.forEach(ingredient => {
                    // Handle both string and object ingredients
                    const ingredientName = typeof ingredient === 'string' ? ingredient : ingredient?.name;
                    if (ingredientName) {
                      allIngredients.add(ingredientName);
                    }
                  });
                }
              });
            });
          });
        }
        
        setAvailableIngredients(Array.from(allIngredients));
      }
    }
  }, [id, mealPlans]);

  // When navigated to with state for viewing a meal plan
  useEffect(() => {
    if (state?.viewMealPlan) {
      setMealPlan(state.viewMealPlan);
      setShowPlanForm(false);
      
      if (state.viewMealPlan.available_ingredients) {
        setAvailableIngredients(state.viewMealPlan.available_ingredients);
      } else {
        // Extract ingredients from recipes if available_ingredients is not provided
        const allIngredients = new Set<string>();
        
        if (state.viewMealPlan.days) {
          state.viewMealPlan.days.forEach(day => {
            day.meals.forEach(meal => {
              meal.recipes.forEach(recipe => {
                if (recipe.ingredients) {
                  recipe.ingredients.forEach(ingredient => {
                    // Handle both string and object ingredients
                    const ingredientName = typeof ingredient === 'string' ? ingredient : ingredient?.name;
                    if (ingredientName) {
                      allIngredients.add(ingredientName);
                    }
                  });
                }
              });
            });
          });
        }
        
        setAvailableIngredients(Array.from(allIngredients));
      }
    }
  }, [state]);

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

  // Update the current meal plan view when mealPlans changes
  useEffect(() => {
    // If we're viewing a meal plan and mealPlans array was updated
    if (mealPlan && !showPlanForm && mealPlans.length > 0) {
      // Find the current meal plan in the updated list
      const updatedPlan = mealPlans.find(plan => plan.id === mealPlan.id);
      if (updatedPlan) {
        setMealPlan(updatedPlan);
      }
    }
  }, [mealPlans, mealPlan, showPlanForm]);

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

  const handleDietaryToggle = (preference: string) => {
    setDietaryPreferences(prev => 
      prev.includes(preference) 
        ? prev.filter(p => p !== preference) 
        : [...prev, preference]
    );
  };

  const handleNewPlan = () => {
    setMealPlan(null);
    setShowPlanForm(true);
    setPlanName(t('mealPlan.defaultName', 'My Meal Plan'));
    setDays(7);
    setDietaryPreferences([]);
    setAvailableIngredients([]);
  };

  const handleViewMealPlan = (plan: MealPlan) => {
    setMealPlan(plan);
    setShowPlanForm(false);
    
    // Extract ingredients from the meal plan for display
    if (plan.available_ingredients) {
      setAvailableIngredients(plan.available_ingredients);
    } else {
      // If no available_ingredients, extract from recipes
      const allIngredients = new Set<string>();
      
      if (plan.days) {
        plan.days.forEach(day => {
          day.meals.forEach(meal => {
            meal.recipes.forEach(recipe => {
              if (recipe.ingredients) {
                recipe.ingredients.forEach(ingredient => {
                  // Handle both string and object ingredients
                  const ingredientName = typeof ingredient === 'string' ? ingredient : ingredient?.name;
                  if (ingredientName) {
                    allIngredients.add(ingredientName);
                  }
                });
              }
            });
          });
        });
      }
      
      setAvailableIngredients(Array.from(allIngredients));
    }
  };

  const handleDeleteMealPlan = async (id: string) => {
    try {
      await deleteMealPlan(id);
      toast.success(t('mealPlan.deletedSuccessfully', 'Meal plan deleted successfully'));
      setMealPlan(null);
      setShowPlanForm(false);
    } catch (error) {
      toast.error(t('mealPlan.deleteError', 'Failed to delete meal plan'));
    }
  };

  const handleRemoveIngredient = (ingredient: string) => {
    setAvailableIngredients(prev => prev.filter(i => i !== ingredient));
  };

  const handleAddIngredient = (e: React.FormEvent) => {
    e.preventDefault();
    const input = (e.target as HTMLFormElement).querySelector('#new-ingredient') as HTMLInputElement;
    if (input && input.value.trim()) {
      setAvailableIngredients(prev => [...prev, input.value.trim()]);
      setNewIngredient('');
    }
  };

  const handleGeneratePlan = async () => {
    setIsLoading(true);
    try {
      // Create simplified day structure
      const today = new Date();
      
      // Format dates as YYYY-MM-DD
      const startDate = today.toISOString().split('T')[0];
      
      // Calculate end date
      const endDate = new Date(today);
      endDate.setDate(today.getDate() + days - 1);
      const endDateStr = endDate.toISOString().split('T')[0];
      
      // Create simple days array
      const daysArray = [];
      for (let i = 0; i < days; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() + i);
        const dateStr = date.toISOString().split('T')[0];
        
        daysArray.push({
          date: dateStr,
          meals: [
            { name: "Breakfast", time: "08:00", recipes: [] },
            { name: "Lunch", time: "13:00", recipes: [] },
            { name: "Dinner", time: "19:00", recipes: [] }
          ]
        });
      }
      
      // Create minimal plan structure
      const planData = {
        name: planName,
        start_date: startDate,
        end_date: endDateStr,
        days: daysArray,
        dietary_preferences: dietaryPreferences,
        available_ingredients: availableIngredients,
      };
      
      console.log("Sending meal plan data:", planData);
      const newPlanId = await createMealPlan(planData);
      
      if (newPlanId) {
        toast.success(t('mealPlan.createdSuccessfully', 'Meal plan created successfully'));
        
        // If there's a selected recipe in the state, add it to the plan
        if (state?.selectedRecipe && selectedMealTime) {
          try {
            await addRecipeToMealPlan(newPlanId, state.selectedRecipe, selectedMealTime);
            toast.success(t('mealPlan.recipeAdded', 'Recipe added to meal plan'));
          } catch (error) {
            toast.error(t('mealPlan.recipeAddError', 'Failed to add recipe to meal plan'));
          }
        }
        
        // Find the newly created plan in the list of plans
        await fetchMealPlans();
        const createdPlan = mealPlans.find(plan => plan.id === newPlanId);
        if (createdPlan) {
          setMealPlan(createdPlan);
          setShowPlanForm(false);
        }
      }
    } catch (error) {
      console.error('Error generating meal plan:', error);
      toast.error(t('mealPlan.createError', 'Failed to create meal plan'));
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
  const [selectedDay, setSelectedDay] = useState(1); // Default to Day 1

  const renderMealTimeModal = () => {
    // Calculate the number of days in the current meal plan
    const numberOfDays = mealPlan?.days?.length || 0;
    
    return (
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Select Day and Meal Time</h3>
          
          {/* Day selection */}
          <div className="mb-4">
            <label htmlFor="day-select" className="block text-sm font-medium text-gray-700 mb-1">
              Day
            </label>
            <select
              id="day-select"
              value={selectedDay}
              onChange={(e) => setSelectedDay(parseInt(e.target.value))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-900"
            >
              {Array.from({ length: numberOfDays }, (_, i) => (
                <option key={i+1} value={i+1}>Day {i+1}</option>
              ))}
            </select>
          </div>
          
          {/* Meal time selection */}
          <div className="space-y-2">
            <p className="block text-sm font-medium text-gray-700 mb-1">Meal Time</p>
            {['Breakfast', 'Lunch', 'Dinner'].map((mealTime) => (
              <button
                key={mealTime}
                onClick={() => {
                  // Pass both the day number and meal time when navigating
                  navigate('/recipes', {
                    state: {
                      forMealPlan: mealPlan?.id,
                      mealTime,
                      selectedDay: selectedDay - 1, // Convert to 0-based index
                      currentMealPlan: mealPlan
                    }
                  });
                  setShowMealTimeModal(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md text-sm"
              >
                {mealTime}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowMealTimeModal(false)}
            className="mt-4 w-full px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  };

  // Render existing meal plans list
  const renderMealPlansList = () => {
    if (mealPlans.length === 0) {
      return (
        <div className="bg-white shadow sm:rounded-lg p-6 text-center">
          <p className="text-gray-500">{t('mealPlan.noPlans', 'You have no meal plans yet.')}</p>
        </div>
      );
    }
    
    return (
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h2 className="text-lg font-medium text-gray-900">{t('mealPlan.savedPlans', 'Your Meal Plans')}</h2>
        </div>
        <div className="border-t border-gray-200">
          <ul className="divide-y divide-gray-200">
            {mealPlans.map((plan) => (
              <li key={plan.id} className="px-4 py-4 sm:px-6 flex items-center justify-between">
                <div>
                  <h3 className="text-md font-medium text-blue-600">{plan.name}</h3>
                  <p className="text-sm text-gray-500">
                    {plan.start_date && plan.end_date && 
                      `${new Date(plan.start_date).toLocaleDateString()} to ${new Date(plan.end_date).toLocaleDateString()}`}
                  </p>
                  {(plan as any).notes && <p className="text-sm text-gray-500 mt-1">{(plan as any).notes}</p>}
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
        <FormInput
          label={t('mealPlan.planName', 'Plan Name')}
          type="text"
          value={planName}
          onChange={(e) => setPlanName(e.target.value)}
        />

        <FormInput
          label={t('mealPlan.numberOfDays', 'Number of Days')}
          type="number"
          id="days"
          min="1"
          max="30"
          value={days.toString()}
          onChange={(e) => setDays(parseInt(e.target.value))}
        />

        {state?.selectedRecipe && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('mealPlan.mealTime', 'When to add')} {state.selectedRecipe.name}?
            </label>
            <select
              id="meal-time"
              value={selectedMealTime}
              onChange={(e) => setSelectedMealTime(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-900"
            >
              <option value="Breakfast">Breakfast</option>
              <option value="Lunch">Lunch</option>
              <option value="Dinner">Dinner</option>
            </select>
          </div>
        )}

        <div>
          <span className="block text-sm font-medium text-gray-700 mb-1">{t('mealPlan.dietaryPreferences', 'Dietary Preferences')}</span>
          <div className="mt-2 flex flex-wrap gap-2">
            {dietaryOptions.map((option) => (
              <button
                key={option.id}
                type="button"
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
                  dietaryPreferences.includes(option.id)
                    ? 'bg-blue-100 text-blue-800 border-blue-300'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200 border-gray-200'
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
            <div className="flex">
              <div className="flex-grow">
                <FormInput
                  id="new-ingredient"
                  value={newIngredient}
                  onChange={(e) => setNewIngredient(e.target.value)}
                  placeholder={t('mealPlan.enterIngredient', 'Enter an ingredient')}
                  className="rounded-r-none"
                />
              </div>
              <button
                type="submit"
                className="inline-flex items-center px-3 py-2 border border-l-0 border-blue-600 rounded-r-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {t('common.add')}
              </button>
            </div>
          </form>
          
          {availableIngredients.length > 0 ? (
            <div className="mt-4">
              <ul className="divide-y divide-gray-200 border border-gray-300 rounded-md">
                {availableIngredients.map((ingredient, index) => (
                  <li key={index} className="pl-3 pr-4 py-3 flex items-center justify-between text-sm">
                    <div className="w-0 flex-1 flex items-center">
                      <span className="flex-1 w-0 truncate">
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
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {t('common.cancel', 'Cancel')}
          </button>
          <button
            type="button"
            onClick={handleGeneratePlan}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? t('common.loading') : t('mealPlan.generatePlan', 'Generate Plan')}
          </button>
        </div>
      </div>
    </div>
  );

  // Main render function
  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-2xl font-semibold text-gray-900">{t('mealPlan.title', 'Meal Planner')}</h1>
          
          {!showPlanForm && !mealPlan && (
            <button
              onClick={handleNewPlan}
              className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {t('mealPlan.createNew', 'Create New Plan')}
            </button>
          )}
          
          {mealPlan && !showPlanForm && (
            <div className="flex space-x-2">
              <button
                onClick={() => setShowMealTimeModal(true)}
                className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {t('mealPlan.addRecipe', 'Add Recipe')}
              </button>
              <button
                onClick={() => setMealPlan(null)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {t('common.back', 'Back')}
              </button>
            </div>
          )}
        </div>

        {/* Show meal plan form if creating a new plan */}
        {showPlanForm && renderPlanForm()}

        {/* Show the selected meal plan if there is one */}
        {mealPlan && !showPlanForm && (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">{mealPlan.name}</h2>
              {mealPlan.start_date && mealPlan.end_date && (
                <p className="mt-1 text-sm text-gray-500">
                  {new Date(mealPlan.start_date).toLocaleDateString()} - {new Date(mealPlan.end_date).toLocaleDateString()}
                </p>
              )}
              {(mealPlan as any).notes && <p className="mt-1 text-sm text-gray-500">{(mealPlan as any).notes}</p>}
            </div>
            
            {/* Display meal plan days */}
            <div>
              {mealPlan.days?.map((day, dayIndex) => (
                <div key={dayIndex} className="border-b border-gray-200 last:border-b-0">
                  <div className="px-4 py-3 bg-gray-50">
                    <h3 className="text-md font-medium text-gray-900">
                      {t('mealPlan.day', 'Day')} {dayIndex + 1}: {day.date && new Date(day.date).toLocaleDateString()}
                    </h3>
                    {day.notes && <p className="text-sm text-gray-500">{day.notes}</p>}
                  </div>
                  
                  {/* Display meals for each day */}
                  {day.meals.map((meal, mealIndex) => (
                    <div key={mealIndex} className="px-4 py-3 border-t border-gray-200">
                      <div className="flex justify-between items-center">
                        <h4 className="text-sm font-medium text-gray-900">
                          {meal.name} {meal.time && `(${meal.time})`}
                        </h4>
                        <button
                          onClick={() => {
                            navigate('/recipes', {
                              state: {
                                forMealPlan: mealPlan.id,
                                mealTime: meal.name,
                                selectedDay: dayIndex,
                                currentMealPlan: mealPlan
                              }
                            });
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          {t('mealPlan.addRecipe', 'Add Recipe')}
                        </button>
                      </div>
                      
                      {/* Display recipes for each meal */}
                      <div className="mt-2">
                        {meal.recipes.length > 0 ? (
                          <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
                            {meal.recipes.map((recipe, recipeIndex) => (
                              <li key={recipeIndex} className="px-3 py-2 flex justify-between items-center">
                                <div>
                                  <Link to={`/recipes/${recipe.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-800">
                                    {recipe.name}
                                  </Link>
                                  <p className="text-xs text-gray-500">
                                    {t('recipe.prepTime', 'Prep')}: {recipe.prep_time} min | {t('recipe.cookTime', 'Cook')}: {recipe.cook_time} min
                                  </p>
                                </div>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-gray-500 italic">
                            {t('mealPlan.noRecipes', 'No recipes added for this meal')}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Show the list of meal plans if none is selected */}
        {!mealPlan && !showPlanForm && renderMealPlansList()}
        
        {/* Meal time selection modal */}
        {showMealTimeModal && renderMealTimeModal()}
      </div>
    </div>
  );
};

export default MealPlanPage; 