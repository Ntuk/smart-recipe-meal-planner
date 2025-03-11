import React from 'react';
import { useTranslation } from 'react-i18next';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const currentLanguage = i18n.language;

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div className="flex items-center space-x-2">
      <button
        className={`px-2 py-1 text-sm rounded ${
          currentLanguage === 'en' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'
        }`}
        onClick={() => changeLanguage('en')}
      >
        EN
      </button>
      <button
        className={`px-2 py-1 text-sm rounded ${
          currentLanguage === 'fi' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'
        }`}
        onClick={() => changeLanguage('fi')}
      >
        FI
      </button>
    </div>
  );
};

export default LanguageSwitcher; 