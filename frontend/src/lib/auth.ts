/**
 * Модуль аутентификации и авторизации
 * Управляет проверкой статуса авторизации и защитой маршрутов
 */

export interface AuthStatus {
  is_authenticated: boolean;
  last_sync: string | null;
  email: string | null;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Проверка статуса авторизации пользователя
 */
export async function checkAuthStatus(): Promise<AuthStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/parse_calendar/status/`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return {
        is_authenticated: false,
        last_sync: null,
        email: null,
      };
    }

    const data = await response.json();
    return {
      is_authenticated: data.is_authenticated || false,
      last_sync: data.last_sync || null,
      email: data.email || null,
    };
  } catch (error) {
    console.error('Auth check failed:', error);
    return {
      is_authenticated: false,
      last_sync: null,
      email: null,
    };
  }
}

/**
 * Выход из системы
 */
export async function logout(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/parse_calendar/logout/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.ok;
  } catch (error) {
    console.error('Logout failed:', error);
    return false;
  }
}

/**
 * Начало процесса авторизации через Google
 */
export function initiateGoogleAuth(): void {
  window.location.href = `${API_BASE_URL}/parse_calendar/authorize/`;
}

/**
 * Список маршрутов, требующих обязательной авторизации
 */
export const PROTECTED_ROUTES = [
  '/daily-schedule-config',
  '/weekly-schedule-overview',
  '/monthly-calendar',
  '/ai-chat-interface',
  '/personal-cabinet-parsing',
  '/google-calendar-integration',
];

/**
 * Проверка, является ли маршрут защищённым
 */
export function isProtectedRoute(pathname: string): boolean {
  // Корневой путь перенаправляем на авторизацию
  if (pathname === '/' || pathname === '/page') {
    return true;
  }
  
  return PROTECTED_ROUTES.some(route => pathname.startsWith(route));
}
