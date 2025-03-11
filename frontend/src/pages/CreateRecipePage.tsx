import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface Ingredient {
  name: string;
  quantity: string | null;
  unit: string | null;
}

const CreateRecipePage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  // Initialize form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [newIngredient, setNewIngredient] = useState({ name: '', quantity: '', unit: '' });
  const [instructions, setInstructions] = useState('');
  const [prepTime, setPrepTime] = useState('');
  const [cookTime, setCookTime] = useState('');
  const [servings, setServings] = useState('');
  const [tags, setTags] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Get ingredients from location state if available
  useEffect(() => {
    if (location.state?.ingredients) {
      setIngredients(location.state.ingredients);
    }
  }, [location.state]);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      // Instead of redirecting, we'll show a message
      setError('You must be logged in to create a recipe. Please log in first.');
    }
  }, [isAuthenticated]);
  
  const handleAddIngredient = () => {
    if (!newIngredient.name.trim()) return;
    
    setIngredients([...ingredients, {
      name: newIngredient.name,
      quantity: newIngredient.quantity || null,
      unit: newIngredient.unit || null
    }]);
    
    setNewIngredient({ name: '', quantity: '', unit: '' });
  };
  
  const handleRemoveIngredient = (index: number) => {
    const updatedIngredients = [...ingredients];
    updatedIngredients.splice(index, 1);
    setIngredients(updatedIngredients);
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Recipe title is required');
      return;
    }
    
    if (ingredients.length === 0) {
      setError('At least one ingredient is required');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // In a real app, you would call an API to save the recipe
      // For now, we'll just simulate success and navigate back to recipes
      
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Navigate back to recipes page
      navigate('/recipes');
    } catch (err) {
      console.error('Error creating recipe:', err);
      setError('Failed to create recipe');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Create New Recipe</h1>
      
      {error && (
        <div className="mb-6 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Recipe Title*
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            placeholder="Enter recipe title"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            placeholder="Enter recipe description"
            rows={3}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ingredients*
          </label>
          
          <div className="mb-4">
            <div className="flex space-x-2 mb-2">
              <input
                type="text"
                value={newIngredient.name}
                onChange={(e) => setNewIngredient({...newIngredient, name: e.target.value})}
                className="flex-grow p-2 border border-gray-300 rounded-md"
                placeholder="Ingredient name"
              />
              <input
                type="text"
                value={newIngredient.quantity}
                onChange={(e) => setNewIngredient({...newIngredient, quantity: e.target.value})}
                className="w-24 p-2 border border-gray-300 rounded-md"
                placeholder="Qty"
              />
              <input
                type="text"
                value={newIngredient.unit}
                onChange={(e) => setNewIngredient({...newIngredient, unit: e.target.value})}
                className="w-24 p-2 border border-gray-300 rounded-md"
                placeholder="Unit"
              />
              <button
                type="button"
                onClick={handleAddIngredient}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md"
              >
                Add
              </button>
            </div>
          </div>
          
          {ingredients.length > 0 ? (
            <ul className="border border-gray-200 rounded-md divide-y">
              {ingredients.map((ingredient, index) => (
                <li key={index} className="flex justify-between items-center p-3">
                  <span>
                    {ingredient.quantity && `${ingredient.quantity} `}
                    {ingredient.unit && `${ingredient.unit} of `}
                    {ingredient.name}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemoveIngredient(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 italic">No ingredients added yet</p>
          )}
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Instructions
          </label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            placeholder="Enter cooking instructions"
            rows={5}
          />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Prep Time (minutes)
            </label>
            <input
              type="number"
              value={prepTime}
              onChange={(e) => setPrepTime(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
              placeholder="Prep time"
              min="0"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cook Time (minutes)
            </label>
            <input
              type="number"
              value={cookTime}
              onChange={(e) => setCookTime(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
              placeholder="Cook time"
              min="0"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Servings
            </label>
            <input
              type="number"
              value={servings}
              onChange={(e) => setServings(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
              placeholder="Number of servings"
              min="1"
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tags (comma separated)
          </label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
            placeholder="e.g. Italian, Pasta, Quick"
          />
        </div>
        
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/recipes')}
            className="px-4 py-2 border border-gray-300 rounded-md"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
          >
            {loading ? 'Creating...' : 'Create Recipe'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateRecipePage; 