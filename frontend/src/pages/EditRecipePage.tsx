import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeApiService } from '../services/api';
import { toast } from 'react-hot-toast';

interface Ingredient {
  name: string;
  quantity: string | null;
  unit: string | null;
}

const EditRecipePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
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
  const [initialLoading, setInitialLoading] = useState(true);
  const [difficulty, setDifficulty] = useState('Easy');
  
  // Fetch recipe data when component mounts
  useEffect(() => {
    if (!id) {
      setError('Recipe ID is required');
      setInitialLoading(false);
      return;
    }
    
    const loadRecipe = async () => {
      setInitialLoading(true);
      
      try {
        // First check localStorage for the recipe
        let foundRecipe: any = null;
        
        // Check in user_created_recipes
        const userRecipesJson = localStorage.getItem('user_created_recipes');
        if (userRecipesJson) {
          const userRecipes = JSON.parse(userRecipesJson);
          const userRecipe = userRecipes.find((r: any) => r.id === id);
          
          if (userRecipe) {
            console.log('Found recipe in localStorage:', userRecipe);
            foundRecipe = userRecipe;
          }
        }
        
        // If not found in localStorage, check mock recipes
        if (!foundRecipe) {
          // Try to get from API (would work in real implementation)
          try {
            // This would be the real implementation
            // foundRecipe = await recipeApiService.getRecipe(id);
            
            // For demo, simulate fetching from a mock API
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Check if it's one of the mock recipes by ID
            // This is just hardcoded for the demo - in real app would need proper mock data handling
            if (id === '1') {
              foundRecipe = {
                id: '1',
                name: 'Spaghetti Carbonara',
                description: 'A classic Italian pasta dish with eggs, cheese, pancetta, and black pepper.',
                ingredients: [
                  { name: 'Spaghetti', quantity: '400', unit: 'g' },
                  { name: 'Eggs', quantity: '4', unit: '' },
                  { name: 'Pancetta', quantity: '150', unit: 'g' },
                  { name: 'Parmesan cheese', quantity: '50', unit: 'g' },
                  { name: 'Black pepper', quantity: '2', unit: 'tsp' },
                  { name: 'Salt', quantity: '1', unit: 'tsp' }
                ],
                steps: [
                  'Cook spaghetti according to package instructions.',
                  'In a bowl, whisk eggs and grated cheese.',
                  'Cook pancetta until crispy.',
                  'Combine pasta, egg mixture, and pancetta. Toss quickly.',
                  'Season with black pepper and serve immediately.'
                ],
                prep_time: 10,
                cook_time: 15,
                servings: 4,
                tags: ['Italian', 'Pasta', 'Quick'],
                cuisine: 'Italian',
                difficulty: 'Easy',
              };
            } else if (id === '5') {
              foundRecipe = {
                id: '5',
                name: 'Energizing fruit smoothie',
                description: '',
                ingredients: [
                  { name: 'Frozen berries', quantity: '1', unit: 'cup' },
                  { name: 'Banana', quantity: '1', unit: '' },
                  { name: 'Yogurt', quantity: '1/2', unit: 'cup' },
                  { name: 'Honey', quantity: '1', unit: 'tbsp' },
                  { name: 'Orange juice', quantity: '1/2', unit: 'cup' }
                ],
                steps: [
                  'Add all ingredients to a blender.',
                  'Blend until smooth.',
                  'Pour into a glass and enjoy immediately.'
                ],
                prep_time: 5,
                cook_time: 0,
                servings: 1,
                tags: ['Breakfast', 'Smoothie', 'Quick', 'No-cook'],
                cuisine: 'International',
                difficulty: 'Easy',
              };
            }
          } catch (err) {
            console.error('Error fetching recipe from API:', err);
          }
        }
        
        if (!foundRecipe) {
          setError('Recipe not found');
          setInitialLoading(false);
          return;
        }
        
        // Set form values from recipe data
        setTitle(foundRecipe.name || foundRecipe.title || '');
        setDescription(foundRecipe.description || '');
        
        // Handle ingredients which might be an array of strings or objects
        if (Array.isArray(foundRecipe.ingredients)) {
          if (typeof foundRecipe.ingredients[0] === 'string') {
            // Convert string ingredients to object format
            setIngredients(foundRecipe.ingredients.map(ing => ({
              name: ing,
              quantity: null,
              unit: null
            })));
          } else {
            // Handle object format ingredients
            setIngredients(foundRecipe.ingredients.map(ing => ({
              name: ing.name || ing,
              quantity: ing.quantity || null,
              unit: ing.unit || null
            })));
          }
        }
        
        // Handle instructions/steps
        if (Array.isArray(foundRecipe.steps)) {
          setInstructions(foundRecipe.steps.join('\n'));
        } else if (Array.isArray(foundRecipe.instructions)) {
          setInstructions(foundRecipe.instructions.join('\n'));
        }
        
        // Set other fields
        setPrepTime(String(foundRecipe.prep_time || foundRecipe.prep_time_minutes || ''));
        setCookTime(String(foundRecipe.cook_time || foundRecipe.cook_time_minutes || ''));
        setServings(String(foundRecipe.servings || ''));
        
        // Handle tags
        if (Array.isArray(foundRecipe.tags)) {
          setTags(foundRecipe.tags.join(', '));
        }
        
        // Handle difficulty
        setDifficulty(foundRecipe.difficulty || 'Easy');
        
      } catch (err) {
        console.error('Error loading recipe for editing:', err);
        setError('Failed to load recipe data.');
      } finally {
        setInitialLoading(false);
      }
    };
    
    loadRecipe();
  }, [id]);
  
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
      if (!id) {
        throw new Error('Recipe ID is missing');
      }
      
      // Format the recipe data for the API
      const recipeData = {
        name: title,
        description: description,
        ingredients: ingredients.map(ing => ({
          name: ing.name,
          quantity: ing.quantity || '',
          unit: ing.unit || ''
        })),
        steps: instructions.split('\n').filter(step => step.trim()),
        prep_time: parseInt(prepTime) || 0,
        cook_time: parseInt(cookTime) || 0,
        servings: parseInt(servings) || 1,
        tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag),
        difficulty: difficulty,
      };
      
      console.log('Updating recipe with data:', recipeData);
      
      // Call the API to update the recipe
      const updatedRecipe = await recipeApiService.updateRecipe(id, recipeData);
      console.log('Recipe updated successfully:', updatedRecipe);
      
      // Show success message
      toast.success('Recipe updated successfully!');
      
      // Navigate back to recipe detail
      navigate(`/recipes/${id}`);
    } catch (err) {
      console.error('Error updating recipe:', err);
      setError(t('common.error', 'An error occurred'));
      toast.error('Failed to update recipe. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  if (initialLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-700">Loading recipe...</span>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h1 className="text-2xl font-bold text-gray-900">{t('recipes.editRecipe', 'Edit Recipe')}</h1>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                {t('recipes.editRecipeDescription', 'Update the details of your recipe')}
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
                    {t('recipes.title', 'Recipe Title')}
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id="title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Enter recipe name"
                    />
                  </div>
                </div>
                
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    {t('recipes.description', 'Description')}
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="description"
                      rows={3}
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Briefly describe your recipe"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    {t('recipes.ingredients', 'Ingredients')}
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
                          {t('common.delete', 'Delete')}
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
                        placeholder={t('recipes.quantity', 'Quantity')}
                        value={newIngredient.quantity}
                        onChange={(e) => setNewIngredient({ ...newIngredient, quantity: e.target.value })}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        placeholder={t('recipes.unit', 'Unit')}
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
                    {t('recipes.addIngredient', 'Add Ingredient')}
                  </button>
                </div>
                
                <div>
                  <label htmlFor="instructions" className="block text-sm font-medium text-gray-700">
                    {t('recipes.instructions', 'Instructions')}
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="instructions"
                      rows={6}
                      value={instructions}
                      onChange={(e) => setInstructions(e.target.value)}
                      placeholder={t('recipes.instructionsPlaceholder', 'Enter each step on a new line')}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-3">
                  <div>
                    <label htmlFor="prepTime" className="block text-sm font-medium text-gray-700">
                      {t('recipes.prepTime', 'Prep Time (minutes)')}
                    </label>
                    <div className="mt-1">
                      <input
                        type="number"
                        id="prepTime"
                        min="0"
                        value={prepTime}
                        onChange={(e) => setPrepTime(e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="cookTime" className="block text-sm font-medium text-gray-700">
                      {t('recipes.cookTime', 'Cook Time (minutes)')}
                    </label>
                    <div className="mt-1">
                      <input
                        type="number"
                        id="cookTime"
                        min="0"
                        value={cookTime}
                        onChange={(e) => setCookTime(e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="servings" className="block text-sm font-medium text-gray-700">
                      {t('recipes.servings', 'Servings')}
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
                
                <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
                      {t('recipes.tags', 'Tags')}
                    </label>
                    <div className="mt-1">
                      <input
                        type="text"
                        id="tags"
                        value={tags}
                        onChange={(e) => setTags(e.target.value)}
                        placeholder={t('recipes.tagsPlaceholder', 'e.g., Italian, Pasta, Quick (comma separated)')}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700">
                      {t('recipes.difficulty', 'Difficulty')}
                    </label>
                    <div className="mt-1">
                      <select
                        id="difficulty"
                        value={difficulty}
                        onChange={(e) => setDifficulty(e.target.value)}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      >
                        <option value="Easy">Easy</option>
                        <option value="Medium">Medium</option>
                        <option value="Hard">Hard</option>
                      </select>
                    </div>
                  </div>
                </div>
                
                <div className="pt-5">
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => navigate(`/recipes/${id}`)}
                      className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {t('common.cancel', 'Cancel')}
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      {loading ? t('common.loading', 'Loading...') : t('common.save', 'Save')}
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

export default EditRecipePage; 