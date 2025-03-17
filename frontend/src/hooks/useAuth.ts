import { useState, useEffect, useCallback } from 'react';
import { authApiService } from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      
      if (token) {
        try {
          // Get user profile from API
          const userData = await authApiService.getProfile();
          
          setAuthState({
            user: userData,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          console.error('Error fetching user profile:', error);
          // Token might be invalid or expired
          localStorage.removeItem('auth_token');
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      console.log('Attempting login with email:', credentials.email);
      const response = await authApiService.login(credentials);
      console.log('Login response:', response);
      
      // Get user profile after successful login
      const userData = await authApiService.getProfile();
      
      setAuthState({
        user: userData,
        isAuthenticated: true,
        isLoading: false,
      });
      
      return { success: true };
    } catch (error: any) {
      console.error('Login error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        request: error.config?.data
      });

      if (error.response?.status === 401) {
        return { 
          success: false, 
          error: "Invalid email or password" 
        };
      }

      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed. Please try again.' 
      };
    }
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    try {
      console.log('Attempting registration with data:', data);
      const response = await authApiService.register(data);
      console.log('Registration response:', response);
      
      // Save the token if it's in the response
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
      }
      
      // Get user profile after successful registration
      const userData = await authApiService.getProfile();
      
      setAuthState({
        user: userData,
        isAuthenticated: true,
        isLoading: false,
      });
      
      return { success: true };
    } catch (error: any) {
      console.error('Registration error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        request: error.config?.data
      });

      // Handle specific error cases
      if (error.response?.status === 400) {
        const detail = error.response.data?.detail;
        if (detail === "Email already registered") {
          return { success: false, error: "This email is already registered" };
        } else if (detail === "Username already taken") {
          return { success: false, error: "This username is already taken" };
        }
      }

      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed. Please try again.' 
      };
    }
  }, []);

  const logout = useCallback(() => {
    authApiService.logout();
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
  }, []);

  return {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    login,
    register,
    logout,
  };
}; 