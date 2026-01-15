'use client';

import { useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  time: string;
  category: 'work' | 'personal' | 'meeting' | 'deadline';
  priority: 'high' | 'medium' | 'low';
  description?: string;
  location?: string;
}

interface EventDetailsModalProps {
  event: CalendarEvent | null;
  onClose: () => void;
}

const EventDetailsModal = ({ event, onClose }: EventDetailsModalProps) => {
  useEffect(() => {
    if (event) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [event]);

  if (!event) return null;

  const getCategoryLabel = (category: CalendarEvent['category']) => {
    switch (category) {
      case 'work':
        return 'Работа';
      case 'personal':
        return 'Личное';
      case 'meeting':
        return 'Встреча';
      case 'deadline':
        return 'Дедлайн';
      default:
        return category;
    }
  };

  const getPriorityLabel = (priority: CalendarEvent['priority']) => {
    switch (priority) {
      case 'high':
        return 'Высокий';
      case 'medium':
        return 'Средний';
      case 'low':
        return 'Низкий';
      default:
        return priority;
    }
  };

  const getCategoryColor = (category: CalendarEvent['category']) => {
    switch (category) {
      case 'work':
        return 'bg-primary text-primary-foreground';
      case 'personal':
        return 'bg-secondary text-secondary-foreground';
      case 'meeting':
        return 'bg-accent text-accent-foreground';
      case 'deadline':
        return 'bg-destructive text-destructive-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };

  return (
    <>
      <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[200]" onClick={onClose} />
      <div className="fixed inset-0 z-[201] flex items-center justify-center p-4">
        <div className="bg-card rounded-lg border border-border shadow-elevation-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-xl font-heading font-semibold text-foreground">Детали события</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-md hover:bg-muted transition-smooth"
              aria-label="Закрыть"
            >
              <Icon name="XMarkIcon" size={24} className="text-muted-foreground" />
            </button>
          </div>

          <div className="p-6 space-y-4">
            <div>
              <h3 className="text-2xl font-heading font-semibold text-foreground mb-2">
                {event.title}
              </h3>
              <div className="flex items-center gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-caption font-medium ${getCategoryColor(
                    event.category
                  )}`}
                >
                  {getCategoryLabel(event.category)}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-caption font-medium bg-muted text-muted-foreground">
                  {getPriorityLabel(event.priority)}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Icon name="CalendarIcon" size={20} className="text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-caption text-muted-foreground">Дата</p>
                  <p className="text-base font-body text-foreground">{formatDate(event.date)}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Icon name="ClockIcon" size={20} className="text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-caption text-muted-foreground">Время</p>
                  <p className="text-base font-body text-foreground">{event.time}</p>
                </div>
              </div>

              {event.location && (
                <div className="flex items-start gap-3">
                  <Icon name="MapPinIcon" size={20} className="text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-caption text-muted-foreground">Место</p>
                    <p className="text-base font-body text-foreground">{event.location}</p>
                  </div>
                </div>
              )}

              {event.description && (
                <div className="flex items-start gap-3">
                  <Icon
                    name="DocumentTextIcon"
                    size={20}
                    className="text-muted-foreground mt-0.5"
                  />
                  <div>
                    <p className="text-sm font-caption text-muted-foreground">Описание</p>
                    <p className="text-base font-body text-foreground">{event.description}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-4">
              <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-md hover:shadow-elevation-md transition-smooth">
                <Icon name="PencilIcon" size={18} />
                <span className="text-sm font-body font-medium">Редактировать</span>
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-destructive text-destructive-foreground rounded-md hover:shadow-elevation-md transition-smooth">
                <Icon name="TrashIcon" size={18} />
                <span className="text-sm font-body font-medium">Удалить</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default EventDetailsModal;
