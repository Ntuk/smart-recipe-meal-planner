import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTranslation } from 'react-i18next';

interface Ingredient {
  name: string;
  quantity: string | null;
  unit: string | null;
}

const CreateRecipePage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { t } = useTranslation();
  
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
    if (location.state && location.state.ingredients) {
      setIngredients(location.state.ingredients);
    }
  }, [location.state]);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      setError(t('auth.loginRequired'));
    }
  }, [isAuthenticated, t]);
  
  const handleAddIngredient = () => {
    if (newIngredient.name.trim()) {
      setIngredients([
        ...ingredients,
        {
          name: newIngredient.name.trim(),
          quantity: newIngredient.quantity.trim() || null,
          unit: newIngredient.unit.trim() || null,
        },
      ]);
      setNewIngredient({ name: '', quantity: '', unit: '' });
    }
  };
  
  const handleRemoveIngredient = (index: number) => {
    const updatedIngredients = [...ingredients];
    updatedIngredients.splice(index, 1);
    setIngredients(updatedIngredients);
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isAuthenticated) {
      setError(t('auth.loginRequired'));
      return;
    }
    
    if (!title.trim()) {
      setError(t('recipes.titleRequired', 'Title is required'));
      return;
    }
    
    if (ingredients.length === 0) {
      setError(t('recipes.ingredientsRequired', 'At least one ingredient is required'));
      return;
    }
    
    if (!instructions.trim()) {
      setError(t('recipes.instructionsRequired', 'Instructions are required'));
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Mock API call for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Redirect to recipes page
      navigate('/recipes');
    } catch (err) {
      console.error('Error creating recipe:', err);
      setError(t('common.error'));
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h1 className="text-2xl font-bold text-gray-900">{t('recipes.createRecipe')}</h1>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                {t('recipes.createRecipeDescription', 'Fill in the details to create a new recipe')}
              </p>
            </div>
            
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              {error && (
                <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
                  {error}
                </div>
              )}
              
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                    {t('recipes.title')}
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id="title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    {t('recipes.description')}
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="description"
                      rows={3}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    {t('recipes.ingredients')}
                  </label>
                  
                  <div className="mt-2 space-y-2">
                    {ingredients.map((ingredient, index) => (
                      <div key={index} className="flex items-center">
                        <span className="flex-grow">{ingredient.name} {ingredient.quantity && `(${ingredient.quantity} ${ingredient.unit || ''})`}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveIngredient(index)}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          {t('common.delete')}
                        </button>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    <div>
                      <input
                        type="text"
                        placeholder={t('recipes.ingredientName', 'Ingredient name')}
                        value={newIngredient.name}
                        onChange={(e) => setNewIngredient({ ...newIngredient, name: e.target.value })}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        placeholder={t('recipes.quantity')}
                        value={newIngredient.quantity}
                        onChange={(e) => setNewIngredient({ ...newIngredient, quantity: e.target.value })}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        placeholder={t('recipes.unit')}
                        value={newIngredient.unit}
                        onChange={(e) => setNewIngredient({ ...newIngredient, unit: e.target.value })}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                  
                  <button
                    type="button"
                    onClick={handleAddIngredient}
                    className="mt-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {t('recipes.addIngredient')}
                  </button>
                </div>
                
                <div>
                  <label htmlFor="instructions" className="block text-sm font-medium text-gray-700">
                    {t('recipes.instructions')}
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="instructions"
                      rows={5}
                      value={instructions}
                      onChange={(e) => setInstructions(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder={t('recipes.instructionsPlaceholder', 'Enter step-by-step instructions')}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-3">
                  <div>
                    <label htmlFor="prep-time" className="block text-sm font-medium text-gray-700">
                      {t('recipes.prepTime')}
                    </label>
                    <div className="mt-1">
                      <input
                        type="number"
                        id="prep-time"
                        min="0"
                        value={prepTime}
                        onChange={(e) => setPrepTime(e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder={t('recipes.minutes', 'Minutes')}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="cook-time" className="block text-sm font-medium text-gray-700">
                      {t('recipes.cookTime')}
                    </label>
                    <div className="mt-1">
                      <input
                        type="number"
                        id="cook-time"
                        min="0"
                        value={cookTime}
                        onChange={(e) => setCookTime(e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder={t('recipes.minutes', 'Minutes')}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="servings" className="block text-sm font-medium text-gray-700">
                      {t('recipes.servings')}
                    </label>
                    <div className="mt-1">
                      <input
                        type="number"
                        id="servings"
                        min="1"
                        value={servings}
                        onChange={(e) => setServings(e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
                    {t('recipes.tags')}
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id="tags"
                      value={tags}
                      onChange={(e) => setTags(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder={t('recipes.tagsPlaceholder', 'Comma-separated tags (e.g. Italian, Pasta, Quick)')}
                    />
                  </div>
                </div>
                
                <div className="pt-5">
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => navigate('/recipes')}
                      className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {t('common.cancel')}
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {loading ? t('common.loading') : t('common.save')}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateRecipePage; 