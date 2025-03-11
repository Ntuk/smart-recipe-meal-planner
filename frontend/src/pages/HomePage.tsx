import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const HomePage = () => {
  const [count, setCount] = useState(0);
  const { t } = useTranslation();

  return (
    <div className="bg-gray-100">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            {t('home.title')}
          </h1>
          <p className="mt-5 max-w-xl mx-auto text-xl text-gray-500">
            {t('home.welcome')}
          </p>
          <p className="mt-3 max-w-md mx-auto text-lg text-gray-500">
            {t('home.description')}
          </p>
          <div className="mt-10 flex justify-center gap-4">
            <Link 
              to="/scan" 
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={() => setCount(count + 1)}
            >
              {t('home.scanIngredients')}
            </Link>
            <Link 
              to="/recipes" 
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              {t('home.browseRecipes')}
            </Link>
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900">{t('home.howItWorks')}</h2>
          <div className="mt-6 grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">{t('home.step1Title')}</h3>
                <p className="mt-2 text-sm text-gray-500">
                  {t('home.step1Description')}
                </p>
              </div>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">{t('home.step2Title')}</h3>
                <p className="mt-2 text-sm text-gray-500">
                  {t('home.step2Description')}
                </p>
              </div>
            </div>
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900">{t('home.step3Title')}</h3>
                <p className="mt-2 text-sm text-gray-500">
                  {t('home.step3Description')}
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