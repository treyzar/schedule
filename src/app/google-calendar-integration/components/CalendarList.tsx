'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface Calendar {
  id: string;
  name: string;
  color: string;
  eventCount: number;
  isSelected: boolean;
}

interface CalendarListProps {
  calendars: Calendar[];
  onSelectionChange: (calendarId: string, isSelected: boolean) => void;
}

const CalendarList = ({ calendars, onSelectionChange }: CalendarListProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-sm">
        <div className="h-6 bg-muted rounded w-48 mb-4 animate-pulse" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-md border border-border">
              <div className="w-5 h-5 bg-muted rounded animate-pulse" />
              <div className="w-4 h-4 rounded-full bg-muted animate-pulse" />
              <div className="flex-1">
                <div className="h-4 bg-muted rounded w-32 mb-2 animate-pulse" />
                <div className="h-3 bg-muted rounded w-24 animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-sm">
      <h3 className="text-lg font-heading font-semibold text-foreground mb-4">
        Доступные календари
      </h3>
      <div className="space-y-3">
        {calendars.map((calendar) => (
          <label
            key={calendar.id}
            className="flex items-center gap-3 p-3 rounded-md border border-border hover:bg-muted cursor-pointer transition-smooth"
          >
            <input
              type="checkbox"
              checked={calendar.isSelected}
              onChange={(e) => onSelectionChange(calendar.id, e.target.checked)}
              className="w-5 h-5 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2"
            />
            <div
              className="w-4 h-4 rounded-full flex-shrink-0"
              style={{ backgroundColor: calendar.color }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-body font-medium text-foreground truncate">
                {calendar.name}
              </p>
              <p className="text-xs text-muted-foreground">
                {calendar.eventCount} {calendar.eventCount === 1 ? 'событие' : 'событий'}
              </p>
            </div>
            <Icon
              name={calendar.isSelected ? 'CheckIcon' : 'PlusIcon'}
              size={20}
              className={calendar.isSelected ? 'text-success' : 'text-muted-foreground'}
            />
          </label>
        ))}
      </div>
    </div>
  );
};

export default CalendarList;
