import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recipeApi } from '../services/api';

// Hook for fetching recipes
export const useRecipes = (filters?: { ingredients?: string[]; tags?: string[]; cuisine?: string }) => {
  return useQuery({
    queryKey: ['recipes', filters],
    queryFn: () => recipeApi.getRecipes(filters),
  });
};

// Hook for fetching a single recipe
export const useRecipe = (id: string) => {
  return useQuery({
    queryKey: ['recipe', id],
    queryFn: () => recipeApi.getRecipe(id),
    enabled: !!id,
  });
};

// Hook for creating a recipe
export const useCreateRecipe = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (recipe: any) => recipeApi.createRecipe(recipe),
    onSuccess: () => {
      // Invalidate recipes query to refetch the data
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
    },
  });
};

// Hook for updating a recipe
export const useUpdateRecipe = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, recipe }: { id: string; recipe: any }) => recipeApi.updateRecipe(id, recipe),
    onSuccess: (data) => {
      // Invalidate specific recipe query
      queryClient.invalidateQueries({ queryKey: ['recipe', data.id] });
      // Invalidate recipes query
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
    },
  });
};

// Hook for deleting a recipe
export const useDeleteRecipe = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => recipeApi.deleteRecipe(id),
    onSuccess: (_, id) => {
      // Invalidate specific recipe query
      queryClient.invalidateQueries({ queryKey: ['recipe', id] });
      // Invalidate recipes query
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
    },
  });
}; 