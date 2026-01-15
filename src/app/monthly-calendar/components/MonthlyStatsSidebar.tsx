'use client';

import Icon from '@/components/ui/AppIcon';

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  time: string;
  category: 'work' | 'personal' | 'meeting' | 'deadline';
  priority: 'high' | 'medium' | 'low';
}

interface MonthlyStatsSidebarProps {
  events: CalendarEvent[];
  currentDate: Date;
}

const MonthlyStatsSidebar = ({ events, currentDate }: MonthlyStatsSidebarProps) => {
  const getCategoryStats = () => {
    const stats = {
      work: 0,
      personal: 0,
      meeting: 0,
      deadline: 0,
    };

    events.forEach((event) => {
      stats[event.category]++;
    });

    return stats;
  };

  const getBusiestDay = () => {
    const dayCount: Record<string, number> = {};

    events.forEach((event) => {
      dayCount[event.date] = (dayCount[event.date] || 0) + 1;
    });

    const busiestDate = Object.entries(dayCount).sort((a, b) => b[1] - a[1])[0];

    if (!busiestDate) return null;

    const date = new Date(busiestDate[0]);
    return {
      date: date.getDate(),
      count: busiestDate[1],
    };
  };

  const stats = getCategoryStats();
  const busiestDay = getBusiestDay();

  const categoryInfo = [
    { key: 'work', label: 'Работа', icon: 'BriefcaseIcon', color: 'text-primary' },
    { key: 'personal', label: 'Личное', icon: 'UserIcon', color: 'text-secondary' },
    { key: 'meeting', label: 'Встречи', icon: 'UsersIcon', color: 'text-accent' },
    { key: 'deadline', label: 'Дедлайны', icon: 'ClockIcon', color: 'text-destructive' },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="text-lg font-heading font-semibold text-foreground mb-4">
          Статистика месяца
        </h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-muted rounded-md">
            <span className="text-sm font-body text-muted-foreground">Всего событий</span>
            <span className="text-xl font-heading font-semibold text-foreground">
              {events.length}
            </span>
          </div>

          {busiestDay && (
            <div className="flex items-center justify-between p-3 bg-primary/10 rounded-md">
              <span className="text-sm font-body text-muted-foreground">
                Самый загруженный день
              </span>
              <span className="text-xl font-heading font-semibold text-primary">
                {busiestDay.date} ({busiestDay.count})
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="text-lg font-heading font-semibold text-foreground mb-4">
          Распределение по категориям
        </h3>

        <div className="space-y-3">
          {categoryInfo.map((category) => (
            <div
              key={category.key}
              className="flex items-center justify-between p-3 bg-muted rounded-md"
            >
              <div className="flex items-center gap-2">
                <Icon name={category.icon as any} size={18} className={category.color} />
                <span className="text-sm font-body text-foreground">{category.label}</span>
              </div>
              <span className="text-lg font-heading font-semibold text-foreground">
                {stats[category.key as keyof typeof stats]}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="text-lg font-heading font-semibold text-foreground mb-4">
          Быстрые действия
        </h3>

        <div className="space-y-2">
          <button className="w-full flex items-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:shadow-elevation-md transition-smooth">
            <Icon name="PlusCircleIcon" size={20} />
            <span className="text-sm font-body font-medium">Добавить событие</span>
          </button>

          <button className="w-full flex items-center gap-2 px-4 py-3 bg-secondary text-secondary-foreground rounded-md hover:shadow-elevation-md transition-smooth">
            <Icon name="DocumentDuplicateIcon" size={20} />
            <span className="text-sm font-body font-medium">Применить шаблон</span>
          </button>

          <button className="w-full flex items-center gap-2 px-4 py-3 bg-muted text-foreground rounded-md hover:bg-muted/80 transition-smooth">
            <Icon name="ArrowDownTrayIcon" size={20} />
            <span className="text-sm font-body font-medium">Экспорт месяца</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default MonthlyStatsSidebar;
