import { useState, useEffect, useCallback } from 'react';
import { mealPlanningApiService } from '../services/api';
import { MealPlan, MealPlanDay, Meal, Recipe } from '../types';
import { useAuth } from './useAuth';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

// Types
interface MealPlan {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  days: MealPlanDay[];
}

interface MealPlanDay {
  date: string;
  meals: Meal[];
  notes?: string;
}

interface Meal {
  name: string;
  time?: string;
  recipes: Recipe[];
  notes?: string;
}

interface Recipe {
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
}

interface Day {
  date: string;
  meals: Meal[];
  notes?: string;
}

export const useMealPlanning = () => {
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const { t } = useTranslation();

  const fetchMealPlans = useCallback(async () => {
    if (!user) {
      console.log('No user found, skipping meal plan fetch');
      return;
    }
    try {
      console.log('Fetching meal plans for user:', user.id);
      const response = await mealPlanningApiService.getMealPlans(user.id);
      console.log('Received meal plans response:', response);
      setMealPlans(response);
    } catch (error) {
      console.error('Error fetching meal plans:', error);
      toast.error(t('errors.failedToFetchMealPlans', 'Failed to fetch meal plans'));
    }
  }, [user, t]);

  const createMealPlan = async (mealPlanData: any) => {
    if (!user) {
      toast.error(t('errors.mustBeLoggedIn', 'You must be logged in to create a meal plan'));
      return null;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const newMealPlan = await mealPlanningApiService.createMealPlan(mealPlanData);
      setMealPlans(prev => [...prev, newMealPlan]);
      toast.success(t('success.mealPlanCreated', 'Meal plan created successfully'));
      return newMealPlan;
    } catch (err) {
      console.error('Error creating meal plan:', err);
      setError(t('errors.failedToCreateMealPlan', 'Failed to create meal plan'));
      toast.error(t('errors.failedToCreateMealPlan', 'Failed to create meal plan'));
      return null;
    } finally {
      setLoading(false);
    }
  };

  const deleteMealPlan = async (id: string) => {
    if (!user) {
      toast.error(t('errors.mustBeLoggedIn', 'You must be logged in to delete a meal plan'));
      return false;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await mealPlanningApiService.deleteMealPlan(id);
      setMealPlans(prev => prev.filter(plan => plan.id !== id));
      toast.success(t('success.mealPlanDeleted', 'Meal plan deleted successfully'));
      return true;
    } catch (err) {
      console.error('Error deleting meal plan:', err);
      setError(t('errors.failedToDeleteMealPlan', 'Failed to delete meal plan'));
      toast.error(t('errors.failedToDeleteMealPlan', 'Failed to delete meal plan'));
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Add function to add a recipe to a meal plan
  const addRecipeToMealPlan = useCallback(async (mealPlanId: string, recipe: Recipe, mealTime: string) => {
    if (!user) {
      console.log('No user found, cannot add recipe to meal plan');
      return false;
    }
    console.log('Adding recipe to meal plan:', {
      mealPlanId,
      recipe,
      mealTime,
      currentMealPlans: mealPlans
    });
    
    try {
      // First try to find the meal plan in state
      let mealPlan = mealPlans.find(mp => mp.id === mealPlanId);
      
      // If not found, fetch it
      if (!mealPlan) {
        console.log('Meal plan not found in state, attempting to fetch it');
        try {
          mealPlan = await mealPlanningApiService.getMealPlan(mealPlanId);
          console.log('Fetched meal plan:', mealPlan);
          if (!mealPlan) {
            toast.error(t('errors.mealPlanNotFound', 'Meal plan not found'));
            return false;
          }
          // Update state with the fetched meal plan
          setMealPlans(prev => [...prev, mealPlan]);
        } catch (error) {
          console.error('Error fetching meal plan:', error);
          toast.error(t('errors.failedToFetchMealPlan', 'Failed to fetch meal plan'));
          return false;
        }
      }
      
      console.log('Current meal plans:', mealPlans);
      console.log('Looking for meal plan with ID:', mealPlanId);
      console.log('Looking for meal time:', mealTime);
      
      // Create a deep copy of the days array
      const updatedDays = JSON.parse(JSON.stringify(mealPlan.days));
      
      // Find the first day that has the specified meal time
      const targetDayIndex = updatedDays.findIndex(day => 
        day.meals.some(meal => meal.name === mealTime)
      );
      
      if (targetDayIndex === -1) {
        console.error('No day found with meal time:', mealTime);
        toast.error(t('errors.mealTimeNotFound', 'Meal time not found in meal plan'));
        return false;
      }
      
      const targetDay = updatedDays[targetDayIndex];
      console.log('Target day:', targetDay);
      
      // Find the meal by name
      console.log('Looking for meal with name:', mealTime);
      const mealIndex = targetDay.meals.findIndex(meal => meal.name === mealTime);
      if (mealIndex === -1) {
        console.error('Meal not found:', mealTime);
        toast.error(t('errors.mealNotFound', 'Meal not found in meal plan'));
        return false;
      }
      console.log('Found meal at index:', mealIndex);
      
      // Format the recipe to add
      const formattedRecipe = {
        id: recipe.id,
        name: recipe.name,
        prep_time: Number(recipe.prep_time),
        cook_time: Number(recipe.cook_time),
        servings: Number(recipe.servings),
        image_url: recipe.image_url || '',
        // Important: preserve the original ingredients format
        ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : []
      };
      
      // Add the recipe to the meal
      targetDay.meals[mealIndex].recipes.push(formattedRecipe);
      console.log('Updated day with added recipe:', targetDay);
      
      // Create update data with the full days array
      const updateData = {
        days: updatedDays
      };
      
      // Update the local state immediately to show the change
      setMealPlans(prevPlans => {
        // Create a deep copy of the previous plans
        const updatedPlans = JSON.parse(JSON.stringify(prevPlans));
        // Find the index of the plan being updated
        const planIndex = updatedPlans.findIndex(p => p.id === mealPlanId);
        if (planIndex !== -1) {
          // Replace the days with the updated days
          updatedPlans[planIndex].days = updatedDays;
        }
        return updatedPlans;
      });
      
      // Send update to backend
      console.log('Sending update to server:', updateData);
      try {
        // Send the update without $set - let the backend handle MongoDB formatting
        const updatedPlan = await mealPlanningApiService.updateMealPlan(mealPlanId, updateData);
        console.log('Server response after update:', updatedPlan);
        
        // Verify the recipe was added by checking the returned plan
        let recipeWasAdded = false;
        if (updatedPlan && updatedPlan.days) {
          for (const day of updatedPlan.days) {
            for (const meal of day.meals) {
              if (meal.recipes.some(r => r.id === recipe.id)) {
                recipeWasAdded = true;
                break;
              }
            }
            if (recipeWasAdded) break;
          }
        }
        
        if (recipeWasAdded) {
          toast.success(t('success.recipeAdded', 'Recipe added to meal plan successfully'));
          // Update our state with the server response to ensure consistency
          setMealPlans(prevPlans => {
            const updatedPlans = [...prevPlans];
            const planIndex = updatedPlans.findIndex(p => p.id === mealPlanId);
            if (planIndex !== -1) {
              updatedPlans[planIndex] = updatedPlan;
            }
            return updatedPlans;
          });
          return true;
        } else {
          console.warn('Recipe was not found in the updated plan from server');
          // Force a refresh from server to sync state
          await fetchMealPlans();
          toast.error(t('errors.failedToAddRecipe', 'Recipe may not have been saved correctly'));
          return false;
        }
      } catch (error) {
        console.error('Error during API call to update meal plan:', error);
        toast.error(t('errors.failedToAddRecipe', 'Failed to save recipe to meal plan'));
        // Refresh from server to ensure state is correct
        await fetchMealPlans();
        return false;
      }
    } catch (error) {
      console.error('Error adding recipe to meal plan:', error);
      toast.error(t('errors.failedToAddRecipe', 'Failed to add recipe to meal plan'));
      // Refresh from server to ensure state is correct
      await fetchMealPlans();
      return false;
    }
  }, [user, mealPlans, fetchMealPlans, t]);

  // Fetch meal plans when the hook is initialized
  useEffect(() => {
    if (user) {
      console.log('Fetching meal plans on hook initialization');
      fetchMealPlans();
    }
  }, [user, fetchMealPlans]);

  return {
    mealPlans,
    loading,
    error,
    fetchMealPlans,
    createMealPlan,
    deleteMealPlan,
    addRecipeToMealPlan
  };
}; 