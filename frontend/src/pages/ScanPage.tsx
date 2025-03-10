import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ingredientScannerApi } from '../services/api';

const ScanPage = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manualInput, setManualInput] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleScan = async () => {
    if (!file) {
      setError('Please select an image to scan');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Call the actual API using the service
      const response = await ingredientScannerApi.scanIngredients(file);
      setIngredients(response.ingredients);
    } catch (err) {
      setError('Failed to scan ingredients. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualInput.trim()) {
      setError('Please enter some ingredients');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Call the actual API using the service
      const response = await ingredientScannerApi.manualInput(manualInput);
      setIngredients(response.ingredients);
    } catch (err) {
      setError('Failed to process ingredients. Please try again.');
      console.error(err);
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
              <h1 className="text-2xl font-bold text-gray-900">Scan Ingredients</h1>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Upload a photo of your ingredients or enter them manually
              </p>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Upload Image</h3>
                  <div className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                    <div className="space-y-1 text-center">
                      {preview ? (
                        <img src={preview} alt="Preview" className="mx-auto h-64 w-auto" />
                      ) : (
                        <svg
                          className="mx-auto h-12 w-12 text-gray-400"
                          stroke="currentColor"
                          fill="none"
                          viewBox="0 0 48 48"
                          aria-hidden="true"
                        >
                          <path
                            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      )}
                      <div className="flex text-sm text-gray-600">
                        <label
                          htmlFor="file-upload"
                          className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                        >
                          <span>Upload a file</span>
                          <input
                            id="file-upload"
                            name="file-upload"
                            type="file"
                            className="sr-only"
                            accept="image/*"
                            onChange={handleFileChange}
                          />
                        </label>
                        <p className="pl-1">or drag and drop</p>
                      </div>
                      <p className="text-xs text-gray-500">PNG, JPG, GIF up to 10MB</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    onClick={handleScan}
                    disabled={!file || isLoading}
                  >
                    {isLoading ? 'Scanning...' : 'Scan Ingredients'}
                  </button>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900">Manual Input</h3>
                  <form onSubmit={handleManualSubmit} className="mt-2">
                    <div>
                      <label htmlFor="ingredients" className="block text-sm font-medium text-gray-700">
                        Enter ingredients separated by commas
                      </label>
                      <div className="mt-1">
                        <textarea
                          id="ingredients"
                          name="ingredients"
                          rows={4}
                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                          placeholder="e.g., tomatoes, onions, garlic, olive oil"
                          value={manualInput}
                          onChange={(e) => setManualInput(e.target.value)}
                        />
                      </div>
                    </div>
                    <button
                      type="submit"
                      className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Processing...' : 'Submit Ingredients'}
                    </button>
                  </form>
                </div>
              </div>

              {error && (
                <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-red-400"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {ingredients.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-medium text-gray-900">Detected Ingredients</h3>
                  <div className="mt-2 bg-gray-50 p-4 rounded-md">
                    <ul className="list-disc pl-5 space-y-1">
                      {ingredients.map((ingredient, index) => (
                        <li key={index} className="text-sm text-gray-700">
                          {ingredient}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mt-4 flex space-x-3">
                    <Link
                      to="/meal-plan"
                      state={{ ingredients }}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      Generate Meal Plan
                    </Link>
                    <button
                      type="button"
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      onClick={() => {
                        setIngredients([]);
                        setFile(null);
                        setPreview(null);
                        setManualInput('');
                      }}
                    >
                      Clear
                    </button>
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

export default ScanPage; 