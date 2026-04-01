'use client';

import { useState, useEffect } from 'react';

interface Event {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  day: number;
  category: string;
  color: string;
  description?: string;
}

interface WeeklyGridProps {
  events: Event[];
  currentWeek: Date;
  onEventClick: (event: Event) => void;
  onEventDrop: (eventId: string, newDay: number, newStartTime: string) => void;
}

const WeeklyGrid = ({ events, currentWeek, onEventClick, onEventDrop }: WeeklyGridProps) => {
  const [isHydrated, setIsHydrated] = useState(false);
  const [draggedEvent, setDraggedEvent] = useState<string | null>(null);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

  const getWeekDates = (date: Date) => {
    const dates = [];
    const start = new Date(date);
    start.setDate(start.getDate() - start.getDay() + 1);

    for (let i = 0; i < 7; i++) {
      const day = new Date(start);
      day.setDate(day.getDate() + i);
      dates.push(day);
    }
    return dates;
  };

  const isToday = (date: Date) => {
    if (!isHydrated) return false;
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const weekDates = isHydrated ? getWeekDates(currentWeek) : Array(7).fill(new Date());

  const handleDragStart = (eventId: string) => {
    setDraggedEvent(eventId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (day: number, hour: number) => {
    if (draggedEvent) {
      const newStartTime = `${hour.toString().padStart(2, '0')}:00`;
      onEventDrop(draggedEvent, day, newStartTime);
      setDraggedEvent(null);
    }
  };

  const getEventsForDayAndHour = (day: number, hour: number) => {
    return events.filter((event) => {
      const eventHour = parseInt(event.startTime.split(':')[0]);
      return event.day === day && eventHour === hour;
    });
  };

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-4">
        <div className="h-96 bg-muted animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <div className="min-w-[800px]">
          <div className="grid grid-cols-8 border-b border-border bg-muted/50">
            <div className="p-3 text-sm font-heading font-semibold text-muted-foreground">
              Время
            </div>
            {weekDays.map((day, index) => (
              <div
                key={day}
                className={`p-3 text-center ${
                  isToday(weekDates[index]) ? 'bg-primary/10 border-l-2 border-primary' : ''
                }`}
              >
                <p className="text-sm font-heading font-semibold text-foreground">{day}</p>
                <p className="text-xs font-caption text-muted-foreground">
                  {weekDates[index].getDate()}
                </p>
              </div>
            ))}
          </div>

          <div className="max-h-[600px] overflow-y-auto">
            {hours.map((hour) => (
              <div key={hour} className="grid grid-cols-8 border-b border-border">
                <div className="p-2 text-xs font-caption text-muted-foreground border-r border-border">
                  {hour.toString().padStart(2, '0')}:00
                </div>
                {[0, 1, 2, 3, 4, 5, 6].map((day) => (
                  <div
                    key={`${day}-${hour}`}
                    className={`p-1 min-h-[60px] border-r border-border hover:bg-muted/30 transition-smooth ${
                      isToday(weekDates[day]) ? 'bg-primary/5' : ''
                    }`}
                    onDragOver={handleDragOver}
                    onDrop={() => handleDrop(day, hour)}
                  >
                    {getEventsForDayAndHour(day, hour).map((event) => (
                      <div
                        key={event.id}
                        draggable
                        onDragStart={() => handleDragStart(event.id)}
                        onClick={() => onEventClick(event)}
                        className={`p-2 mb-1 rounded cursor-pointer hover:opacity-80 transition-smooth ${event.color}`}
                      >
                        <p className="text-xs font-body font-medium text-white truncate">
                          {event.title}
                        </p>
                        <p className="text-[10px] font-caption text-white/80">
                          {event.startTime} - {event.endTime}
                        </p>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeeklyGrid;
