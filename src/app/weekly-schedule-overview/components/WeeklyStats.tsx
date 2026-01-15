'use client';

import Icon from '@/components/ui/AppIcon';

interface WeeklyStatsData {
  totalScheduledHours: number;
  freeHours: number;
  busyDays: number;
  averageHoursPerDay: number;
}

interface WeeklyStatsProps {
  stats: WeeklyStatsData;
}

const WeeklyStats = ({ stats }: WeeklyStatsProps) => {
  const statItems = [
    {
      label: 'Запланировано часов',
      value: stats.totalScheduledHours,
      icon: 'ClockIcon',
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      label: 'Свободно часов',
      value: stats.freeHours,
      icon: 'CheckCircleIcon',
      color: 'text-success',
      bgColor: 'bg-success/10',
    },
    {
      label: 'Занятых дней',
      value: stats.busyDays,
      icon: 'CalendarDaysIcon',
      color: 'text-accent',
      bgColor: 'bg-accent/10',
    },
    {
      label: 'Среднее часов/день',
      value: stats.averageHoursPerDay.toFixed(1),
      icon: 'ChartBarIcon',
      color: 'text-secondary',
      bgColor: 'bg-secondary/10',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {statItems.map((item) => (
        <div
          key={item.label}
          className="p-4 bg-card rounded-lg border border-border shadow-elevation-sm hover:shadow-elevation-md transition-smooth"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className={`p-2 rounded-md ${item.bgColor}`}>
              <Icon name={item.icon as any} size={20} className={item.color} />
            </div>
          </div>
          <p className="text-2xl font-heading font-bold text-foreground mb-1">{item.value}</p>
          <p className="text-sm font-caption text-muted-foreground">{item.label}</p>
        </div>
      ))}
    </div>
  );
};

export default WeeklyStats;
