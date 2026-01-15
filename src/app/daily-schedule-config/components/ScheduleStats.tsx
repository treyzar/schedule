'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface ScheduleEvent {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  category: 'work' | 'personal' | 'break' | 'meeting';
  color: string;
  description?: string;
}

interface ScheduleStatsProps {
  events: ScheduleEvent[];
}

interface CategoryStats {
  category: string;
  count: number;
  duration: number;
  percentage: number;
  color: string;
  icon: string;
}

const ScheduleStats = ({ events }: ScheduleStatsProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const calculateDuration = (startTime: string, endTime: string): number => {
    const [startHour, startMinute] = startTime.split(':').map(Number);
    const [endHour, endMinute] = endTime.split(':').map(Number);
    return endHour * 60 + endMinute - (startHour * 60 + startMinute);
  };

  const calculateStats = (): CategoryStats[] => {
    const categoryMap: Record<
      string,
      { count: number; duration: number; color: string; icon: string }
    > = {
      work: { count: 0, duration: 0, color: 'bg-primary', icon: 'BriefcaseIcon' },
      personal: { count: 0, duration: 0, color: 'bg-secondary', icon: 'UserIcon' },
      break: { count: 0, duration: 0, color: 'bg-accent', icon: 'CoffeeIcon' },
      meeting: { count: 0, duration: 0, color: 'bg-warning', icon: 'UsersIcon' },
    };

    let totalDuration = 0;

    events.forEach((event) => {
      const duration = calculateDuration(event.startTime, event.endTime);
      categoryMap[event.category].count += 1;
      categoryMap[event.category].duration += duration;
      totalDuration += duration;
    });

    return Object.entries(categoryMap).map(([category, data]) => ({
      category,
      count: data.count,
      duration: data.duration,
      percentage: totalDuration > 0 ? (data.duration / totalDuration) * 100 : 0,
      color: data.color,
      icon: data.icon,
    }));
  };

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-1/2" />
          <div className="h-20 bg-muted rounded" />
        </div>
      </div>
    );
  }

  const stats = calculateStats();
  const totalEvents = events.length;
  let totalDuration = stats.reduce((sum, stat) => sum + stat.duration, 0);

  const categoryLabels: Record<string, string> = {
    work: 'Работа',
    personal: 'Личное',
    break: 'Перерывы',
    meeting: 'Встречи',
  };

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <div className="px-6 py-4 border-b border-border">
        <h3 className="text-lg font-heading font-semibold text-foreground">Статистика дня</h3>
      </div>

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-muted">
            <div className="flex items-center gap-2 mb-2">
              <Icon name="CalendarDaysIcon" size={20} className="text-primary" />
              <span className="text-xs font-caption text-muted-foreground">Всего событий</span>
            </div>
            <p className="text-2xl font-heading font-bold text-foreground">{totalEvents}</p>
          </div>

          <div className="p-4 rounded-lg bg-muted">
            <div className="flex items-center gap-2 mb-2">
              <Icon name="ClockIcon" size={20} className="text-primary" />
              <span className="text-xs font-caption text-muted-foreground">Занято времени</span>
            </div>
            <p className="text-2xl font-heading font-bold text-foreground">
              {Math.floor(totalDuration / 60)}ч {totalDuration % 60}м
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="text-sm font-body font-medium text-foreground">
            Распределение по категориям
          </h4>
          {stats.map((stat) => (
            <div key={stat.category} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Icon name={stat.icon as any} size={16} className="text-muted-foreground" />
                  <span className="text-sm font-body text-foreground">
                    {categoryLabels[stat.category]}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-caption text-muted-foreground">
                    {stat.count} событий
                  </span>
                  <span className="text-sm font-data text-foreground font-medium">
                    {Math.floor(stat.duration / 60)}ч {stat.duration % 60}м
                  </span>
                </div>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full ${stat.color} transition-all duration-500`}
                  style={{ width: `${stat.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="pt-4 border-t border-border">
          <div className="flex items-center gap-2 p-3 rounded-lg bg-success/10">
            <Icon name="CheckCircleIcon" size={20} className="text-success" />
            <p className="text-sm font-body text-foreground">
              Загруженность дня:{' '}
              <span className="font-medium">{Math.round((totalDuration / (18 * 60)) * 100)}%</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScheduleStats;
