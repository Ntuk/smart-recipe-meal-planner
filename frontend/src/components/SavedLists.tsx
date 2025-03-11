import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface SavedList {
  id: string;
  name: string;
  items: any[];
  created_at: string;
}

const SavedLists = () => {
  const [savedLists, setSavedLists] = useState<SavedList[]>([]);
  const [showSavedLists, setShowSavedLists] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Load saved lists from localStorage
    const lists = JSON.parse(localStorage.getItem('shoppingLists') || '[]');
    setSavedLists(lists);
  }, []);

  const handleLoadList = (list: SavedList) => {
    // Navigate to shopping list page with the selected list
    navigate('/shopping-lists', { 
      state: { 
        savedList: list
      } 
    });
  };

  const handleDeleteList = (id: string) => {
    // Remove the list from localStorage
    const updatedLists = savedLists.filter(list => list.id !== id);
    localStorage.setItem('shoppingLists', JSON.stringify(updatedLists));
    setSavedLists(updatedLists);
  };

  // Always show the component, even when there are no saved lists
  return (
    <div className="mt-4 mb-6">
      {savedLists.length > 0 ? (
        <>
          <button
            onClick={() => setShowSavedLists(!showSavedLists)}
            className="text-indigo-600 hover:text-indigo-800 flex items-center"
          >
            <span>{showSavedLists ? 'Hide' : 'Show'} Saved Lists ({savedLists.length})</span>
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
              <h3 className="text-lg font-medium text-gray-900 mb-2">Your Saved Lists</h3>
              <div className="space-y-2">
                {savedLists.map(list => (
                  <div key={list.id} className="flex justify-between items-center p-3 bg-white rounded-md shadow-sm">
                    <div>
                      <h4 className="font-medium">{list.name}</h4>
                      <p className="text-sm text-gray-500">
                        {list.items.length} items • {new Date(list.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleLoadList(list)}
                        className="text-indigo-600 hover:text-indigo-800"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => handleDeleteList(list.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Delete
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
          No saved shopping lists yet. Create and save a list to see it here.
        </div>
      )}
    </div>
  );
};

export default SavedLists; 