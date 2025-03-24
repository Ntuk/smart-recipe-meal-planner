import { useState, useEffect, useCallback } from 'react';
import { mealPlanningApiService } from '../services/api';
import { useAuth } from './useAuth';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

// Use the types from the imported module instead of redeclaring them
import { MealPlan, MealPlanDay, MealPlanMeal, Recipe } from '../types';

export const useMealPlanning = () => {
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const { t } = useTranslation();

  const fetchMealPlans = useCallback(async () => {
    if (!user) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const plans = await mealPlanningApiService.getMealPlans(user.id);
      setMealPlans(plans);
    } catch (error) {
      console.error('Error fetching meal plans:', error);
      toast.error(t('errors.failedToFetchMealPlans', 'Failed to fetch meal plans'));
    } finally {
      setLoading(false);
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
  const addRecipeToMealPlan = useCallback(async (
    mealPlanId: string, 
    recipe: any, // Use 'any' to accept both Recipe and MealPlanRecipe
    mealTime: string, 
    dayIndex?: number
  ) => {
    if (!user) {
      return false;
    }
    
    try {
      console.log("Adding recipe to meal plan:", { mealPlanId, recipe, mealTime, dayIndex });
      
      // First try to find the meal plan in state
      let mealPlan = mealPlans.find(mp => mp.id === mealPlanId);
      
      // If not found, fetch it
      if (!mealPlan) {
        try {
          const fetchedPlan = await mealPlanningApiService.getMealPlan(mealPlanId);
          if (!fetchedPlan) {
            toast.error(t('errors.mealPlanNotFound', 'Meal plan not found'));
            return false;
          }
          mealPlan = fetchedPlan;
          // Update state with the fetched meal plan
          setMealPlans(prev => [...prev, fetchedPlan]);
        } catch (error) {
          console.error('Error fetching meal plan:', error);
          toast.error(t('errors.failedToFetchMealPlan', 'Failed to fetch meal plan'));
          return false;
        }
      }
      
      // Create a deep copy of the days array
      const updatedDays = JSON.parse(JSON.stringify(mealPlan!.days));
      
      // Determine which day to add the recipe to
      let targetDayIndex: number;
      
      if (dayIndex !== undefined && dayIndex >= 0 && dayIndex < updatedDays.length) {
        // If dayIndex is provided and valid, use that
        targetDayIndex = dayIndex;
      } else {
        // Otherwise fall back to the legacy behavior - first day with the meal time
        targetDayIndex = updatedDays.findIndex((day: MealPlanDay) => 
          day.meals.some((meal: MealPlanMeal) => meal.name === mealTime)
        );
      }
      
      console.log("Target day index:", targetDayIndex);
      
      if (targetDayIndex === -1) {
        console.error('No day found with meal time:', mealTime);
        toast.error(t('errors.mealTimeNotFound', 'Meal time not found in meal plan'));
        return false;
      }
      
      const targetDay = updatedDays[targetDayIndex];
      
      // Find the meal by name
      const mealIndex = targetDay.meals.findIndex((meal: MealPlanMeal) => meal.name === mealTime);
      console.log("Target meal index:", mealIndex, "in meal time:", mealTime);
      
      if (mealIndex === -1) {
        console.error('Meal not found:', mealTime);
        toast.error(t('errors.mealNotFound', 'Meal not found in meal plan'));
        return false;
      }
      
      // Create minimal recipe structure that matches the MealPlanRecipe structure
      const minimalRecipe = {
        id: recipe.id,
        name: recipe.title || '',
        title: recipe.title || '',
        prep_time: Number(recipe.prep_time_minutes) || 0,
        cook_time: Number(recipe.cook_time_minutes) || 0,
        servings: Number(recipe.servings) || 1,
        image_url: recipe.image_url || ''
      };
      
      console.log("Adding recipe to meal:", minimalRecipe);
      
      // Add the recipe to the meal
      targetDay.meals[mealIndex].recipes.push(minimalRecipe);
      
      // Create update data with the full days array
      const updateData = {
        days: updatedDays
      };
      
      console.log("Sending update to backend:", updateData);
      
      // Send the update to the API
      const updatedPlan = await mealPlanningApiService.updateMealPlan(mealPlanId, updateData);
      console.log("Received updated plan from backend:", updatedPlan);
      
      // Update the meal plans state immediately
      setMealPlans(prevPlans => 
        prevPlans.map(plan => 
          plan.id === mealPlanId ? { ...plan, days: updatedDays } : plan
        )
      );
      
      // Show success message
      toast.success(t('success.recipeAddedToMealPlan', 'Recipe added to meal plan'));
      
      return true;
    } catch (error) {
      console.error('Error adding recipe to meal plan:', error);
      toast.error(t('errors.failedToUpdateMealPlan', 'Failed to add recipe to meal plan'));
      return false;
    }
  }, [mealPlans, user, t, toast]);

  useEffect(() => {
    if (user) {
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