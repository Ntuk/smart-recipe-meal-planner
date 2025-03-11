import React from 'react';
import { useTranslation } from 'react-i18next';

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  
  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };
  
  return (
    <div className="flex items-center space-x-2">
      <button
        className={`px-2 py-1 text-sm rounded ${i18n.language === 'en' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
        onClick={() => changeLanguage('en')}
      >
        EN
      </button>
      <button
        className={`px-2 py-1 text-sm rounded ${i18n.language === 'fi' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
        onClick={() => changeLanguage('fi')}
      >
        FI
      </button>
      <button
        className={`px-2 py-1 text-sm rounded ${i18n.language === 'sv' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
        onClick={() => changeLanguage('sv')}
      >
        SV
      </button>
    </div>
  );
};

export default LanguageSwitcher; 