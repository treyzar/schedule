'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';
import StatusIndicator from './StatusIndicator';
import SkyengStatusBadge from '@/components/ui/SkyengStatusBadge';

interface NavigationItem {
  label: string;
  href: string;
  icon: string;
  tooltip: string;
}

interface AuthStatus {
  is_authenticated: boolean;
  google_authenticated: boolean;
  skyeng_authenticated: boolean;
  is_fully_authenticated: boolean;
  email: string | null;
}

const Header = () => {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Проверяем статус авторизации при загрузке
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/parse_calendar/status/', {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          setAuthStatus(data);
        }
      } catch (error) {
        console.error('Failed to check auth status:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const navigationItems: NavigationItem[] = [
    {
      label: 'Настройка',
      href: '/personal-cabinet-parsing',
      icon: 'CogIcon',
      tooltip: 'Настройка парсинга и интеграций',
    },
    {
      label: 'Помощник',
      href: '/ai-chat-interface',
      icon: 'SparklesIcon',
      tooltip: 'AI помощник для планирования',
    },
    {
      label: 'День',
      href: '/daily-schedule-config',
      icon: 'CalendarDaysIcon',
      tooltip: 'Детальное расписание на день',
    },
    {
      label: 'Неделя',
      href: '/weekly-schedule-overview',
      icon: 'CalendarIcon',
      tooltip: 'Обзор недельного расписания',
    },
    {
      label: 'Месяц',
      href: '/monthly-calendar',
      icon: 'TableCellsIcon',
      tooltip: 'Месячный календарь',
    },
  ];

  const isActive = (href: string) => {
    if (href === '/personal-cabinet-parsing') {
      return pathname === href || pathname === '/google-calendar-integration';
    }
    return pathname === href;
  };

  const isFullyAuthenticated = authStatus?.is_fully_authenticated;
  const showGoogleButton = !authStatus?.google_authenticated;

  return (
    <header className="fixed top-0 left-0 right-0 z-[100] bg-card/95 backdrop-blur-md shadow-elevation-md">
      <div className="flex items-center h-[64px] px-4 md:px-6">
        {/* Логотип с градиентом */}
        <Link href="/daily-schedule-config" className="flex items-center gap-3 mr-6 md:mr-8 group">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl gradient-primary shadow-elevation-md group-hover:shadow-elevation-lg transition-smooth">
            <Icon name="ClockIcon" size={22} className="text-white" />
          </div>
          <div className="hidden sm:block">
            <span className="text-xl font-heading font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              SmartScheduler
            </span>
            <p className="text-[10px] font-caption text-muted-foreground -mt-1">Умное планирование</p>
          </div>
        </Link>

        {/* Навигация для десктопа */}
        <nav className="hidden md:flex items-center gap-1 flex-1">
          {navigationItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              title={item.tooltip}
              className={`
                relative flex items-center gap-2 px-3 py-2 rounded-lg transition-smooth
                hover:bg-muted/80
                ${
                  isActive(item.href)
                    ? 'text-primary font-semibold'
                    : 'text-foreground/80'
                }
              `}
            >
              {isActive(item.href) && (
                <span className="absolute inset-0 bg-primary/10 rounded-lg -z-10" />
              )}
              <Icon name={item.icon as any} size={18} />
              <span className="text-sm font-body">{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* Кнопка мобильного меню */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden ml-auto p-2 rounded-lg hover:bg-muted transition-smooth"
          aria-label="Toggle mobile menu"
        >
          <Icon name={mobileMenuOpen ? 'XMarkIcon' : 'Bars3Icon'} size={24} className="text-foreground" />
        </button>

        {/* Правая часть с индикаторами */}
        <div className="hidden md:flex items-center gap-3 ml-auto">
          {/* Статус Skyeng */}
          <SkyengStatusBadge />

          {/* Статус Google */}
          {!isLoading && authStatus?.google_authenticated && (
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-success/10 rounded-lg">
              <Icon name="CheckCircleIcon" size={14} className="text-success" />
              <span className="text-xs font-medium text-success">Google</span>
            </div>
          )}

          <StatusIndicator />

          {!isLoading && showGoogleButton && (
            <Link
              href="/google-auth"
              className="px-4 py-2 rounded-lg transition-smooth text-sm font-body font-medium gradient-primary text-white hover:shadow-elevation-md"
            >
              Подключить Google
            </Link>
          )}
        </div>
      </div>

      {/* Мобильное меню */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-card border-t border-border shadow-elevation-lg">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <span className="text-sm font-body text-foreground font-medium">Интеграции</span>
            <StatusIndicator />
          </div>

          {/* Статус авторизации в мобильном меню */}
          {!isLoading && (
            <div className="p-4 border-b border-border space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground">Google Calendar</span>
                {authStatus?.google_authenticated ? (
                  <span className="text-sm text-success font-medium">✓ Подключено</span>
                ) : (
                  <Link
                    href="/google-auth"
                    className="text-sm text-primary font-medium hover:underline"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Подключить →
                  </Link>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground">Skyeng</span>
                {authStatus?.skyeng_authenticated ? (
                  <span className="text-sm text-success font-medium">✓ Подключено</span>
                ) : (
                  <Link
                    href="/skyeng-login"
                    className="text-sm text-primary font-medium hover:underline"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Подключить →
                  </Link>
                )}
              </div>
            </div>
          )}

          <nav className="flex flex-col p-3 gap-1">
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-smooth
                  ${
                    isActive(item.href)
                      ? 'bg-primary/10 text-primary font-semibold'
                      : 'text-foreground/80 hover:bg-muted'
                  }
                `}
              >
                <Icon name={item.icon as any} size={20} />
                <span className="text-sm font-body">{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
};

export default Header;
