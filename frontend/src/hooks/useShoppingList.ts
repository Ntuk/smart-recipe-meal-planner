import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { shoppingListApi } from '../services/api';

// Types
interface ShoppingListCreate {
  meal_plan_id: string;
  name: string;
  available_ingredients: string[];
  user_id?: string;
}

// Hook for fetching shopping lists
export const useShoppingLists = (userId?: string) => {
  return useQuery({
    queryKey: ['shopping-lists', userId],
    queryFn: () => shoppingListApi.getShoppingLists(userId),
  });
};

// Hook for fetching a single shopping list
export const useShoppingList = (id: string) => {
  return useQuery({
    queryKey: ['shopping-list', id],
    queryFn: () => shoppingListApi.getShoppingList(id),
    enabled: !!id,
  });
};

// Hook for creating a shopping list
export const useCreateShoppingList = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (shoppingList: ShoppingListCreate) => shoppingListApi.createShoppingList(shoppingList),
    onSuccess: () => {
      // Invalidate shopping lists query to refetch the data
      queryClient.invalidateQueries({ queryKey: ['shopping-lists'] });
    },
  });
};

// Hook for checking/unchecking an item in a shopping list
export const useCheckShoppingListItem = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ shoppingListId, ingredient, checked }: { shoppingListId: string; ingredient: string; checked: boolean }) => 
      shoppingListApi.checkItem(shoppingListId, ingredient, checked),
    onSuccess: (_, { shoppingListId }) => {
      // Invalidate specific shopping list query
      queryClient.invalidateQueries({ queryKey: ['shopping-list', shoppingListId] });
    },
  });
};

// Hook for deleting a shopping list
export const useDeleteShoppingList = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => shoppingListApi.deleteShoppingList(id),
    onSuccess: (_, id) => {
      // Invalidate specific shopping list query
      queryClient.invalidateQueries({ queryKey: ['shopping-list', id] });
      // Invalidate shopping lists query
      queryClient.invalidateQueries({ queryKey: ['shopping-lists'] });
    },
  });
}; 