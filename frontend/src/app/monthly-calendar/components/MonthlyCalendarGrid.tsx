'use client';

import { useState, useEffect } from 'react';

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  time: string;
  category: 'work' | 'personal' | 'meeting' | 'deadline';
  priority: 'high' | 'medium' | 'low';
}

interface MonthlyCalendarGridProps {
  currentDate: Date;
  events: CalendarEvent[];
  onDateClick: (date: Date) => void;
  onEventClick: (event: CalendarEvent) => void;
}

const MonthlyCalendarGrid = ({
  currentDate,
  events,
  onDateClick,
  onEventClick,
}: MonthlyCalendarGridProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-4">
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 35 }).map((_, i) => (
            <div key={i} className="aspect-square bg-muted animate-pulse rounded-md" />
          ))}
        </div>
      </div>
    );
  }

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    const firstDay = new Date(date.getFullYear(), date.getMonth(), 1).getDay();
    return firstDay === 0 ? 6 : firstDay - 1;
  };

  const daysInMonth = getDaysInMonth(currentDate);
  const firstDayOffset = getFirstDayOfMonth(currentDate);
  const totalCells = Math.ceil((daysInMonth + firstDayOffset) / 7) * 7;

  const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

  const getEventsForDate = (day: number) => {
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(
      2,
      '0'
    )}-${String(day).padStart(2, '0')}`;
    return events.filter((event) => event.date === dateStr);
  };

  const getCategoryColor = (category: CalendarEvent['category']) => {
    switch (category) {
      case 'work':
        return 'bg-primary';
      case 'personal':
        return 'bg-secondary';
      case 'meeting':
        return 'bg-accent';
      case 'deadline':
        return 'bg-destructive';
      default:
        return 'bg-muted';
    }
  };

  const isToday = (day: number) => {
    const today = new Date();
    return (
      day === today.getDate() &&
      currentDate.getMonth() === today.getMonth() &&
      currentDate.getFullYear() === today.getFullYear()
    );
  };

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <div className="grid grid-cols-7 border-b border-border">
        {weekDays.map((day) => (
          <div
            key={day}
            className="p-3 text-center text-sm font-heading font-semibold text-muted-foreground bg-muted"
          >
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7">
        {Array.from({ length: totalCells }).map((_, index) => {
          const day = index - firstDayOffset + 1;
          const isValidDay = day > 0 && day <= daysInMonth;
          const dayEvents = isValidDay ? getEventsForDate(day) : [];
          const eventCount = dayEvents.length;

          return (
            <div
              key={index}
              className={`
                min-h-[100px] md:min-h-[120px] border-r border-b border-border p-2
                ${isValidDay ? 'bg-background hover:bg-muted cursor-pointer' : 'bg-muted/30'}
                ${isToday(day) ? 'ring-2 ring-primary ring-inset' : ''}
                transition-smooth
              `}
              onClick={() => {
                if (isValidDay) {
                  onDateClick(new Date(currentDate.getFullYear(), currentDate.getMonth(), day));
                }
              }}
            >
              {isValidDay && (
                <>
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`
                        text-sm font-body font-medium
                        ${isToday(day) ? 'text-primary' : 'text-foreground'}
                      `}
                    >
                      {day}
                    </span>
                    {eventCount > 0 && (
                      <span className="text-xs font-caption text-muted-foreground">
                        {eventCount}
                      </span>
                    )}
                  </div>

                  <div className="space-y-1">
                    {dayEvents.slice(0, 3).map((event) => (
                      <button
                        key={event.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          onEventClick(event);
                        }}
                        className={`
                          w-full text-left px-2 py-1 rounded text-xs font-caption
                          truncate transition-smooth
                          ${getCategoryColor(event.category)} text-white
                          hover:shadow-elevation-sm
                        `}
                        title={`${event.time} - ${event.title}`}
                      >
                        {event.title}
                      </button>
                    ))}
                    {eventCount > 3 && (
                      <div className="text-xs font-caption text-muted-foreground text-center">
                        +{eventCount - 3} ещё
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MonthlyCalendarGrid;
