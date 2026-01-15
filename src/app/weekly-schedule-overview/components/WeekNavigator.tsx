'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface WeekNavigatorProps {
  currentWeek: Date;
  onWeekChange: (date: Date) => void;
}

const WeekNavigator = ({ currentWeek, onWeekChange }: WeekNavigatorProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) {
    return (
      <div className="flex items-center justify-between p-4 bg-card rounded-lg border border-border">
        <div className="h-10 w-32 bg-muted animate-pulse rounded" />
        <div className="h-10 w-48 bg-muted animate-pulse rounded" />
        <div className="h-10 w-32 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  const getWeekRange = (date: Date) => {
    const start = new Date(date);
    start.setDate(start.getDate() - start.getDay() + 1);
    const end = new Date(start);
    end.setDate(end.getDate() + 6);
    return { start, end };
  };

  const formatWeekRange = (date: Date) => {
    const { start, end } = getWeekRange(date);
    const startStr = start.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
    const endStr = end.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
    return `${startStr} - ${endStr}`;
  };

  const handlePrevWeek = () => {
    const newDate = new Date(currentWeek);
    newDate.setDate(newDate.getDate() - 7);
    onWeekChange(newDate);
  };

  const handleNextWeek = () => {
    const newDate = new Date(currentWeek);
    newDate.setDate(newDate.getDate() + 7);
    onWeekChange(newDate);
  };

  const handleToday = () => {
    onWeekChange(new Date());
  };

  return (
    <div className="flex items-center justify-between p-4 bg-card rounded-lg border border-border shadow-elevation-sm">
      <button
        onClick={handlePrevWeek}
        className="flex items-center gap-2 px-4 py-2 rounded-md hover:bg-muted transition-smooth"
        aria-label="Предыдущая неделя"
      >
        <Icon name="ChevronLeftIcon" size={20} />
        <span className="hidden sm:inline text-sm font-body">Назад</span>
      </button>

      <div className="flex items-center gap-3">
        <button
          onClick={handleToday}
          className="px-4 py-2 text-sm font-body text-primary hover:bg-muted rounded-md transition-smooth"
        >
          Сегодня
        </button>
        <h2 className="text-lg font-heading font-semibold text-foreground">
          {formatWeekRange(currentWeek)}
        </h2>
      </div>

      <button
        onClick={handleNextWeek}
        className="flex items-center gap-2 px-4 py-2 rounded-md hover:bg-muted transition-smooth"
        aria-label="Следующая неделя"
      >
        <span className="hidden sm:inline text-sm font-body">Вперёд</span>
        <Icon name="ChevronRightIcon" size={20} />
      </button>
    </div>
  );
};

export default WeekNavigator;
