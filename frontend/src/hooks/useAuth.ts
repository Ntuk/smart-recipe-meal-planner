import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  preferences?: {
    dietary_preferences?: string[];
    favorite_cuisines?: string[];
  };
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export const useAuth = () => {
  const queryClient = useQueryClient();
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: authApi.isAuthenticated(),
    isLoading: true,
    error: null,
  });

  // Fetch user profile if authenticated
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getProfile,
    enabled: authState.isAuthenticated,
    retry: false,
    onError: () => {
      // If token is invalid, log out
      authApi.logout();
      setAuthState(prev => ({
        ...prev,
        isAuthenticated: false,
        user: null,
      }));
    }
  });

  // Update auth state when user data changes
  useEffect(() => {
    if (!isLoading) {
      setAuthState(prev => ({
        ...prev,
        user,
        isLoading,
        error: error ? (error as Error).message : null,
      }));
    }
  }, [user, isLoading, error]);

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setAuthState({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      queryClient.setQueryData(['user'], data.user);
    },
    onError: (error) => {
      setAuthState(prev => ({
        ...prev,
        error: (error as Error).message,
        isLoading: false,
      }));
    }
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setAuthState({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      queryClient.setQueryData(['user'], data.user);
    },
    onError: (error) => {
      setAuthState(prev => ({
        ...prev,
        error: (error as Error).message,
        isLoading: false,
      }));
    }
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (data) => {
      setAuthState(prev => ({
        ...prev,
        user: data,
      }));
      queryClient.setQueryData(['user'], data);
    }
  });

  // Logout function
  const logout = useCallback(() => {
    authApi.logout();
    queryClient.removeQueries({ queryKey: ['user'] });
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, [queryClient]);

  return {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading || registerMutation.isPending || loginMutation.isPending,
    error: authState.error,
    register: registerMutation.mutate,
    login: loginMutation.mutate,
    logout,
    updateProfile: updateProfileMutation.mutate,
  };
}; 