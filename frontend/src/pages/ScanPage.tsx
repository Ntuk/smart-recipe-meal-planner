import React, { useState, useRef } from 'react';
import { ingredientScannerApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';

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
      setError('You must be logged in to scan ingredients');
      return;
    }
    
    if (!file) {
      setError('Please select an image to scan');
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
      setError('Failed to scan ingredients. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualInput = async () => {
    if (!isAuthenticated) {
      setError('You must be logged in to process ingredients');
      return;
    }
    
    if (!manualText.trim()) {
      setError('Please enter some text');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await ingredientScannerApiService.manualInput(manualText);
      setIngredients(response.ingredients.map(item => item.name));
    } catch (err) {
      console.error('Error processing text:', err);
      setError('Failed to process text. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Ingredient Scanner</h1>
      
      <div className="mb-6">
        <div className="flex space-x-4 mb-4">
          <button
            className={`px-4 py-2 rounded-md ${scanMode === 'image' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setScanMode('image')}
          >
            Scan Image
          </button>
          <button
            className={`px-4 py-2 rounded-md ${scanMode === 'text' ? 'bg-indigo-600 text-white' : 'bg-gray-200'}`}
            onClick={() => setScanMode('text')}
          >
            Manual Input
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
                  <p className="text-gray-500">Click to select an image</p>
                  <p className="text-sm text-gray-400 mt-2">Supported formats: JPG, PNG</p>
                </div>
              )}
            </div>
            
            <button
              onClick={handleScan}
              disabled={!file || loading}
              className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Scanning...' : 'Scan Ingredients'}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <textarea
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder="Enter your ingredients list here, one per line..."
              className="w-full h-64 p-4 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
            
            <button
              onClick={handleManualInput}
              disabled={!manualText.trim() || loading}
              className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Process Text'}
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
          <h2 className="text-xl font-semibold mb-4">Detected Ingredients</h2>
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
            <button className="py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
              Create Recipe
            </button>
            <button className="py-2 px-4 bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200">
              Add to Shopping List
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanPage; 