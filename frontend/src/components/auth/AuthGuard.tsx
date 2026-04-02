'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';
import SkyengStatusBadge from '@/components/ui/SkyengStatusBadge';

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * Guard для проверки авторизации.
 * Сейчас Skyeng авторизация опциональна (отключена).
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  
  // Страницы, которые не требуют авторизации
  const publicPaths = [
    '/',
    '/google-auth',
    '/skyeng-login',
  ];
  
  useEffect(() => {
    const checkAuth = async () => {
      // Если мы на публичной странице, не проверяем
      if (publicPaths.some(path => pathname.startsWith(path))) {
        return;
      }
      
      try {
        const response = await fetch('http://localhost:8000/parse_calendar/status/', {
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          
          // ⚠️ Skyeng авторизация временно отключена
          // Проверка requires_skyeng_auth закомментирована
          /*
          if (data.requires_skyeng_auth) {
            const nextUrl = encodeURIComponent(pathname);
            router.push(`/skyeng-login?next=${nextUrl}`);
            return;
          }
          */
          
          // Если вообще не авторизован в Google - редирект на главную
          if (!data.google_authenticated) {
            router.push('/google-auth');
            return;
          }
        }
      } catch (err) {
        console.error('Auth check failed:', err);
      }
    };
    
    checkAuth();
  }, [pathname, router]);
  
  return <>{children}</>;
}

/**
 * Компонент для отображения статуса авторизации в хедере.
 */
export function AuthStatusDisplay() {
  const router = useRouter();
  
  return (
    <div className="flex items-center gap-4">
      {/* Статус Google */}
      <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-lg">
        <Icon name="CloudIcon" size={16} className="text-primary" />
        <span className="text-xs font-medium text-foreground">Google Calendar</span>
      </div>
      
      {/* Статус Skyeng */}
      <SkyengStatusBadge />
      
      {/* Кнопка настроек авторизации */}
      <button
        onClick={() => router.push('/auth-settings')}
        className="p-2 hover:bg-muted/50 rounded-lg transition-colors"
        title="Настройки авторизации"
      >
        <Icon name="Cog6ToothIcon" size={20} className="text-muted-foreground" />
      </button>
    </div>
  );
}
