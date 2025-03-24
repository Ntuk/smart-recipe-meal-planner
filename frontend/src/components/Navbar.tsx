import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { useTranslation } from 'react-i18next';
import cookzenLogo from '../assets/cookzen_logo.png';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuthContext();
  const { t } = useTranslation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <img 
                src={cookzenLogo} 
                alt={t('common.appName')} 
                className="h-10 w-auto"
              />
            </Link>
          </div>

          {/* Desktop navigation - only visible on large screens */}
          <div className="hidden lg:flex lg:items-center lg:space-x-8">
            <Link
              to="/"
              className={`${
                isActive('/') 
                  ? 'border-blue-500 text-gray-900' 
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              } px-3 py-2 text-sm font-medium border-b-2`}
            >
              {t('navigation.home')}
            </Link>
            
            {/* Only show these links if authenticated */}
            {isAuthenticated && (
              <>
                <Link
                  to="/recipes"
                  className={`${
                    isActive('/recipes') 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  } px-3 py-2 text-sm font-medium border-b-2`}
                >
                  {t('navigation.recipes')}
                </Link>
                <Link
                  to="/scan"
                  className={`${
                    isActive('/scan') 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  } px-3 py-2 text-sm font-medium border-b-2`}
                >
                  {t('navigation.scanIngredients')}
                </Link>
                <Link
                  to="/meal-plan"
                  className={`${
                    isActive('/meal-plan') 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  } px-3 py-2 text-sm font-medium border-b-2`}
                >
                  {t('navigation.mealPlans')}
                </Link>
                <Link
                  to="/shopping-list"
                  className={`${
                    isActive('/shopping-list') 
                      ? 'border-blue-500 text-gray-900' 
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  } px-3 py-2 text-sm font-medium border-b-2`}
                >
                  {t('navigation.shoppingLists')}
                </Link>
              </>
            )}

            {/* Desktop auth buttons */}
            {!isAuthenticated ? (
              <div className="flex items-center space-x-4 ml-8">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  {t('common.login')}
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  {t('common.register')}
                </Link>
              </div>
            ) : (
              <div className="relative ml-8">
                <button
                  type="button"
                  className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                  onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
                >
                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-800 font-semibold">
                    {user?.username.charAt(0).toUpperCase()}
                  </div>
                  <span>{user?.username}</span>
                </button>

                {isProfileMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5">
                    <Link
                      to="/profile"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setIsProfileMenuOpen(false)}
                    >
                      {t('common.profile')}
                    </Link>
                    <button
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => {
                        logout();
                        setIsProfileMenuOpen(false);
                      }}
                    >
                      {t('common.logout')}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Hamburger menu button - visible on medium and small screens */}
          <div className="flex items-center lg:hidden">
            {isAuthenticated && (
              <div className="mr-4">
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-800 font-semibold">
                  {user?.username.charAt(0).toUpperCase()}
                </div>
              </div>
            )}
            <button
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className={`${isMenuOpen ? 'hidden' : 'block'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <svg
                className={`${isMenuOpen ? 'block' : 'hidden'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className={`${isMenuOpen ? 'block' : 'hidden'} lg:hidden`}>
        <div className="pt-2 pb-3 space-y-1 border-b border-gray-200">
          <Link
            to="/"
            className={`${
              isActive('/') 
                ? 'bg-blue-50 border-l-4 border-blue-500 text-blue-700' 
                : 'border-l-4 border-transparent text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            } block pl-3 pr-4 py-2 text-base font-medium flex items-center`}
            onClick={() => setIsMenuOpen(false)}
          >
            {/* Small logo in mobile menu */}
            <img src={cookzenLogo} alt="" className="h-6 w-auto mr-2" />
            {t('navigation.home')}
          </Link>
          
          {/* Only show these links if authenticated in mobile view */}
          {isAuthenticated && (
            <>
              <Link
                to="/recipes"
                className={`${
                  isActive('/recipes') 
                    ? 'bg-blue-50 border-l-4 border-blue-500 text-blue-700' 
                    : 'border-l-4 border-transparent text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                } block pl-3 pr-4 py-2 text-base font-medium`}
                onClick={() => setIsMenuOpen(false)}
              >
                {t('navigation.recipes')}
              </Link>
              <Link
                to="/scan"
                className={`${
                  isActive('/scan') 
                    ? 'bg-blue-50 border-l-4 border-blue-500 text-blue-700' 
                    : 'border-l-4 border-transparent text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                } block pl-3 pr-4 py-2 text-base font-medium`}
                onClick={() => setIsMenuOpen(false)}
              >
                {t('navigation.scanIngredients')}
              </Link>
              <Link
                to="/meal-plan"
                className={`${
                  isActive('/meal-plan') 
                    ? 'bg-blue-50 border-l-4 border-blue-500 text-blue-700' 
                    : 'border-l-4 border-transparent text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                } block pl-3 pr-4 py-2 text-base font-medium`}
                onClick={() => setIsMenuOpen(false)}
              >
                {t('navigation.mealPlans')}
              </Link>
              <Link
                to="/shopping-list"
                className={`${
                  isActive('/shopping-list') 
                    ? 'bg-blue-50 border-l-4 border-blue-500 text-blue-700' 
                    : 'border-l-4 border-transparent text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                } block pl-3 pr-4 py-2 text-base font-medium`}
                onClick={() => setIsMenuOpen(false)}
              >
                {t('navigation.shoppingLists')}
              </Link>
            </>
          )}
        </div>

        {/* Mobile auth section */}
        <div className="pt-4 pb-3 border-t border-gray-200">
          {isAuthenticated ? (
            <div className="space-y-1">
              <Link
                to="/profile"
                className="block pl-3 pr-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                onClick={() => setIsMenuOpen(false)}
              >
                {t('common.profile')}
              </Link>
              <button
                className="block w-full text-left pl-3 pr-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                onClick={() => {
                  logout();
                  setIsMenuOpen(false);
                }}
              >
                {t('common.logout')}
              </button>
            </div>
          ) : (
            <div className="space-y-1">
              <Link
                to="/login"
                className="block pl-3 pr-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                onClick={() => setIsMenuOpen(false)}
              >
                {t('common.login')}
              </Link>
              <Link
                to="/register"
                className="block pl-3 pr-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                onClick={() => setIsMenuOpen(false)}
              >
                {t('common.register')}
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 