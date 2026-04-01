'use client';

import Icon from '@/components/ui/AppIcon';

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

interface EventDetailsModalProps {
  event: Event | null;
  onClose: () => void;
  onEdit: (event: Event) => void;
  onDelete: (eventId: string) => void;
}

const EventDetailsModal = ({ event, onClose, onEdit, onDelete }: EventDetailsModalProps) => {
  if (!event) return null;

  const weekDays = [
    'Понедельник',
    'Вторник',
    'Среда',
    'Четверг',
    'Пятница',
    'Суббота',
    'Воскресенье',
  ];

  return (
    <>
      <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[200]" onClick={onClose} />
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-[201]">
        <div className="bg-card rounded-lg border border-border shadow-elevation-lg overflow-hidden">
          <div className={`p-4 ${event.color}`}>
            <div className="flex items-start justify-between">
              <h3 className="text-lg font-heading font-semibold text-white">{event.title}</h3>
              <button
                onClick={onClose}
                className="p-1 rounded hover:bg-white/20 transition-smooth"
                aria-label="Закрыть"
              >
                <Icon name="XMarkIcon" size={20} className="text-white" />
              </button>
            </div>
          </div>

          <div className="p-6 space-y-4">
            <div className="flex items-center gap-3">
              <Icon name="CalendarIcon" size={20} className="text-muted-foreground" />
              <div>
                <p className="text-sm font-caption text-muted-foreground">День</p>
                <p className="text-sm font-body text-foreground">{weekDays[event.day]}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Icon name="ClockIcon" size={20} className="text-muted-foreground" />
              <div>
                <p className="text-sm font-caption text-muted-foreground">Время</p>
                <p className="text-sm font-body text-foreground">
                  {event.startTime} - {event.endTime}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Icon name="TagIcon" size={20} className="text-muted-foreground" />
              <div>
                <p className="text-sm font-caption text-muted-foreground">Категория</p>
                <p className="text-sm font-body text-foreground">{event.category}</p>
              </div>
            </div>

            {event.description && (
              <div className="flex items-start gap-3">
                <Icon name="DocumentTextIcon" size={20} className="text-muted-foreground" />
                <div>
                  <p className="text-sm font-caption text-muted-foreground">Описание</p>
                  <p className="text-sm font-body text-foreground">{event.description}</p>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3 p-4 border-t border-border">
            <button
              onClick={() => onEdit(event)}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:shadow-elevation-md transition-smooth"
            >
              <Icon name="PencilIcon" size={18} />
              <span className="text-sm font-body font-medium">Редактировать</span>
            </button>
            <button
              onClick={() => {
                onDelete(event.id);
                onClose();
              }}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:shadow-elevation-md transition-smooth"
            >
              <Icon name="TrashIcon" size={18} />
              <span className="text-sm font-body font-medium">Удалить</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default EventDetailsModal;
