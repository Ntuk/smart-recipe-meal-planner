import { useTranslation } from 'react-i18next';
import { translateIngredient } from '../i18n/ingredients';

export const useIngredientTranslation = () => {
  const { i18n } = useTranslation();
  
  // Function to translate an ingredient name
  const translateIngredientName = (ingredientName: string): string => {
    return translateIngredient(ingredientName, i18n.language);
  };
  
  // Function to translate an array of ingredient names
  const translateIngredientNames = (ingredientNames: string[]): string[] => {
    return ingredientNames.map(name => translateIngredientName(name));
  };
  
  return {
    translateIngredientName,
    translateIngredientNames
  };
}; 