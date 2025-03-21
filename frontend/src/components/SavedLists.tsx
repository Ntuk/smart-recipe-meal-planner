import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useShoppingList } from '../hooks/useShoppingList';
import { useAuthContext } from '../context/AuthContext';

interface SavedList {
  id: string;
  name: string;
  items: any[];
  created_at: string;
}

const SavedLists = () => {
  const [localSavedLists, setLocalSavedLists] = useState<SavedList[]>([]);
  const [showSavedLists, setShowSavedLists] = useState(false);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthContext();
  const { shoppingLists, deleteShoppingList } = useShoppingList();

  useEffect(() => {
    // Only load from localStorage if not authenticated
    if (!isAuthenticated) {
      const lists = JSON.parse(localStorage.getItem('shoppingLists') || '[]');
      setLocalSavedLists(lists);
    }
  }, [isAuthenticated]);

  const handleLoadList = (list: SavedList) => {
    // Navigate to shopping list page with the selected list
    navigate('/shopping-lists', { 
      state: { 
        savedList: list
      } 
    });
  };

  const handleDeleteList = async (id: string) => {
    if (isAuthenticated) {
      // Delete from backend
      await deleteShoppingList(id);
    } else {
      // Remove the list from localStorage
      const updatedLists = localSavedLists.filter(list => list.id !== id);
      localStorage.setItem('shoppingLists', JSON.stringify(updatedLists));
      setLocalSavedLists(updatedLists);
    }
  };

  const lists = isAuthenticated ? shoppingLists || [] : localSavedLists;

  // Always show the component, even when there are no saved lists
  return (
    <div className="mt-4 mb-6">
      {lists.length > 0 ? (
        <>
          <button
            onClick={() => setShowSavedLists(!showSavedLists)}
            className="text-indigo-600 hover:text-indigo-800 flex items-center"
          >
            <span>
              {showSavedLists ? t('common.hide') : t('common.show')} {t('shoppingList.savedLists')} ({lists.length})
            </span>
            <svg 
              className={`ml-1 h-5 w-5 transform ${showSavedLists ? 'rotate-180' : ''} transition-transform`} 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showSavedLists && (
            <div className="mt-2 bg-gray-50 p-4 rounded-md">
              <h3 className="text-lg font-medium text-gray-900 mb-2">{t('shoppingList.savedLists')}</h3>
              <div className="space-y-2">
                {lists.map(list => (
                  <div key={list.id} className="flex justify-between items-center p-3 bg-white rounded-md shadow-sm">
                    <div>
                      <h4 className="font-medium">{list.name}</h4>
                      <p className="text-sm text-gray-500">
                        {list.items.length} {t('shoppingList.items')} • {new Date(list.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleLoadList(list)}
                        className="text-indigo-600 hover:text-indigo-800"
                      >
                        {t('shoppingList.load')}
                      </button>
                      <button
                        onClick={() => handleDeleteList(list.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        {t('common.delete')}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-gray-500 italic">
          {t('shoppingList.noSavedLists')}
        </div>
      )}
    </div>
  );
};

export default SavedLists; 