'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Icon from '@/components/ui/AppIcon';

export interface CalendarEvent {
  id: string;
  title: string;
  start: { dateTime?: string; date?: string };
  end: { dateTime?: string; date?: string };
  description?: string;
  location?: string;
  extendedProperties?: {
    private?: {
      category?: string;
      priority?: string;
    };
  };
}

export interface TimeSlot {
  id: string;
  date: string;
  startTime: string;
  endTime: string;
  durationMinutes: number;
}

export interface TimeStatistics {
  totalMeetings: number;
  totalTasks: number;
  totalFreeTime: number; // в минутах
  busiestDay: string;
  averageDayLength: number; // в часах
}

interface ContextSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  events?: CalendarEvent[];
  freeSlots?: TimeSlot[];
  statistics?: TimeStatistics;
  isLoading?: boolean;
}

const ContextSidebar = ({
  isOpen,
  onClose,
  events = [],
  freeSlots = [],
  statistics,
  isLoading = false,
}: ContextSidebarProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const getEventIcon = (event: CalendarEvent) => {
    const category = event.extendedProperties?.private?.category || '';
    if (category.toLowerCase().includes('встреча') || category.toLowerCase().includes('meeting')) {
      return 'UsersIcon';
    }
    if (category.toLowerCase().includes('задача') || category.toLowerCase().includes('task')) {
      return 'ClipboardDocumentCheckIcon';
    }
    if (category.toLowerCase().includes('напоминание')) {
      return 'BellIcon';
    }
    return 'CalendarIcon';
  };

  const formatEventTime = (event: CalendarEvent) => {
    const start = event.start.dateTime || event.start.date;
    const end = event.end.dateTime || event.end.date;
    if (!start || !end) return '';

    const startDate = new Date(start);
    const endDate = new Date(end);

    const startTime = startDate.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    const endTime = endDate.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

    return `${startTime} - ${endTime}`;
  };

  const formatEventDate = (event: CalendarEvent) => {
    const start = event.start.dateTime || event.start.date;
    if (!start) return '';
    return new Date(start).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' });
  };

  const getCategoryColor = (event: CalendarEvent) => {
    const category = event.extendedProperties?.private?.category || '';
    const colors: Record<string, string> = {
      'работа': 'bg-blue-100 text-blue-800',
      'личное': 'bg-green-100 text-green-800',
      'учеба': 'bg-purple-100 text-purple-800',
      'встреча': 'bg-orange-100 text-orange-800',
    };
    const key = category.toLowerCase() as string;
    return colors[key] || 'bg-gray-100 text-gray-800';
  };

  if (!isHydrated) {
    return null;
  }

  const recentEvents = events.slice(0, 5);
  const upcomingFreeSlots = freeSlots.slice(0, 3);

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[110] lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed top-[60px] right-0 bottom-0 w-80 bg-card border-l border-border shadow-elevation-lg z-[120]
          transform transition-transform duration-300 ease-in-out overflow-y-auto
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
          lg:relative lg:top-0 lg:translate-x-0 lg:block
        `}
      >
        <div className="sticky top-0 bg-card border-b border-border p-4 flex items-center justify-between z-10">
          <h3 className="text-sm font-heading font-semibold text-foreground">Контекст</h3>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded-md hover:bg-muted transition-smooth"
            aria-label="Закрыть панель"
          >
            <Icon name="XMarkIcon" size={20} />
          </button>
        </div>

        <div className="p-4 space-y-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Icon name="ArrowPathIcon" size={24} className="animate-spin text-primary" />
            </div>
          ) : (
            <>
              {statistics && (
                <div>
                  <h4 className="text-xs font-caption font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                    Статистика за неделю
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-2 rounded-md bg-muted">
                      <span className="text-xs font-body text-muted-foreground">Встречи</span>
                      <span className="text-sm font-semibold">{statistics.totalMeetings}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded-md bg-muted">
                      <span className="text-xs font-body text-muted-foreground">Задачи</span>
                      <span className="text-sm font-semibold">{statistics.totalTasks}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded-md bg-muted">
                      <span className="text-xs font-body text-muted-foreground">Свободное время</span>
                      <span className="text-sm font-semibold">{Math.round(statistics.totalFreeTime / 60)}ч</span>
                    </div>
                  </div>
                </div>
              )}

              {recentEvents.length > 0 && (
                <div>
                  <h4 className="text-xs font-caption font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                    Последние события
                  </h4>
                  <div className="space-y-2">
                    {recentEvents.map((event) => (
                      <div
                        key={event.id}
                        className="p-3 rounded-md bg-muted hover:bg-muted/70 transition-smooth cursor-pointer"
                      >
                        <div className="flex items-start gap-2">
                          <Icon
                            name={getEventIcon(event) as any}
                            size={16}
                            className="text-primary mt-0.5 flex-shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-body text-foreground font-medium truncate">
                              {event.title}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryColor(event)}`}>
                                {event.extendedProperties?.private?.category || 'Общее'}
                              </span>
                            </div>
                            <p className="text-xs font-caption text-muted-foreground mt-1">
                              {formatEventDate(event)}
                            </p>
                            <p className="text-xs font-caption text-muted-foreground">
                              {formatEventTime(event)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {upcomingFreeSlots.length > 0 && (
                <div>
                  <h4 className="text-xs font-caption font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                    Свободные слоты
                  </h4>
                  <div className="space-y-2">
                    {upcomingFreeSlots.map((slot) => (
                      <div
                        key={slot.id}
                        className="p-3 rounded-md border border-border hover:border-primary transition-smooth"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-body text-foreground font-medium">
                            {slot.date}
                          </span>
                          <span className="text-xs font-caption text-muted-foreground">
                            {Math.round(slot.durationMinutes / 60)}ч {slot.durationMinutes % 60}мин
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs font-caption text-muted-foreground">
                          <Icon name="ClockIcon" size={14} />
                          <span>
                            {slot.startTime} - {slot.endTime}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {recentEvents.length === 0 && !statistics && (
                <div className="text-center py-8">
                  <Icon name="CalendarIcon" size={40} className="mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm font-body text-muted-foreground">
                    Нет данных о событиях
                  </p>
                  <Link
                    href="/weekly-schedule-overview"
                    className="mt-3 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:shadow-elevation-md transition-smooth"
                  >
                    <Icon name="CalendarDaysIcon" size={16} />
                    Открыть календарь
                  </Link>
                </div>
              )}
            </>
          )}

          <div>
            <h4 className="text-xs font-caption font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Навигация
            </h4>
            <div className="space-y-2">
              <Link
                href="/daily-schedule-config"
                className="flex items-center gap-2 p-3 rounded-md bg-muted hover:bg-primary hover:text-primary-foreground transition-smooth"
              >
                <Icon name="CalendarDaysIcon" size={18} />
                <span className="text-sm font-body">Дневное расписание</span>
              </Link>
              <Link
                href="/weekly-schedule-overview"
                className="flex items-center gap-2 p-3 rounded-md bg-muted hover:bg-primary hover:text-primary-foreground transition-smooth"
              >
                <Icon name="CalendarIcon" size={18} />
                <span className="text-sm font-body">Недельный обзор</span>
              </Link>
              <Link
                href="/monthly-calendar"
                className="flex items-center gap-2 p-3 rounded-md bg-muted hover:bg-primary hover:text-primary-foreground transition-smooth"
              >
                <Icon name="TableCellsIcon" size={18} />
                <span className="text-sm font-body">Месячный календарь</span>
              </Link>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default ContextSidebar;
