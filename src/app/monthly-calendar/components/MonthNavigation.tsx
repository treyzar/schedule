'use client';

import Icon from '@/components/ui/AppIcon';

interface MonthNavigationProps {
  currentDate: Date;
  onPreviousMonth: () => void;
  onNextMonth: () => void;
  onTodayClick: () => void;
  onYearChange: (year: number) => void;
}

const MonthNavigation = ({
  currentDate,
  onPreviousMonth,
  onNextMonth,
  onTodayClick,
  onYearChange,
}: MonthNavigationProps) => {
  const months = [
    'Январь',
    'Февраль',
    'Март',
    'Апрель',
    'Май',
    'Июнь',
    'Июль',
    'Август',
    'Сентябрь',
    'Октябрь',
    'Ноябрь',
    'Декабрь',
  ];

  const currentYear = currentDate.getFullYear();
  const years = Array.from({ length: 10 }, (_, i) => currentYear - 5 + i);

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
      <div className="flex items-center gap-3">
        <h2 className="text-2xl font-heading font-semibold text-foreground">
          {months[currentDate.getMonth()]} {currentDate.getFullYear()}
        </h2>
        <button
          onClick={onTodayClick}
          className="px-3 py-1.5 text-sm font-body text-primary hover:bg-primary/10 rounded-md transition-smooth"
        >
          Сегодня
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onPreviousMonth}
          className="p-2 rounded-md hover:bg-muted transition-smooth"
          title="Предыдущий месяц"
        >
          <Icon name="ChevronLeftIcon" size={20} className="text-foreground" />
        </button>

        <select
          value={currentYear}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="px-3 py-2 bg-background border border-border rounded-md text-sm font-body text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>

        <button
          onClick={onNextMonth}
          className="p-2 rounded-md hover:bg-muted transition-smooth"
          title="Следующий месяц"
        >
          <Icon name="ChevronRightIcon" size={20} className="text-foreground" />
        </button>
      </div>
    </div>
  );
};

export default MonthNavigation;
