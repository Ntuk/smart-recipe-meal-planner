import { useState, useCallback, useEffect } from 'react';

interface User {
  id: string;
  username: string;
  email: string;
  preferences?: {
    dietary_preferences?: string[];
    favorite_cuisines?: string[];
  };
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock implementation for development
  const register = useCallback((userData: { username: string; email: string; password: string }) => {
    setIsLoading(true);
    setError(null);
    
    // Simulate API call
    setTimeout(() => {
      const mockUser: User = {
        id: '1',
        username: userData.username,
        email: userData.email,
        preferences: {
          dietary_preferences: [],
          favorite_cuisines: []
        }
      };
      
      setUser(mockUser);
      setIsLoading(false);
      // Store in localStorage to persist across refreshes
      localStorage.setItem('user', JSON.stringify(mockUser));
    }, 1000);
  }, []);

  const login = useCallback((credentials: { email: string; password: string }) => {
    setIsLoading(true);
    setError(null);
    
    // Simulate API call
    setTimeout(() => {
      const mockUser: User = {
        id: '1',
        username: 'user',
        email: credentials.email,
        preferences: {
          dietary_preferences: ['Vegetarian'],
          favorite_cuisines: ['Italian', 'Mexican']
        }
      };
      
      setUser(mockUser);
      setIsLoading(false);
      // Store in localStorage to persist across refreshes
      localStorage.setItem('user', JSON.stringify(mockUser));
    }, 1000);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('user');
  }, []);

  const updateProfile = useCallback((profileData: any) => {
    setIsLoading(true);
    setError(null);
    
    // Simulate API call
    setTimeout(() => {
      if (user) {
        const updatedUser = {
          ...user,
          ...profileData,
        };
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }
      setIsLoading(false);
    }, 1000);
  }, [user]);

  // Check if user is already logged in (from localStorage)
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('user');
      }
    }
  }, []);

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    register,
    login,
    logout,
    updateProfile,
  };
}; 