import { useState } from 'react';
import { Link } from 'react-router-dom';

const HomePage = () => {
  const [count, setCount] = useState(0);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            Smart Recipe & Meal Planner
          </h1>
          <p className="mt-5 max-w-xl mx-auto text-xl text-gray-500">
            Welcome to Smart Recipe & Meal Planner
          </p>
          <p className="mt-3 max-w-md mx-auto text-lg text-gray-500">
            Plan your meals based on available ingredients, dietary preferences, and more!
          </p>
          <div className="mt-10 flex justify-center gap-4">
            <Link 
              to="/scan" 
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={() => setCount(count + 1)}
            >
              Scan Ingredients
            </Link>
            <Link 
              to="/recipes" 
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              Browse Recipes
            </Link>
          </div>
          <div className="mt-4 text-sm text-gray-500">
            Button click count: {count}
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900">How it works</h2>
          <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">1. Scan Ingredients</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Upload a photo of your ingredients or enter them manually.
                </p>
              </div>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">2. Get Meal Suggestions</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Our system will suggest recipes based on your available ingredients.
                </p>
              </div>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">3. Generate Shopping List</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Get a shopping list for any missing ingredients you need.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage; 