import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mealPlanningApi } from '../services/api';

// Types
interface MealPlanCreate {
  name: string;
  days: number;
  dietary_preferences: string[];
  available_ingredients: string[];
  user_id?: string;
}

// Hook for fetching meal plans
export const useMealPlans = (userId?: string) => {
  return useQuery({
    queryKey: ['meal-plans', userId],
    queryFn: () => mealPlanningApi.getMealPlans(userId),
  });
};

// Hook for fetching a single meal plan
export const useMealPlan = (id: string) => {
  return useQuery({
    queryKey: ['meal-plan', id],
    queryFn: () => mealPlanningApi.getMealPlan(id),
    enabled: !!id,
  });
};

// Hook for creating a meal plan
export const useCreateMealPlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (mealPlan: MealPlanCreate) => mealPlanningApi.createMealPlan(mealPlan),
    onSuccess: () => {
      // Invalidate meal plans query to refetch the data
      queryClient.invalidateQueries({ queryKey: ['meal-plans'] });
    },
  });
};

// Hook for deleting a meal plan
export const useDeleteMealPlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => mealPlanningApi.deleteMealPlan(id),
    onSuccess: (_, id) => {
      // Invalidate specific meal plan query
      queryClient.invalidateQueries({ queryKey: ['meal-plan', id] });
      // Invalidate meal plans query
      queryClient.invalidateQueries({ queryKey: ['meal-plans'] });
    },
  });
}; 