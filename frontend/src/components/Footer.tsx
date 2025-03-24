import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './LanguageSwitcher';
import cookzenLogo from '../assets/cookzen_logo.png';
import { Link } from 'react-router-dom';

const Footer = () => {
  const { t } = useTranslation();
  
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto py-8 px-4 overflow-hidden sm:px-6 lg:px-8">
        <div className="flex flex-col items-center">
          <Link to="/" className="mb-4">
            <img 
              src={cookzenLogo} 
              alt="CookZen" 
              className="h-10 w-auto" 
            />
          </Link>
          
          <div className="text-center max-w-md mb-4">
            <p className="text-sm text-gray-500">
              {t('home.description')}
            </p>
          </div>
          
          <LanguageSwitcher />
        </div>
        
        <p className="mt-8 text-center text-sm text-gray-400">
          &copy; {new Date().getFullYear()} Nico Tukiainen. {t('common.allRightsReserved')}
        </p>
      </div>
    </footer>
  );
};

export default Footer; 