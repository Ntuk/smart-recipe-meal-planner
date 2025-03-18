import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { shoppingListApiService } from '../services/api';
import { useAuth } from './useAuth';

// Types
interface ShoppingListItem {
  name: string;
  quantity?: string;
  unit?: string;
  checked: boolean;
}

interface ShoppingList {
  id: string;
  name: string;
  items: ShoppingListItem[];
  meal_plan_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export const useShoppingList = () => {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  // Fetch shopping lists
  const { data: shoppingLists, isLoading, error } = useQuery({
    queryKey: ['shoppingLists'],
    queryFn: () => shoppingListApiService.getShoppingLists(),
    enabled: isAuthenticated,
  });

  // Create shopping list mutation
  const createMutation = useMutation({
    mutationFn: (shoppingListData: any) => shoppingListApiService.createShoppingList(shoppingListData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shoppingLists'] });
    },
  });

  // Check item mutation
  const checkMutation = useMutation({
    mutationFn: ({ shoppingListId, itemName, checked }: { shoppingListId: string; itemName: string; checked: boolean }) =>
      shoppingListApiService.checkItem(shoppingListId, itemName, checked),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shoppingLists'] });
    },
  });

  // Delete shopping list mutation
  const deleteMutation = useMutation({
    mutationFn: (shoppingListId: string) => shoppingListApiService.deleteShoppingList(shoppingListId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shoppingLists'] });
    },
  });

  const createShoppingList = async (shoppingListData: any) => {
    if (!isAuthenticated) return null;
    try {
      const response = await createMutation.mutateAsync(shoppingListData);
      return response;
    } catch (err) {
      console.error('Error creating shopping list:', err);
      return null;
    }
  };

  const checkItem = async (shoppingListId: string, itemName: string, checked: boolean) => {
    if (!isAuthenticated) return false;
    try {
      await checkMutation.mutateAsync({ shoppingListId, itemName, checked });
      return true;
    } catch (err) {
      console.error('Error updating item:', err);
      return false;
    }
  };

  const deleteShoppingList = async (shoppingListId: string) => {
    if (!isAuthenticated) return false;
    try {
      await deleteMutation.mutateAsync(shoppingListId);
      return true;
    } catch (err) {
      console.error('Error deleting shopping list:', err);
      return false;
    }
  };

  return {
    shoppingLists,
    loading: isLoading || createMutation.isPending || checkMutation.isPending || deleteMutation.isPending,
    error: error || createMutation.error || checkMutation.error || deleteMutation.error,
    createShoppingList,
    checkItem,
    deleteShoppingList
  };
}; 