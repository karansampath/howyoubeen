'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, User, APIError } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = api.getAuthToken();
      if (token) {
        try {
          const response = await api.getCurrentUser();
          setUser(response.user);
        } catch (error) {
          // Token might be expired or invalid
          console.error('Failed to get current user:', error);
          api.setAuthToken(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    setLoading(true);
    try {
      const response = await api.login({ email, password });
      setUser(response.user);
    } catch (error) {
      setUser(null);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (username: string, email: string, password: string, fullName: string): Promise<void> => {
    setLoading(true);
    try {
      const response = await api.register({
        username,
        email,
        password,
        full_name: fullName,
      });
      setUser(response.user);
    } catch (error) {
      setUser(null);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    setLoading(true);
    try {
      await api.logout();
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with logout even if API call fails
    } finally {
      setUser(null);
      setLoading(false);
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const response = await api.refreshToken();
      setUser(response.user);
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, log out the user
      api.setAuthToken(null);
      setUser(null);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
