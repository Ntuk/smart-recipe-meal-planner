import { useState } from 'react';
import { Link } from 'react-router-dom';

// Mock recipe data
const MOCK_RECIPES = [
  {
    id: '1',
    title: 'Spaghetti Carbonara',
    description: 'A classic Italian pasta dish with eggs, cheese, pancetta, and black pepper.',
    ingredients: ['Spaghetti', 'Eggs', 'Pancetta', 'Parmesan cheese', 'Black pepper', 'Salt'],
    prep_time_minutes: 10,
    cook_time_minutes: 15,
    servings: 4,
    tags: ['Italian', 'Pasta', 'Quick'],
    cuisine: 'Italian',
    difficulty: 'Easy',
  },
  {
    id: '2',
    title: 'Chicken Stir Fry',
    description: 'A quick and healthy stir fry with chicken and vegetables.',
    ingredients: ['Chicken breast', 'Bell peppers', 'Broccoli', 'Carrots', 'Soy sauce', 'Garlic', 'Ginger'],
    prep_time_minutes: 15,
    cook_time_minutes: 10,
    servings: 4,
    tags: ['Asian', 'Chicken', 'Quick', 'Healthy'],
    cuisine: 'Asian',
    difficulty: 'Easy',
  },
  {
    id: '3',
    title: 'Vegetable Curry',
    description: 'A flavorful vegetarian curry with mixed vegetables and spices.',
    ingredients: ['Potatoes', 'Carrots', 'Peas', 'Cauliflower', 'Curry powder', 'Coconut milk', 'Onion', 'Garlic'],
    prep_time_minutes: 20,
    cook_time_minutes: 30,
    servings: 6,
    tags: ['Indian', 'Vegetarian', 'Spicy'],
    cuisine: 'Indian',
    difficulty: 'Medium',
  },
  {
    id: '4',
    title: 'Greek Salad',
    description: 'A refreshing salad with tomatoes, cucumbers, olives, and feta cheese.',
    ingredients: ['Tomatoes', 'Cucumber', 'Red onion', 'Feta cheese', 'Kalamata olives', 'Olive oil', 'Lemon juice'],
    prep_time_minutes: 15,
    cook_time_minutes: 0,
    servings: 4,
    tags: ['Greek', 'Salad', 'Vegetarian', 'No-cook'],
    cuisine: 'Greek',
    difficulty: 'Easy',
  },
];

const RecipesPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCuisine, setSelectedCuisine] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Get unique cuisines, difficulties, and tags from recipes
  const cuisines = [...new Set(MOCK_RECIPES.map(recipe => recipe.cuisine))];
  const difficulties = [...new Set(MOCK_RECIPES.map(recipe => recipe.difficulty))];
  const allTags = [...new Set(MOCK_RECIPES.flatMap(recipe => recipe.tags))];

  // Filter recipes based on search term and filters
  const filteredRecipes = MOCK_RECIPES.filter(recipe => {
    const matchesSearch = searchTerm === '' || 
      recipe.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      recipe.ingredients.some(ingredient => ingredient.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesCuisine = selectedCuisine === '' || recipe.cuisine === selectedCuisine;
    const matchesDifficulty = selectedDifficulty === '' || recipe.difficulty === selectedDifficulty;
    const matchesTags = selectedTags.length === 0 || 
      selectedTags.every(tag => recipe.tags.includes(tag));
    
    return matchesSearch && matchesCuisine && matchesDifficulty && matchesTags;
  });

  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag) 
        : [...prev, tag]
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h1 className="text-2xl font-bold text-gray-900">Browse Recipes</h1>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Find recipes based on ingredients, cuisine, or dietary preferences
              </p>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-4">
                <div className="sm:col-span-4">
                  <label htmlFor="search" className="block text-sm font-medium text-gray-700">
                    Search recipes or ingredients
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="search"
                      id="search"
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="e.g., pasta, chicken, tomatoes"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="cuisine" className="block text-sm font-medium text-gray-700">
                    Cuisine
                  </label>
                  <select
                    id="cuisine"
                    name="cuisine"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    value={selectedCuisine}
                    onChange={(e) => setSelectedCuisine(e.target.value)}
                  >
                    <option value="">All Cuisines</option>
                    {cuisines.map((cuisine) => (
                      <option key={cuisine} value={cuisine}>
                        {cuisine}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700">
                    Difficulty
                  </label>
                  <select
                    id="difficulty"
                    name="difficulty"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                  >
                    <option value="">All Difficulties</option>
                    {difficulties.map((difficulty) => (
                      <option key={difficulty} value={difficulty}>
                        {difficulty}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <span className="block text-sm font-medium text-gray-700 mb-1">Tags</span>
                  <div className="flex flex-wrap gap-2">
                    {allTags.map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                          selectedTags.includes(tag)
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                        }`}
                        onClick={() => handleTagToggle(tag)}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-8 grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                {filteredRecipes.length > 0 ? (
                  filteredRecipes.map((recipe) => (
                    <div key={recipe.id} className="bg-white overflow-hidden shadow rounded-lg border border-gray-200">
                      <div className="p-5">
                        <h3 className="text-lg font-medium text-gray-900">{recipe.title}</h3>
                        <p className="mt-1 text-sm text-gray-500">{recipe.description}</p>
                        <div className="mt-2">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2">
                            {recipe.cuisine}
                          </span>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            {recipe.difficulty}
                          </span>
                        </div>
                        <div className="mt-3">
                          <p className="text-sm text-gray-500">
                            <span className="font-medium">Prep:</span> {recipe.prep_time_minutes} min | 
                            <span className="font-medium"> Cook:</span> {recipe.cook_time_minutes} min | 
                            <span className="font-medium"> Servings:</span> {recipe.servings}
                          </p>
                        </div>
                        <div className="mt-4">
                          <h4 className="text-sm font-medium text-gray-900">Ingredients:</h4>
                          <ul className="mt-2 text-sm text-gray-500 list-disc list-inside">
                            {recipe.ingredients.slice(0, 4).map((ingredient, index) => (
                              <li key={index}>{ingredient}</li>
                            ))}
                            {recipe.ingredients.length > 4 && (
                              <li>+{recipe.ingredients.length - 4} more</li>
                            )}
                          </ul>
                        </div>
                        <div className="mt-5">
                          <Link
                            to={`/recipes/${recipe.id}`}
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            View Recipe
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="sm:col-span-3 text-center py-12">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No recipes found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Try adjusting your search or filters to find what you're looking for.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecipesPage; 