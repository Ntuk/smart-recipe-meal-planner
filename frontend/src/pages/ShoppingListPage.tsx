import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useShoppingList } from '../hooks/useShoppingList';
import { ShoppingListItem } from '../types';
import { v4 as uuidv4 } from 'uuid';
import { useAuthContext } from '../context/AuthContext';
import { toast } from 'react-hot-toast';
import SavedLists from '../components/SavedLists';
import { useTranslation } from 'react-i18next';
import { useIngredientTranslation } from '../hooks/useIngredientTranslation';

interface LocationState {
  ingredients?: string[];
  mealPlanId?: string;
  savedList?: {
    id: string;
    name: string;
    items: ShoppingItem[];
    created_at: string;
  };
}

interface ShoppingItem {
  id: string;
  name: string;
  checked: boolean;
  category?: string;
}

// Helper function to categorize ingredients
const categorizeIngredient = (ingredient: string): string => {
  const categories = {
    'dairyeggs': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'egg', 'parmesan'],
    'meatseafood': ['chicken', 'beef', 'pork', 'fish', 'shrimp', 'salmon', 'tuna', 'bacon', 'sausage', 'pancetta'],
    'produce': ['tomato', 'onion', 'garlic', 'lettuce', 'carrot', 'potato', 'cucumber', 'pepper', 'broccoli', 'spinach', 'cabbage', 'cauliflower', 'peas'],
    'grainspasta': ['rice', 'pasta', 'noodle', 'bread', 'flour', 'cereal', 'oat', 'spaghetti'],
    'spicesseasonings': ['salt', 'pepper', 'oregano', 'basil', 'thyme', 'cumin', 'paprika', 'cinnamon', 'curry', 'ginger'],
    'oilssauces': ['oil', 'vinegar', 'sauce', 'mayonnaise', 'ketchup', 'mustard', 'soy sauce', 'olive oil'],
    'cannedjarred': ['bean', 'soup', 'tuna', 'tomato sauce', 'coconut milk'],
  };

  const lowerIngredient = ingredient.toLowerCase();
  
  for (const [category, keywords] of Object.entries(categories)) {
    if (keywords.some(keyword => lowerIngredient.includes(keyword))) {
      return category;
    }
  }
  
  return 'other';
};

const ShoppingListPage = () => {
  const location = useLocation();
  const state = location.state as LocationState;
  const { isAuthenticated } = useAuthContext();
  const { t } = useTranslation();
  const { translateIngredientName } = useIngredientTranslation();
  
  const { createShoppingList, checkItem, deleteShoppingList, shoppingLists, loading: listsLoading } = useShoppingList();
  
  const [items, setItems] = useState<ShoppingListItem[]>([]);
  const [newItem, setNewItem] = useState('');
  const [listName, setListName] = useState(t('shoppingList.title'));
  const [showChecked, setShowChecked] = useState(true);
  const [shoppingListId, setShoppingListId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Initialize shopping list from passed ingredients or saved list
  useEffect(() => {
    console.log('State from location:', state);
    
    if (state?.savedList) {
      // Load from saved list
      setItems(state.savedList.items);
      setListName(state.savedList.name);
      setShoppingListId(state.savedList.id);
    } else if (state?.ingredients && state.ingredients.length > 0) {
      console.log('Ingredients from ScanPage:', state.ingredients);
      
      const formattedItems = state.ingredients.map(ingredient => ({
        id: uuidv4(),
        name: ingredient,
        checked: false,
        category: categorizeIngredient(ingredient)
      }));
      
      console.log('Formatted items:', formattedItems);
      setItems(formattedItems);
    }
  }, [state]);
  
  // Update items when shopping list data changes
  useEffect(() => {
    if (shoppingListId && shoppingLists) {
      const currentList = shoppingLists.find(list => list.id === shoppingListId);
      if (currentList) {
        const formattedItems = currentList.items.map(item => ({
          id: uuidv4(),
          name: item.name,
          checked: item.checked,
          category: categorizeIngredient(item.name)
        }));
        setItems(formattedItems);
        setListName(currentList.name);
      }
    }
  }, [shoppingListId, shoppingLists]);
  
  // Create a shopping list
  const handleCreateShoppingList = async (mealPlanId: string, ingredients: string[]) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await createShoppingList({
        meal_plan_id: mealPlanId,
        name: listName,
        available_ingredients: []
      });
      
      setShoppingListId(response.id);
    } catch (err) {
      setError('Failed to create shopping list');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleAddItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItem.trim()) return;
    
    const item: ShoppingListItem = {
      id: uuidv4(),
      name: newItem.trim(),
      checked: false,
      category: categorizeIngredient(newItem)
    };
    
    setItems(prev => [...prev, item]);
    setNewItem('');
  };
  
  const toggleItemChecked = async (id: string) => {
    // Optimistically update UI
    setItems(prev => 
      prev.map(item => 
        item.id === id ? { ...item, checked: !item.checked } : item
      )
    );
    
    // If we have a shopping list ID, update the item on the server
    if (shoppingListId) {
      try {
        const itemToToggle = items.find(item => item.id === id);
        if (itemToToggle) {
          await checkItem(
            shoppingListId,
            itemToToggle.name,
            !itemToToggle.checked
          );
        }
      } catch (err) {
        // Revert optimistic update on error
        setItems(prev => 
          prev.map(item => 
            item.id === id ? { ...item, checked: !item.checked } : item
          )
        );
        setError('Failed to update item');
        console.error(err);
      }
    }
  };
  
  // Remove item from the list
  const removeItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };
  
  // Clear all checked items
  const clearCheckedItems = () => {
    setItems(prev => prev.filter(item => !item.checked));
  };
  
  // Group items by category
  const itemsByCategory = items.reduce((acc, item) => {
    if (!showChecked && item.checked) return acc;
    
    const category = item.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(item);
    return acc;
  }, {} as Record<string, ShoppingItem[]>);
  
  // Sort categories for display
  const sortedCategories = Object.keys(itemsByCategory).sort();
  
  // Save shopping list
  const saveShoppingList = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (isAuthenticated) {
        // If user is authenticated, save to backend
        const shoppingListData = {
          name: listName,
          items: items.map(item => ({
            name: item.name,
            quantity: null,
            unit: null,
            checked: item.checked
          }))
        };
        
        const response = await createShoppingList(shoppingListData);
        if (response) {
          setShoppingListId(response.id);
          toast.success(t('shoppingList.savedSuccessfully'));
        }
      } else {
        // If user is not authenticated, save to localStorage
        const savedLists = JSON.parse(localStorage.getItem('shoppingLists') || '[]');
        const newList = {
          id: uuidv4(),
          name: listName,
          items,
          created_at: new Date().toISOString()
        };
        savedLists.push(newList);
        localStorage.setItem('shoppingLists', JSON.stringify(savedLists));
        toast.success(t('shoppingList.savedLocally'));
      }
    } catch (err) {
      console.error('Error saving shopping list:', err);
      setError(t('shoppingList.saveError'));
      toast.error(t('shoppingList.saveError'));
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <div className="flex justify-between items-center">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{t('shoppingList.title')}</h1>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    {t('shoppingList.manage')}
                  </p>
                </div>
                <div className="flex items-center">
                  <label htmlFor="show-checked" className="mr-2 text-sm text-gray-700">
                    {t('shoppingList.showCheckedItems')}
                  </label>
                  <input
                    type="checkbox"
                    id="show-checked"
                    checked={showChecked}
                    onChange={() => setShowChecked(!showChecked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>
            
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              {!isAuthenticated && <SavedLists />}
              
              <div className="mb-6">
                <label htmlFor="list-name" className="block text-sm font-medium text-gray-700">
                  {t('shoppingList.listName')}
                </label>
                <input
                  type="text"
                  id="list-name"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={listName}
                  onChange={(e) => setListName(e.target.value)}
                />
              </div>
              
              <form onSubmit={handleAddItem} className="mb-6">
                <label htmlFor="new-item" className="block text-sm font-medium text-gray-700">
                  {t('shoppingList.addItem')}
                </label>
                <div className="mt-1 flex rounded-md shadow-sm">
                  <input
                    type="text"
                    id="new-item"
                    className="focus:ring-blue-500 focus:border-blue-500 flex-1 block w-full rounded-none rounded-l-md sm:text-sm border-gray-300"
                    placeholder="Enter an item"
                    value={newItem}
                    onChange={(e) => setNewItem(e.target.value)}
                  />
                  <button
                    type="submit"
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-r-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {t('common.add')}
                  </button>
                </div>
              </form>
              
              {items.length === 0 ? (
                <div className="text-center py-12">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No items in your shopping list</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Add some items to your shopping list to get started.
                  </p>
                </div>
              ) : (
                <div>
                  {sortedCategories.map(category => (
                    <div key={category} className="mb-6">
                      <h3 className="text-lg font-medium text-gray-900 mb-3">
                        {t(`categories.${category.toLowerCase()}`)}
                      </h3>
                      <ul className="divide-y divide-gray-200 border-t border-b border-gray-200">
                        {itemsByCategory[category].map(item => (
                          <li key={item.id} className="py-4 flex items-center justify-between">
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={item.checked}
                                onChange={() => toggleItemChecked(item.id)}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                              />
                              <span 
                                className={`ml-3 text-sm ${
                                  item.checked ? 'text-gray-400 line-through' : 'text-gray-700'
                                }`}
                              >
                                {translateIngredientName(item.name)}
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeItem(item.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                  fillRule="evenodd"
                                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                  
                  <div className="mt-6 flex justify-between">
                    <button
                      type="button"
                      onClick={clearCheckedItems}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      {t('shoppingList.clearCheckedItems')}
                    </button>
                    <div className="space-x-2">
                      <button
                        type="button"
                        onClick={saveShoppingList}
                        disabled={isLoading}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        {isLoading ? t('common.loading') : t('shoppingList.saveList')}
                      </button>
                      <button
                        type="button"
                        onClick={() => window.print()}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        {t('shoppingList.printList')}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShoppingListPage; 