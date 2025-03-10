import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">Smart Recipe & Meal Planner</h1>
        </div>
      </header>
      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 p-4 flex flex-col items-center justify-center">
              <h2 className="text-2xl font-semibold mb-4">Welcome to Smart Recipe & Meal Planner</h2>
              <p className="text-gray-600 mb-8 text-center max-w-md">
                Plan your meals based on available ingredients, dietary preferences, and more!
              </p>
              <div className="flex space-x-4">
                <button 
                  className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                  onClick={() => setCount((count) => count + 1)}
                >
                  Scan Ingredients
                </button>
                <button className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
                  Browse Recipes
                </button>
              </div>
              <p className="mt-4 text-sm text-gray-500">
                Button click count: {count}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
