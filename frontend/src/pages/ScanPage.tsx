import React, { useState, useRef } from 'react';
import { ingredientScannerApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useShoppingList } from '../hooks/useShoppingList';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const ScanPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [manualText, setManualText] = useState('');
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanMode, setScanMode] = useState<'image' | 'text'>('image');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isAuthenticated } = useAuth();
  const { createShoppingList } = useShoppingList();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (event) => {
        setPreview(event.target?.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleScan = async () => {
    if (!isAuthenticated) {
      setError(t('auth.loginRequired'));
      return;
    }
    
    if (!file) {
      setError(t('scan.selectImage'));
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await ingredientScannerApiService.scanIngredients(file);
      setIngredients(response.ingredients.map(item => item.name));
    } catch (err) {
      console.error('Error scanning ingredients:', err);
      setError(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleManualInput = async () => {
    if (!manualText.trim()) {
      setError(t('scan.enterIngredients'));
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Split by newlines first, then by commas, and flatten the array
      const ingredients = manualText
        .split('\n')
        .flatMap(line => 
          line.split(',')
            .map(item => item.trim())
            .filter(item => item.length > 0)
        );
      
      console.log('Processed ingredients:', ingredients);
      setIngredients(ingredients);
      setLoading(false);
    } catch (err) {
      console.error('Error processing text:', err);
      setError(t('common.error'));
      setLoading(false);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleCreateRecipe = () => {
    if (!isAuthenticated) {
      setError(t('auth.loginRequired'));
      return;
    }
    
    if (ingredients.length === 0) {
      setError(t('scan.noIngredientsDetected'));
      return;
    }
    
    // Navigate to recipes page with ingredients as state
    navigate('/recipes/new', { 
      state: { 
        ingredients: ingredients.map(name => ({ name, quantity: null, unit: null }))
      } 
    });
  };

  const handleAddToShoppingList = async () => {
    if (!ingredients || ingredients.length === 0) {
      setError(t('scan.noIngredientsDetected'));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Navigate to the shopping list page with the ingredients
      navigate('/shopping-lists', { 
        state: { 
          ingredients: ingredients 
        } 
      });
    } catch (error) {
      console.error('Error adding to shopping list:', error);
      setError(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">{t('scan.title')}</h1>
      
      <div className="mb-6">
        <div className="flex space-x-4 mb-4">
          <button
            className={`px-4 py-2 rounded-md ${scanMode === 'image' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setScanMode('image')}
          >
            {t('scan.scanImage')}
          </button>
          <button
            className={`px-4 py-2 rounded-md ${scanMode === 'text' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setScanMode('text')}
          >
            {t('scan.manualInput')}
          </button>
        </div>
        
        {scanMode === 'image' ? (
          <div className="space-y-4">
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
              ref={fileInputRef}
            />
            
            <div 
              onClick={triggerFileInput}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-indigo-500 transition-colors"
            >
              {preview ? (
                <img src={preview} alt="Preview" className="max-h-64 mx-auto" />
              ) : (
                <div>
                  <p className="text-gray-500">{t('scan.selectImage')}</p>
                  <p className="text-sm text-gray-400 mt-2">{t('scan.supportedFormats')}</p>
                </div>
              )}
            </div>
            
            <button
              onClick={handleScan}
              disabled={!file || loading}
              className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? t('common.loading') : t('scan.scanIngredients')}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <textarea
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder={t('scan.enterIngredients')}
              className="w-full h-64 p-4 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
            
            <button
              onClick={handleManualInput}
              disabled={!manualText.trim() || loading}
              className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? t('common.loading') : t('scan.processText')}
            </button>
          </div>
        )}
        
        {error && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
            {error}
          </div>
        )}
      </div>
      
      {ingredients.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">{t('scan.detectedIngredients')}</h2>
          <ul className="space-y-2">
            {ingredients.map((ingredient, index) => (
              <li key={index} className="flex items-center">
                <span className="w-6 h-6 flex items-center justify-center bg-indigo-100 text-indigo-800 rounded-full mr-3">
                  {index + 1}
                </span>
                {ingredient}
              </li>
            ))}
          </ul>
          
          <div className="mt-6 flex space-x-4">
            <button 
              className="py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              onClick={handleCreateRecipe}
              disabled={loading}
            >
              {t('recipes.createRecipe')}
            </button>
            <button 
              className="py-2 px-4 bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200"
              onClick={handleAddToShoppingList}
              disabled={loading}
            >
              {t('scan.addToShoppingList')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanPage; 