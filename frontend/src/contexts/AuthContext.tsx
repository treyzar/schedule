'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { checkAuthStatus, logout as logoutApi, initiateGoogleAuth, AuthStatus, isProtectedRoute } from '@/lib/auth';
import { useRouter, usePathname } from 'next/navigation';

interface AuthContextType extends AuthStatus {
  isLoading: boolean;
  error: string | null;
  logout: () => Promise<void>;
  login: () => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthStatus>({
    is_authenticated: false,
    last_sync: null,
    email: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const router = useRouter();
  const pathname = usePathname();

  /**
   * Проверка и обновление статуса авторизации
   */
  const refreshAuth = useCallback(async () => {
    try {
      setError(null);
      const status = await checkAuthStatus();
      setAuthState(status);

      // Если не авторизован и на защищённом маршруте - редирект на страницу авторизации
      if (!status.is_authenticated && isProtectedRoute(pathname)) {
        // Проверяем, есть ли параметр auth=success в URL (после OAuth редиректа)
        if (typeof window !== 'undefined') {
          const urlParams = new URLSearchParams(window.location.search);
          const authSuccess = urlParams.get('auth');
          
          if (authSuccess === 'success') {
            // Если это редирект после OAuth, пробуем ещё раз через 1.5 секунды
            // Сессия должна установиться за это время
            setTimeout(async () => {
              const retryStatus = await checkAuthStatus();
              if (!retryStatus.is_authenticated) {
                // Если всё ещё не авторизован, пробуем ещё раз через 2 секунды
                setTimeout(async () => {
                  const finalStatus = await checkAuthStatus();
                  if (!finalStatus.is_authenticated) {
                    router.push('/google-auth');
                  }
                }, 2000);
              }
            }, 1500);
            return;
          }
        }
        
        router.push('/google-auth');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
      setAuthState({
        is_authenticated: false,
        last_sync: null,
        email: null,
      });
    } finally {
      setIsLoading(false);
    }
  }, [pathname, router]);

  /**
   * Первичная загрузка статуса авторизации
   */
  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  /**
   * Выход из системы
   */
  const logout = useCallback(async () => {
    try {
      await logoutApi();
      setAuthState({
        is_authenticated: false,
        last_sync: null,
        email: null,
      });
      router.push('/google-auth');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logout failed');
    }
  }, [router]);

  /**
   * Начало авторизации через Google
   */
  const login = useCallback(() => {
    initiateGoogleAuth();
  }, []);

  const value: AuthContextType = {
    ...authState,
    isLoading,
    error,
    logout,
    login,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Хук для использования контекста авторизации
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
