'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';

interface BreadcrumbItem {
  label: string;
  href: string;
}

const NavigationBreadcrumb = () => {
  const pathname = usePathname();

  const routeMap: Record<string, BreadcrumbItem[]> = {
    '/personal-cabinet-parsing': [
      { label: 'Главная', href: '/daily-schedule-config' },
      { label: 'Настройка', href: '/personal-cabinet-parsing' },
      { label: 'Парсинг личного кабинета', href: '/personal-cabinet-parsing' },
    ],
    '/google-calendar-integration': [
      { label: 'Главная', href: '/daily-schedule-config' },
      { label: 'Настройка', href: '/personal-cabinet-parsing' },
      { label: 'Интеграция Google Calendar', href: '/google-calendar-integration' },
    ],
    '/ai-chat-interface': [
      { label: 'Главная', href: '/daily-schedule-config' },
      { label: 'AI Помощник', href: '/ai-chat-interface' },
    ],
    '/daily-schedule-config': [
      { label: 'Главная', href: '/daily-schedule-config' },
      { label: 'Дневное расписание', href: '/daily-schedule-config' },
    ],
    '/weekly-schedule-overview': [
      { label: 'Главная', href: '/daily-schedule-config' },
      { label: 'Расписание', href: '/weekly-schedule-overview' },
      { label: 'Недельный обзор', href: '/weekly-schedule-overview' },
    ],
    '/monthly-calendar': [
      { label: 'Главная', href: '/daily-schedule-config' },
      { label: 'Расписание', href: '/monthly-calendar' },
      { label: 'Месячный календарь', href: '/monthly-calendar' },
    ],
  };

  const breadcrumbs = routeMap[pathname] || [{ label: 'Главная', href: '/daily-schedule-config' }];

  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <nav
      className="flex items-center gap-2 py-3 text-sm font-caption overflow-x-auto"
      aria-label="Breadcrumb"
    >
      {breadcrumbs.map((crumb, index) => (
        <div key={`${crumb.href}-${index}`} className="flex items-center gap-2 whitespace-nowrap">
          {index > 0 && (
            <Icon
              name="ChevronRightIcon"
              size={16}
              className="text-muted-foreground flex-shrink-0"
            />
          )}
          {index === breadcrumbs.length - 1 ? (
            <span className="text-foreground font-medium">{crumb.label}</span>
          ) : (
            <Link
              href={crumb.href}
              className="text-muted-foreground hover:text-primary transition-smooth"
            >
              {crumb.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  );
};

export default NavigationBreadcrumb;
