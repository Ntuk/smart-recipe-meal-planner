import { useState, useCallback } from 'react';
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
  const [shoppingLists, setShoppingLists] = useState<ShoppingList[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  const fetchShoppingLists = useCallback(async () => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await shoppingListApiService.getShoppingLists();
      setShoppingLists(response);
    } catch (err) {
      console.error('Error fetching shopping lists:', err);
      setError('Failed to fetch shopping lists');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const createShoppingList = useCallback(async (shoppingListData: any) => {
    if (!isAuthenticated) return null;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await shoppingListApiService.createShoppingList(shoppingListData);
      setShoppingLists(prev => [...prev, response]);
      return response;
    } catch (err) {
      console.error('Error creating shopping list:', err);
      setError('Failed to create shopping list');
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const checkItem = useCallback(async (shoppingListId: string, itemName: string, checked: boolean) => {
    if (!isAuthenticated) return false;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await shoppingListApiService.checkItem(shoppingListId, itemName, checked);
      
      // Update the shopping list in state
      setShoppingLists(prev => 
        prev.map(list => 
          list.id === shoppingListId ? response : list
        )
      );
      
      return true;
    } catch (err) {
      console.error('Error updating item:', err);
      setError('Failed to update item');
      return false;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const deleteShoppingList = useCallback(async (shoppingListId: string) => {
    if (!isAuthenticated) return false;
    
    setLoading(true);
    setError(null);
    
    try {
      await shoppingListApiService.deleteShoppingList(shoppingListId);
      setShoppingLists(prev => prev.filter(list => list.id !== shoppingListId));
      return true;
    } catch (err) {
      console.error('Error deleting shopping list:', err);
      setError('Failed to delete shopping list');
      return false;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  return {
    shoppingLists,
    loading,
    error,
    fetchShoppingLists,
    createShoppingList,
    checkItem,
    deleteShoppingList
  };
}; 