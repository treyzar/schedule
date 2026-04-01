'use client';

interface MiniCalendarProps {
  currentDate: Date;
  onMonthSelect: (date: Date) => void;
}

const MiniCalendar = ({ currentDate, onMonthSelect }: MiniCalendarProps) => {
  const months = [
    'Янв',
    'Фев',
    'Мар',
    'Апр',
    'Май',
    'Июн',
    'Июл',
    'Авг',
    'Сен',
    'Окт',
    'Ноя',
    'Дек',
  ];

  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <h3 className="text-lg font-heading font-semibold text-foreground mb-4">Быстрая навигация</h3>

      <div className="grid grid-cols-3 gap-2">
        {months.map((month, index) => (
          <button
            key={month}
            onClick={() => onMonthSelect(new Date(currentYear, index, 1))}
            className={`
              px-3 py-2 rounded-md text-sm font-body transition-smooth
              ${
                index === currentMonth
                  ? 'bg-primary text-primary-foreground font-medium'
                  : 'bg-muted text-foreground hover:bg-muted/80'
              }
            `}
          >
            {month}
          </button>
        ))}
      </div>
    </div>
  );
};

export default MiniCalendar;
