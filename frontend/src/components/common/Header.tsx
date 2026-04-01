'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';

interface NavigationItem {
  label: string;
  href: string;
  icon: string;
  tooltip: string;
}

const Header = () => {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
      icon: 'ChatBubbleLeftRightIcon',
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

  return (
    <header className="fixed top-0 left-0 right-0 z-[100] bg-card shadow-elevation-md">
      <div className="flex items-center h-[60px] px-6">
        <Link href="/daily-schedule-config" className="flex items-center gap-3 mr-8">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary">
            <Icon name="ClockIcon" size={24} className="text-primary-foreground" />
          </div>
          <span className="text-xl font-heading font-semibold text-foreground">SmartScheduler</span>
        </Link>

        <nav className="hidden md:flex items-center gap-2 flex-1">
          {navigationItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              title={item.tooltip}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md transition-smooth
                hover:bg-muted hover:-translate-y-[1px]
                ${
                  isActive(item.href)
                    ? 'bg-primary text-primary-foreground font-medium'
                    : 'text-foreground'
                }
              `}
            >
              <Icon name={item.icon as any} size={20} />
              <span className="text-sm font-body">{item.label}</span>
            </Link>
          ))}
        </nav>

        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden ml-auto p-2 rounded-md hover:bg-muted transition-smooth"
          aria-label="Toggle mobile menu"
        >
          <Icon name={mobileMenuOpen ? 'XMarkIcon' : 'Bars3Icon'} size={24} />
        </button>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden bg-card border-t border-border">
          <nav className="flex flex-col p-4 gap-2">
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-md transition-smooth
                  ${
                    isActive(item.href)
                      ? 'bg-primary text-primary-foreground font-medium'
                      : 'text-foreground hover:bg-muted'
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
