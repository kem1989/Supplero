'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, authAPI, isAuthenticated } from '../lib/auth';
import { useComponentTracing } from '../hooks/useTracing';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<any>;
  register: (userData: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Use tracing for the auth context
  const tracing = useComponentTracing('AuthContext');

  const refreshUser = async () => {
    try {
      if (isAuthenticated()) {
        tracing.logTraceEvent('Refresh User Started');
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
        tracing.logTraceEvent('Refresh User Completed', { 
          userId: userData.id,
          userEmail: userData.email 
        });
      } else {
        setUser(null);
        tracing.logTraceEvent('Refresh User Skipped - Not Authenticated');
      }
    } catch (error) {
      tracing.logTraceEvent('Refresh User Failed', { 
        error: error instanceof Error ? error.message : String(error) 
      });
      console.error('Failed to refresh user:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      tracing.logTraceEvent('Login Started', { email });
      console.log('AuthContext: Login attempt for:', email);
      console.log('AuthContext: Trace Context:', tracing.traceContext);
      
      const response = await authAPI.login({ email, password });
      console.log('AuthContext: Login response:', response);
      
      setUser(response.user);
      console.log('AuthContext: User set successfully');
      
      tracing.logTraceEvent('Login Completed', { 
        userId: response.user.id,
        userEmail: response.user.email,
        userRole: response.user.role
      });
      
      return response;
    } catch (error) {
      tracing.logTraceEvent('Login Failed', { 
        error: error instanceof Error ? error.message : String(error),
        email 
      });
      console.error('AuthContext: Login failed:', error);
      throw error;
    }
  };

  const register = async (userData: any) => {
    try {
      tracing.logTraceEvent('Registration Started', { 
        email: userData.email,
        username: userData.username 
      });
      
      const newUser = await authAPI.register(userData);
      // After registration, user needs to login
      setUser(null);
      
      tracing.logTraceEvent('Registration Completed', { 
        userId: newUser.id,
        userEmail: newUser.email 
      });
    } catch (error) {
      tracing.logTraceEvent('Registration Failed', { 
        error: error instanceof Error ? error.message : String(error),
        email: userData.email 
      });
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      tracing.logTraceEvent('Logout Started', { 
        userId: user?.id,
        userEmail: user?.email 
      });
      
      await authAPI.logout();
      setUser(null);
      
      tracing.logTraceEvent('Logout Completed');
    } catch (error) {
      tracing.logTraceEvent('Logout Failed', { 
        error: error instanceof Error ? error.message : String(error) 
      });
      console.error('Logout failed:', error);
    }
  };

  useEffect(() => {
    tracing.logTraceEvent('AuthContext Initialization Started');
    refreshUser();
    tracing.logTraceEvent('AuthContext Initialization Completed');
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 