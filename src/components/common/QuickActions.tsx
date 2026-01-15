'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Icon from '@/components/ui/AppIcon';

interface QuickAction {
  label: string;
  icon: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'accent';
}

const QuickActions = () => {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);

  const getContextualActions = (): QuickAction[] => {
    const baseActions: QuickAction[] = [
      {
        label: 'AI Помощник',
        icon: 'SparklesIcon',
        onClick: () => console.log('Open AI Assistant'),
        variant: 'primary',
      },
    ];

    if (pathname === '/daily-schedule-config') {
      return [
        ...baseActions,
        {
          label: 'Добавить событие',
          icon: 'PlusCircleIcon',
          onClick: () => console.log('Add event'),
          variant: 'secondary',
        },
        {
          label: 'Оптимизировать',
          icon: 'BoltIcon',
          onClick: () => console.log('Optimize schedule'),
          variant: 'accent',
        },
      ];
    }

    if (pathname === '/weekly-schedule-overview') {
      return [
        ...baseActions,
        {
          label: 'Добавить событие',
          icon: 'PlusCircleIcon',
          onClick: () => console.log('Add event'),
          variant: 'secondary',
        },
        {
          label: 'Экспорт',
          icon: 'ArrowDownTrayIcon',
          onClick: () => console.log('Export schedule'),
          variant: 'secondary',
        },
      ];
    }

    if (pathname === '/monthly-calendar') {
      return [
        ...baseActions,
        {
          label: 'Добавить событие',
          icon: 'PlusCircleIcon',
          onClick: () => console.log('Add event'),
          variant: 'secondary',
        },
      ];
    }

    if (pathname === '/personal-cabinet-parsing' || pathname === '/google-calendar-integration') {
      return [
        {
          label: 'Синхронизировать',
          icon: 'ArrowPathIcon',
          onClick: () => console.log('Sync integrations'),
          variant: 'primary',
        },
        {
          label: 'Настройки',
          icon: 'Cog6ToothIcon',
          onClick: () => console.log('Open settings'),
          variant: 'secondary',
        },
      ];
    }

    return baseActions;
  };

  const actions = getContextualActions();

  const getVariantStyles = (variant?: string) => {
    switch (variant) {
      case 'primary':
        return 'bg-primary text-primary-foreground hover:shadow-elevation-md';
      case 'accent':
        return 'bg-accent text-accent-foreground hover:shadow-elevation-md';
      case 'secondary':
      default:
        return 'bg-secondary text-secondary-foreground hover:shadow-elevation-md';
    }
  };

  return (
    <>
      <div className="hidden lg:flex items-center gap-3">
        {actions.map((action) => (
          <button
            key={action.label}
            onClick={action.onClick}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg transition-smooth
              hover:-translate-y-[1px]
              ${getVariantStyles(action.variant)}
            `}
            title={action.label}
          >
            <Icon name={action.icon as any} size={20} />
            <span className="text-sm font-body font-medium">{action.label}</span>
          </button>
        ))}
      </div>

      <div className="lg:hidden fixed bottom-20 right-4 z-[90]">
        {isExpanded && (
          <div className="flex flex-col gap-2 mb-3">
            {actions.slice(1).map((action) => (
              <button
                key={action.label}
                onClick={() => {
                  action.onClick();
                  setIsExpanded(false);
                }}
                className={`
                  flex items-center gap-2 px-4 py-3 rounded-lg shadow-elevation-lg transition-smooth
                  ${getVariantStyles(action.variant)}
                `}
              >
                <Icon name={action.icon as any} size={20} />
                <span className="text-sm font-body font-medium whitespace-nowrap">
                  {action.label}
                </span>
              </button>
            ))}
          </div>
        )}

        <button
          onClick={() => {
            if (actions.length === 1) {
              actions[0].onClick();
            } else {
              setIsExpanded(!isExpanded);
            }
          }}
          className={`
            flex items-center justify-center w-14 h-14 rounded-full shadow-elevation-lg transition-smooth
            ${getVariantStyles(actions[0].variant)}
            ${isExpanded ? 'rotate-45' : ''}
          `}
          aria-label={isExpanded ? 'Закрыть меню' : 'Открыть быстрые действия'}
        >
          <Icon name={isExpanded ? 'XMarkIcon' : (actions[0].icon as any)} size={24} />
        </button>
      </div>

      {isExpanded && (
        <div
          className="lg:hidden fixed inset-0 z-[80] bg-background"
          onClick={() => setIsExpanded(false)}
        />
      )}
    </>
  );
};

export default QuickActions;
