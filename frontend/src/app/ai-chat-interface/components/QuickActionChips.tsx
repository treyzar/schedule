'use client';

import Icon from '@/components/ui/AppIcon';

interface QuickActionChip {
  id: string;
  label: string;
  icon: string;
  query: string;
}

interface QuickActionChipsProps {
  onChipClick: (query: string) => void;
}

const QuickActionChips = ({ onChipClick }: QuickActionChipsProps) => {
  const quickActions: QuickActionChip[] = [
    {
      id: '1',
      label: 'Найти свободное время',
      icon: 'MagnifyingGlassIcon',
      query: 'Найди свободное время на этой неделе для встречи на 1 час',
    },
    {
      id: '2',
      label: 'Показать конфликты',
      icon: 'ExclamationTriangleIcon',
      query: 'Покажи все конфликты в моем расписании',
    },
    {
      id: '3',
      label: 'Оптимизировать день',
      icon: 'BoltIcon',
      query: 'Оптимизируй мое расписание на сегодня',
    },
    {
      id: '4',
      label: 'Статистика времени',
      icon: 'ChartBarIcon',
      query: 'Покажи статистику использования времени за неделю',
    },
  ];

  return (
    <div className="flex flex-wrap gap-2 p-4 border-t border-border bg-muted/30">
      {quickActions.map((action) => (
        <button
          key={action.id}
          onClick={() => onChipClick(action.query)}
          className="flex items-center gap-2 px-3 py-2 rounded-full bg-card border border-border text-foreground hover:bg-primary hover:text-primary-foreground hover:border-primary transition-smooth shadow-elevation-sm"
        >
          <Icon name={action.icon as any} size={16} />
          <span className="text-xs font-body font-medium">{action.label}</span>
        </button>
      ))}
    </div>
  );
};

export default QuickActionChips;
