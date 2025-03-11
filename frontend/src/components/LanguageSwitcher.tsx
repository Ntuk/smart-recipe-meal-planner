import React from 'react';
import { useTranslation } from 'react-i18next';

// Flag SVG components
const UKFlag = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 30" width="24" height="12">
    <clipPath id="a">
      <path d="M0 0v30h60V0z"/>
    </clipPath>
    <clipPath id="b">
      <path d="M30 15h30v15zv15H0zH0V0zV0h30z"/>
    </clipPath>
    <g clipPath="url(#a)">
      <path d="M0 0v30h60V0z" fill="#012169"/>
      <path d="M0 0l60 30m0-30L0 30" stroke="#fff" strokeWidth="6"/>
      <path d="M0 0l60 30m0-30L0 30" clipPath="url(#b)" stroke="#C8102E" strokeWidth="4"/>
      <path d="M30 0v30M0 15h60" stroke="#fff" strokeWidth="10"/>
      <path d="M30 0v30M0 15h60" stroke="#C8102E" strokeWidth="6"/>
    </g>
  </svg>
);

const FinnishFlag = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 1100" width="24" height="12">
    <rect width="1800" height="1100" fill="#fff"/>
    <rect width="1800" height="300" y="400" fill="#003580"/>
    <rect width="300" height="1100" x="500" fill="#003580"/>
  </svg>
);

const SwedishFlag = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 10" width="24" height="12">
    <rect width="16" height="10" fill="#006aa7"/>
    <rect width="2" height="10" x="5" fill="#fecc00"/>
    <rect width="16" height="2" y="4" fill="#fecc00"/>
  </svg>
);

const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  
  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };
  
  // Define a common button style with fixed width to prevent layout shifts
  const buttonBaseStyle = "w-10 h-8 flex items-center justify-center text-sm rounded font-medium mx-1";
  const activeStyle = "bg-blue-100 border-2 border-blue-500";
  const inactiveStyle = "bg-gray-100 border border-gray-300 hover:bg-gray-200";
  
  return (
    <div className="flex items-center">
      <button
        className={`${buttonBaseStyle} ${i18n.language === 'en' ? activeStyle : inactiveStyle}`}
        onClick={() => changeLanguage('en')}
        aria-label="Switch to English"
        title="English"
      >
        <UKFlag />
      </button>
      <button
        className={`${buttonBaseStyle} ${i18n.language === 'fi' ? activeStyle : inactiveStyle}`}
        onClick={() => changeLanguage('fi')}
        aria-label="Switch to Finnish"
        title="Suomi"
      >
        <FinnishFlag />
      </button>
      <button
        className={`${buttonBaseStyle} ${i18n.language === 'sv' ? activeStyle : inactiveStyle}`}
        onClick={() => changeLanguage('sv')}
        aria-label="Switch to Swedish"
        title="Svenska"
      >
        <SwedishFlag />
      </button>
    </div>
  );
};

export default LanguageSwitcher; 