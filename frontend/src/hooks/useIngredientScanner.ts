import { useMutation } from '@tanstack/react-query';
import { ingredientScannerApi } from '../services/api';

// Hook for scanning ingredients from an image
export const useScanIngredients = () => {
  return useMutation({
    mutationFn: (file: File) => ingredientScannerApi.scanIngredients(file),
  });
};

// Hook for manual input of ingredients
export const useManualInput = () => {
  return useMutation({
    mutationFn: (text: string) => ingredientScannerApi.manualInput(text),
  });
}; 