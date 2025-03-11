import { useState, useCallback } from 'react';
import { mealPlanningApiService } from '../services/api';
import { useAuth } from './useAuth';

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
}

export const useMealPlanning = () => {
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  const fetchMealPlans = useCallback(async () => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await mealPlanningApiService.getMealPlans();
      setMealPlans(response);
    } catch (err) {
      console.error('Error fetching meal plans:', err);
      setError('Failed to fetch meal plans');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const createMealPlan = useCallback(async (mealPlanData: any) => {
    if (!isAuthenticated) return null;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await mealPlanningApiService.createMealPlan(mealPlanData);
      setMealPlans(prev => [...prev, response]);
      return response;
    } catch (err) {
      console.error('Error creating meal plan:', err);
      setError('Failed to create meal plan');
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const deleteMealPlan = useCallback(async (mealPlanId: string) => {
    if (!isAuthenticated) return false;
    
    setLoading(true);
    setError(null);
    
    try {
      await mealPlanningApiService.deleteMealPlan(mealPlanId);
      setMealPlans(prev => prev.filter(plan => plan.id !== mealPlanId));
      return true;
    } catch (err) {
      console.error('Error deleting meal plan:', err);
      setError('Failed to delete meal plan');
      return false;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  return {
    mealPlans,
    loading,
    error,
    fetchMealPlans,
    createMealPlan,
    deleteMealPlan
  };
}; 