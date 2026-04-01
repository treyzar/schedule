'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface ScheduleEvent {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  category: 'work' | 'personal' | 'break' | 'meeting';
  color: string;
  description?: string;
}

interface EventDetailsModalProps {
  event: ScheduleEvent | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (event: ScheduleEvent) => void;
  onDelete: (eventId: string) => void;
}

const EventDetailsModal = ({
  event,
  isOpen,
  onClose,
  onSave,
  onDelete,
}: EventDetailsModalProps) => {
  const [isHydrated, setIsHydrated] = useState(false);
  const [formData, setFormData] = useState<ScheduleEvent | null>(null);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (event) {
      setFormData(event);
    }
  }, [event]);

  if (!isHydrated || !isOpen || !formData) {
    return null;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData) {
      onSave(formData);
      onClose();
    }
  };

  const handleDelete = () => {
    if (formData && window.confirm('Вы уверены, что хотите удалить это событие?')) {
      onDelete(formData.id);
      onClose();
    }
  };

  const categoryOptions = [
    { value: 'work', label: 'Работа', icon: 'BriefcaseIcon' },
    { value: 'personal', label: 'Личное', icon: 'UserIcon' },
    { value: 'break', label: 'Перерыв', icon: 'CoffeeIcon' },
    { value: 'meeting', label: 'Встреча', icon: 'UsersIcon' },
  ];

  return (
    <>
      <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[200]" onClick={onClose} />
      <div className="fixed inset-0 z-[201] flex items-center justify-center p-4">
        <div className="bg-card rounded-lg shadow-elevation-lg border border-border w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
            <h2 className="text-xl font-heading font-semibold text-foreground">
              Редактировать событие
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-md hover:bg-muted transition-smooth"
              aria-label="Закрыть"
            >
              <Icon name="XMarkIcon" size={24} className="text-muted-foreground" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-body font-medium text-foreground mb-2">
                Название события
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
                placeholder="Введите название"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-body font-medium text-foreground mb-2">
                  Время начала
                </label>
                <input
                  type="time"
                  value={formData.startTime}
                  onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-body font-medium text-foreground mb-2">
                  Время окончания
                </label>
                <input
                  type="time"
                  value={formData.endTime}
                  onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-body font-medium text-foreground mb-2">
                Категория
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {categoryOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, category: option.value as any })}
                    className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-smooth ${
                      formData.category === option.value
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-muted-foreground'
                    }`}
                  >
                    <Icon name={option.icon as any} size={24} className="text-foreground" />
                    <span className="text-xs font-caption text-foreground">{option.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-body font-medium text-foreground mb-2">
                Описание (необязательно)
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth resize-none"
                rows={4}
                placeholder="Добавьте описание события"
              />
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-border">
              <button
                type="button"
                onClick={handleDelete}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-destructive hover:bg-destructive/10 transition-smooth"
              >
                <Icon name="TrashIcon" size={20} />
                <span className="text-sm font-body font-medium">Удалить</span>
              </button>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 rounded-lg border border-border hover:bg-muted transition-smooth"
                >
                  <span className="text-sm font-body font-medium text-foreground">Отмена</span>
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 rounded-lg bg-primary text-primary-foreground hover:shadow-elevation-md transition-smooth"
                >
                  <span className="text-sm font-body font-medium">Сохранить</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </>
  );
};

export default EventDetailsModal;
