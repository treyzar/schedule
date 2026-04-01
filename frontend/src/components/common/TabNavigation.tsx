'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';

interface TabItem {
  label: string;
  href: string;
  icon: string;
  group: string;
}

const TabNavigation = () => {
  const pathname = usePathname();

  const tabs: TabItem[] = [
    {
      label: 'Настройка',
      href: '/personal-cabinet-parsing',
      icon: 'CogIcon',
      group: 'setup',
    },
    {
      label: 'Помощник',
      href: '/ai-chat-interface',
      icon: 'ChatBubbleLeftRightIcon',
      group: 'assistant',
    },
    {
      label: 'День',
      href: '/daily-schedule-config',
      icon: 'CalendarDaysIcon',
      group: 'schedule',
    },
    {
      label: 'Неделя',
      href: '/weekly-schedule-overview',
      icon: 'CalendarIcon',
      group: 'schedule',
    },
    {
      label: 'Месяц',
      href: '/monthly-calendar',
      icon: 'TableCellsIcon',
      group: 'schedule',
    },
  ];

  const isActive = (href: string) => {
    if (href === '/personal-cabinet-parsing') {
      return pathname === href || pathname === '/google-calendar-integration';
    }
    return pathname === href;
  };

  return (
    <>
      <div className="hidden md:flex fixed bottom-0 left-0 right-0 z-[100] bg-card border-t border-border shadow-elevation-lg md:relative md:border-0 md:shadow-none md:bg-transparent">
        <div className="flex items-center justify-center w-full gap-1 p-2 md:justify-start md:gap-4 md:p-0">
          {tabs.map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              className={`
                flex flex-col md:flex-row items-center justify-center gap-1 md:gap-2 
                px-3 py-2 md:px-6 md:py-3 rounded-lg transition-smooth
                min-w-[64px] md:min-w-0
                hover:bg-muted hover:-translate-y-[1px]
                ${
                  isActive(tab.href)
                    ? 'bg-primary text-primary-foreground font-medium shadow-elevation-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }
              `}
            >
              <Icon name={tab.icon as any} size={20} />
              <span className="text-xs md:text-sm font-body whitespace-nowrap">{tab.label}</span>
            </Link>
          ))}
        </div>
      </div>

      <div className="md:hidden fixed bottom-0 left-0 right-0 z-[100] bg-card border-t border-border shadow-elevation-lg pb-safe">
        <div className="flex items-center justify-around px-2 py-2">
          {tabs.map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              className={`
                flex flex-col items-center justify-center gap-1 
                px-3 py-2 rounded-lg transition-smooth
                min-w-[64px]
                ${isActive(tab.href) ? 'text-primary font-medium' : 'text-muted-foreground'}
              `}
            >
              <Icon name={tab.icon as any} size={22} />
              <span className="text-[10px] font-caption whitespace-nowrap">{tab.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
};

export default TabNavigation;
