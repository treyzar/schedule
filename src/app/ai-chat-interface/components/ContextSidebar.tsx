'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Icon from '@/components/ui/AppIcon';

interface ContextEvent {
  id: string;
  title: string;
  date: string;
  time: string;
  type: 'meeting' | 'task' | 'reminder';
}

interface SuggestedTimeSlot {
  id: string;
  date: string;
  startTime: string;
  endTime: string;
  duration: string;
}

interface ContextSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const ContextSidebar = ({ isOpen, onClose }: ContextSidebarProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const referencedEvents: ContextEvent[] = [
    {
      id: '1',
      title: 'Встреча с командой',
      date: '15.01.2026',
      time: '10:00 - 11:00',
      type: 'meeting',
    },
    {
      id: '2',
      title: 'Подготовка отчета',
      date: '15.01.2026',
      time: '14:00 - 16:00',
      type: 'task',
    },
    {
      id: '3',
      title: 'Звонок клиенту',
      date: '16.01.2026',
      time: '09:00 - 09:30',
      type: 'reminder',
    },
  ];

  const suggestedSlots: SuggestedTimeSlot[] = [
    {
      id: '1',
      date: '15.01.2026',
      startTime: '11:30',
      endTime: '12:30',
      duration: '1 час',
    },
    {
      id: '2',
      date: '16.01.2026',
      startTime: '14:00',
      endTime: '15:00',
      duration: '1 час',
    },
    {
      id: '3',
      date: '17.01.2026',
      startTime: '10:00',
      endTime: '11:00',
      duration: '1 час',
    },
  ];

  const getEventIcon = (type: ContextEvent['type']) => {
    switch (type) {
      case 'meeting':
        return 'UsersIcon';
      case 'task':
        return 'ClipboardDocumentCheckIcon';
      case 'reminder':
        return 'BellIcon';
      default:
        return 'CalendarIcon';
    }
  };

  if (!isHydrated) {
    return null;
  }

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
          <h3 className="text-sm font-heading font-semibold text-foreground">Контекст беседы</h3>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded-md hover:bg-muted transition-smooth"
            aria-label="Закрыть панель"
          >
            <Icon name="XMarkIcon" size={20} />
          </button>
        </div>

        <div className="p-4 space-y-6">
          <div>
            <h4 className="text-xs font-caption font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Упомянутые события
            </h4>
            <div className="space-y-2">
              {referencedEvents.map((event) => (
                <div
                  key={event.id}
                  className="p-3 rounded-md bg-muted hover:bg-muted/70 transition-smooth cursor-pointer"
                >
                  <div className="flex items-start gap-2">
                    <Icon
                      name={getEventIcon(event.type) as any}
                      size={16}
                      className="text-primary mt-0.5 flex-shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-body text-foreground font-medium truncate">
                        {event.title}
                      </p>
                      <p className="text-xs font-caption text-muted-foreground mt-1">
                        {event.date}
                      </p>
                      <p className="text-xs font-caption text-muted-foreground">{event.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-caption font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Предложенные слоты
            </h4>
            <div className="space-y-2">
              {suggestedSlots.map((slot) => (
                <div
                  key={slot.id}
                  className="p-3 rounded-md border border-border hover:border-primary transition-smooth"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-body text-foreground font-medium">
                      {slot.date}
                    </span>
                    <span className="text-xs font-caption text-muted-foreground">
                      {slot.duration}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-caption text-muted-foreground">
                    <Icon name="ClockIcon" size={14} />
                    <span>
                      {slot.startTime} - {slot.endTime}
                    </span>
                  </div>
                  <button className="w-full mt-2 px-3 py-1.5 text-xs font-body font-medium bg-primary text-primary-foreground rounded-md hover:shadow-elevation-md transition-smooth">
                    Добавить в календарь
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-caption font-semibold text-muted-foreground uppercase tracking-wide mb-3">
              Быстрый переход
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
