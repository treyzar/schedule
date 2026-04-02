'use client';

import Icon from '@/components/ui/AppIcon';

interface QuickActionChip {
  id: string;
  label: string;
  icon: string;
  query: string;
  category: 'analysis' | 'scheduling' | 'optimization' | 'stats';
}

interface QuickActionChipsProps {
  onChipClick: (query: string) => void;
}

const QuickActionChips = ({ onChipClick }: QuickActionChipsProps) => {
  const quickActions: QuickActionChip[] = [
    {
      id: '1',
      label: 'Найти время',
      icon: 'MagnifyingGlassIcon',
      query: 'Найди свободное время на этой неделе для встречи на 1 час',
      category: 'scheduling',
    },
    {
      id: '2',
      label: 'Конфликты',
      icon: 'ExclamationTriangleIcon',
      query: 'Покажи все конфликты в моем расписании и предложи решения',
      category: 'analysis',
    },
    {
      id: '3',
      label: 'Оптимизация',
      icon: 'BoltIcon',
      query: 'Оптимизируй мое расписание на сегодня: предложи перерывы и группировку задач',
      category: 'optimization',
    },
    {
      id: '4',
      label: 'Статистика',
      icon: 'ChartBarIcon',
      query: 'Покажи детальную статистику использования времени за неделю: встречи, задачи, свободное время',
      category: 'stats',
    },
    {
      id: '5',
      label: 'Планы на завтра',
      icon: 'SunIcon',
      query: 'Какие у меня планы на завтра? Составь краткую сводку по расписанию',
      category: 'scheduling',
    },
    {
      id: '6',
      label: 'Перерывы',
      icon: 'CoffeeBeanIcon',
      query: 'Найди оптимальное время для перерывов в моем расписании на сегодня',
      category: 'optimization',
    },
  ];

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'analysis': 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100',
      'scheduling': 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
      'optimization': 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
      'stats': 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
    };
    return colors[category] || 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100';
  };

  return (
    <div className="flex flex-wrap gap-2 p-4 border-t border-border bg-muted/30">
      <span className="text-xs font-caption text-muted-foreground w-full mb-1">Быстрые команды:</span>
      {quickActions.map((action) => (
        <button
          key={action.id}
          onClick={() => onChipClick(action.query)}
          className={`flex items-center gap-2 px-3 py-2 rounded-full border text-xs font-body font-medium transition-smooth shadow-elevation-sm ${getCategoryColor(action.category)}`}
        >
          <Icon name={action.icon as any} size={14} />
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
};

export default QuickActionChips;
