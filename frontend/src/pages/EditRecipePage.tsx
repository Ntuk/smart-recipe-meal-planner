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
  
  useEffect(() => {
    if (!id) {
      setError('Recipe ID is missing');
      setInitialLoading(false);
      return;
    }
    
    const loadRecipe = async () => {
      try {
        let foundRecipe = null;
        
        // Fetch recipe from API
        try {
          foundRecipe = await recipeApiService.getRecipe(id);
          console.log('Recipe loaded from API:', foundRecipe);
        } catch (err) {
          console.error('Error fetching recipe from API:', err);
          setError('Failed to load recipe. The recipe might not exist or there was a network error.');
          setInitialLoading(false);
          return;
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
          // Check if steps are objects or strings
          if (foundRecipe.steps.length > 0 && typeof foundRecipe.steps[0] === 'object') {
            // Handle steps that are objects with a description field
            setInstructions(foundRecipe.steps.map(step => 
              step.description || JSON.stringify(step)
            ).join('\n'));
          } else {
            // Handle steps that are already strings
            setInstructions(foundRecipe.steps.join('\n'));
          }
        } else if (Array.isArray(foundRecipe.instructions)) {
          // Similar check for instructions
          if (foundRecipe.instructions.length > 0 && typeof foundRecipe.instructions[0] === 'object') {
            setInstructions(foundRecipe.instructions.map(instruction => 
              instruction.description || JSON.stringify(instruction)
            ).join('\n'));
          } else {
            setInstructions(foundRecipe.instructions.join('\n'));
          }
        }
        
        // Set other fields
        setPrepTime(String(foundRecipe.prep_time || foundRecipe.prep_time_minutes || ''));
        setCookTime(String(foundRecipe.cook_time || foundRecipe.cook_time_minutes || ''));
        setServings(String(foundRecipe.servings || ''));
        
        // Handle tags
        let tagsList: string[] = [];
        
        // Add existing tags if available
        if (Array.isArray(foundRecipe.tags)) {
          // Make sure tags is not empty and contains actual string values
          const validTags = foundRecipe.tags.filter(tag => tag && typeof tag === 'string');
          if (validTags.length > 0) {
            tagsList = [...validTags];
          }
        }
        
        // Add cuisine as a tag if available and not already in tags
        if (foundRecipe.cuisine && typeof foundRecipe.cuisine === 'string' && foundRecipe.cuisine !== 'Other') {
          if (!tagsList.includes(foundRecipe.cuisine)) {
            tagsList.push(foundRecipe.cuisine);
          }
        }
        
        // Add category as a tag if available and not already in tags
        if (foundRecipe.category && typeof foundRecipe.category === 'string') {
          if (!tagsList.includes(foundRecipe.category)) {
            tagsList.push(foundRecipe.category);
          }
        }
        
        // Set tags if we have any
        if (tagsList.length > 0) {
          setTags(tagsList.join(', '));
          console.log('Setting tags:', tagsList.join(', '));
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
      setIngredients([...ingredients, newIngredient]);
      setNewIngredient({ name: '', quantity: '', unit: '' });
    }
  };
  
  const handleRemoveIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!title.trim()) {
      setError(t('recipes.errorTitleRequired', 'Recipe title is required'));
      return;
    }

    // Make sure we have at least a minimal value for prep_time and cook_time
    const validPrepTime = parseInt(prepTime) || 0;
    const validCookTime = parseInt(cookTime) || 0;
    const validServings = parseInt(servings) || 1;
    
    setPrepTime(String(validPrepTime));
    setCookTime(String(validCookTime));
    setServings(String(validServings));
    
    setError(null);
    setLoading(true);
    
    try {
      if (!id) {
        throw new Error('Recipe ID is missing');
      }
      
      // Process tags - convert comma-separated string to array, trim whitespace, filter empty strings
      const tagArray = tags.split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);
        
      console.log('Processed tags for submission:', tagArray);
      
      // Format the recipe data for the API
      const recipeData = {
        name: title,
        description: description,
        ingredients: ingredients.map(ing => ({
          name: ing.name,
          quantity: ing.quantity || '',
          unit: ing.unit || ''
        })),
        steps: instructions.split('\n')
          .filter(step => step.trim())
          .map((step, index) => ({
            number: index + 1,
            description: step.trim()
          })),
        prep_time: validPrepTime,
        cook_time: validCookTime,
        servings: validServings,
        tags: tagArray,
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
              
              <form onSubmit={handleSubmit}>
                <div className="mb-6">
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                    {t('recipes.recipeTitle', 'Recipe Title')}
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id="title"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder={t('recipes.enterRecipeName', 'Enter recipe name')}
                    />
                  </div>
                </div>
                
                <div className="mb-6">
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    {t('recipes.description', 'Description')}
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={3}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder={t('recipes.brieflyDescribeYourRecipe', 'Briefly describe your recipe')}
                    />
                  </div>
                </div>
                
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('recipes.ingredients', 'Ingredients')}
                  </label>
                  
                  <div className="grid grid-cols-3 gap-4 mb-2">
                    <div className="col-span-1">
                      <label className="sr-only">{t('recipes.ingredientName', 'Ingredient name')}</label>
                      <input
                        type="text"
                        value={newIngredient.name}
                        onChange={(e) => setNewIngredient({...newIngredient, name: e.target.value})}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder={t('recipes.ingredientName', 'Ingredient name')}
                      />
                    </div>
                    <div>
                      <label className="sr-only">{t('recipes.quantity', 'Quantity')}</label>
                      <input
                        type="text"
                        value={newIngredient.quantity || ''}
                        onChange={(e) => setNewIngredient({...newIngredient, quantity: e.target.value})}
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder={t('recipes.quantity', 'Quantity')}
                      />
                    </div>
                    <div className="flex">
                      <div className="flex-grow">
                        <label className="sr-only">{t('recipes.unit', 'Unit')}</label>
                        <input
                          type="text"
                          value={newIngredient.unit || ''}
                          onChange={(e) => setNewIngredient({...newIngredient, unit: e.target.value})}
                          className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          placeholder={t('recipes.unit', 'Unit')}
                        />
                      </div>
                      <button
                        type="button"
                        onClick={handleAddIngredient}
                        className="ml-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        {t('common.add', 'Add')}
                      </button>
                    </div>
                  </div>
                  
                  <div className="mt-2 space-y-2 max-h-64 overflow-y-auto">
                    {ingredients.map((ingredient, index) => (
                      <div key={index} className="flex items-center bg-gray-50 p-2 rounded">
                        <span className="flex-grow">
                          {ingredient.quantity && `${ingredient.quantity} `}
                          {ingredient.unit && `${ingredient.unit} `}
                          {ingredient.name}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveIngredient(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          {t('common.remove', 'Remove')}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="mb-6">
                  <label htmlFor="instructions" className="block text-sm font-medium text-gray-700">
                    {t('recipes.instructions', 'Instructions')}
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="instructions"
                      value={instructions}
                      onChange={(e) => setInstructions(e.target.value)}
                      rows={6}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder={t('recipes.enterStepByStepInstructions', 'Enter step-by-step instructions')}
                    />
                    <p className="mt-1 text-sm text-gray-500">
                      {t('recipes.instructionsHint', 'Enter each step on a new line')}
                    </p>
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
                
                <div className="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
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
                        className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        placeholder={t('recipes.commaSeperatedTags', 'Comma-separated tags (e.g. Italian, Pasta, Quick)')}
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
                        <option value="Easy">{t('recipes.difficultyEasy', 'Easy')}</option>
                        <option value="Medium">{t('recipes.difficultyMedium', 'Medium')}</option>
                        <option value="Hard">{t('recipes.difficultyHard', 'Hard')}</option>
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