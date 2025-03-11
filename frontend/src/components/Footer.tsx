import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './LanguageSwitcher';

const Footer = () => {
  const { t } = useTranslation();
  
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto py-8 px-4 overflow-hidden sm:px-6 lg:px-8">
        <div className="mt-8 flex justify-center">
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