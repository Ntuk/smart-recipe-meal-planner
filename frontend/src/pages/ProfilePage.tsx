import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';

const ProfilePage = () => {
  const { user, isAuthenticated, isLoading, updateProfile, logout } = useAuthContext();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [dietaryPreferences, setDietaryPreferences] = useState<string[]>([]);
  const [favoriteCuisines, setFavoriteCuisines] = useState<string[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [formError, setFormError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  
  // Dietary preferences options
  const dietaryOptions = [
    'Vegetarian',
    'Vegan',
    'Gluten-Free',
    'Dairy-Free',
    'Keto',
    'Low-Carb',
    'Paleo',
  ];
  
  // Cuisine options
  const cuisineOptions = [
    'Italian',
    'Mexican',
    'Chinese',
    'Japanese',
    'Indian',
    'Thai',
    'Mediterranean',
    'American',
    'French',
    'Greek',
  ];
  
  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, isLoading, navigate]);
  
  // Initialize form with user data
  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setEmail(user.email);
      setDietaryPreferences(user.preferences?.dietary_preferences || []);
      setFavoriteCuisines(user.preferences?.favorite_cuisines || []);
    }
  }, [user]);
  
  // Handle dietary preference toggle
  const handleDietaryToggle = (preference: string) => {
    setDietaryPreferences(prev => 
      prev.includes(preference) 
        ? prev.filter(p => p !== preference) 
        : [...prev, preference]
    );
  };
  
  // Handle cuisine toggle
  const handleCuisineToggle = (cuisine: string) => {
    setFavoriteCuisines(prev => 
      prev.includes(cuisine) 
        ? prev.filter(c => c !== cuisine) 
        : [...prev, cuisine]
    );
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSuccessMessage('');
    
    try {
      await updateProfile({
        username,
        preferences: {
          dietary_preferences: dietaryPreferences,
          favorite_cuisines: favoriteCuisines,
        },
      });
      
      setSuccessMessage('Profile updated successfully');
      setIsEditing(false);
    } catch (error) {
      setFormError('Failed to update profile');
      console.error(error);
    }
  };
  
  // Handle logout
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Your personal information and preferences
                </p>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Logout
              </button>
            </div>
            
            <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
              {successMessage && (
                <div className="mb-4 bg-green-50 border-l-4 border-green-400 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-green-400"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-green-700">{successMessage}</p>
                    </div>
                  </div>
                </div>
              )}
              
              {formError && (
                <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
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
                      <p className="text-sm text-red-700">{formError}</p>
                    </div>
                  </div>
                </div>
              )}
              
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                      Username
                    </label>
                    <div className="mt-1">
                      <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        disabled={!isEditing}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                      Email
                    </label>
                    <div className="mt-1">
                      <input
                        type="email"
                        id="email"
                        value={email}
                        disabled
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md bg-gray-50"
                      />
                    </div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h3 className="text-lg font-medium text-gray-900">Preferences</h3>
                  
                  <div className="mt-4">
                    <span className="block text-sm font-medium text-gray-700 mb-2">
                      Dietary Preferences
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {dietaryOptions.map((option) => (
                        <button
                          key={option}
                          type="button"
                          disabled={!isEditing}
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            dietaryPreferences.includes(option)
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                          } ${!isEditing && 'opacity-75 cursor-default'}`}
                          onClick={() => isEditing && handleDietaryToggle(option)}
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    <span className="block text-sm font-medium text-gray-700 mb-2">
                      Favorite Cuisines
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {cuisineOptions.map((cuisine) => (
                        <button
                          key={cuisine}
                          type="button"
                          disabled={!isEditing}
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            favoriteCuisines.includes(cuisine)
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                          } ${!isEditing && 'opacity-75 cursor-default'}`}
                          onClick={() => isEditing && handleCuisineToggle(cuisine)}
                        >
                          {cuisine}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="mt-8 flex justify-end">
                  {isEditing ? (
                    <>
                      <button
                        type="button"
                        onClick={() => setIsEditing(false)}
                        className="mr-3 inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Save
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setIsEditing(true)}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Edit Profile
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage; 