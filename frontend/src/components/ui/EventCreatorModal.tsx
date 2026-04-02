'use client';

import { useState, useCallback, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface EventFormData {
  summary: string;
  description: string;
  location: string;
  start_datetime: string;
  end_datetime: string;
  attendees: string;
  category: 'personal' | 'work' | 'meeting' | 'study' | 'other';
  priority: 'low' | 'normal' | 'high';
}

interface GoogleEvent {
  id: string;
  summary: string;
  description?: string;
  location?: string;
  start: { dateTime?: string; date?: string };
  end: { dateTime?: string; date?: string };
  html_link?: string;
}

interface Conflict {
  id: string;
  summary: string;
  start: { dateTime?: string; date?: string };
  end: { dateTime?: string; date?: string };
}

interface FreeSlot {
  start: string;
  end: string;
  duration_minutes: number;
}

interface EventCreatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: {
    start_datetime?: string;
    end_datetime?: string;
  };
  onSuccess?: (event: GoogleEvent) => void;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const EventCreatorModal = ({
  isOpen,
  onClose,
  initialData,
  onSuccess,
}: EventCreatorModalProps) => {
  const [formData, setFormData] = useState<EventFormData>({
    summary: '',
    description: '',
    location: '',
    start_datetime: '',
    end_datetime: '',
    attendees: '',
    category: 'personal',
    priority: 'normal',
  });

  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [showFreeTimeSearch, setShowFreeTimeSearch] = useState(false);
  const [freeSlots, setFreeSlots] = useState<FreeSlot[]>([]);

  // Сбрасываем форму при открытии
  useEffect(() => {
    if (isOpen) {
      setFormData({
        summary: '',
        description: '',
        location: '',
        start_datetime: initialData?.start_datetime || '',
        end_datetime: initialData?.end_datetime || '',
        attendees: '',
        category: 'personal',
        priority: 'normal',
      });
      setError(null);
      setConflicts([]);
      setShowFreeTimeSearch(false);
      setFreeSlots([]);
    }
  }, [isOpen, initialData]);

  /**
   * Создание события в Google Calendar
   */
  const handleCreateEvent = useCallback(async () => {
    if (!formData.summary || !formData.start_datetime || !formData.end_datetime) {
      setError('Заполните название, время начала и окончания события');
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/parse_calendar/events/create/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          summary: formData.summary,
          start_datetime: formData.start_datetime,
          end_datetime: formData.end_datetime,
          description: formData.description || undefined,
          location: formData.location || undefined,
          attendees: formData.attendees ? formData.attendees.split(',').map((e) => e.trim()) : undefined,
          category: formData.category,
          priority: formData.priority,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Ошибка при создании события');
      }

      onSuccess?.(data.event);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при создании события');
    } finally {
      setIsCreating(false);
    }
  }, [formData, onClose, onSuccess]);

  /**
   * Проверка конфликтов перед созданием
   */
  const handleCheckConflicts = useCallback(async () => {
    if (!formData.start_datetime || !formData.end_datetime) {
      setError('Укажите время начала и окончания для проверки конфликтов');
      return;
    }

    setIsCreating(true);
    setError(null);
    setConflicts([]);

    try {
      const response = await fetch(`${API_BASE_URL}/parse_calendar/events/check-conflict/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_datetime: formData.start_datetime,
          end_datetime: formData.end_datetime,
        }),
      });

      const data = await response.json();

      if (data.has_conflict) {
        setConflicts(data.conflicts);
        setError(`Найдено конфликтов: ${data.conflict_count}`);
      } else {
        await handleCreateEvent();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при проверке конфликтов');
    } finally {
      setIsCreating(false);
    }
  }, [formData, handleCreateEvent]);

  /**
   * Поиск свободного времени
   */
  const handleFindFreeTime = useCallback(async () => {
    setIsCreating(true);
    setError(null);
    setFreeSlots([]);

    try {
      const now = new Date();
      const nextWeek = new Date(now);
      nextWeek.setDate(nextWeek.getDate() + 7);

      const response = await fetch(`${API_BASE_URL}/parse_calendar/events/find-free-time/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          duration_minutes: 60,
          date_start: now.toISOString().split('T')[0],
          date_end: nextWeek.toISOString().split('T')[0],
          working_hours_start: 9,
          working_hours_end: 18,
        }),
      });

      const data = await response.json();
      setFreeSlots(data.free_slots);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при поиске свободного времени');
    } finally {
      setIsCreating(false);
    }
  }, []);

  const handleSelectFreeSlot = (slot: FreeSlot) => {
    setFormData((prev) => ({
      ...prev,
      start_datetime: slot.start,
      end_datetime: slot.end,
    }));
    setShowFreeTimeSearch(false);
    setFreeSlots([]);
  };

  const formatDateTime = (dateTimeString?: string) => {
    if (!dateTimeString) return '';
    try {
      const date = new Date(dateTimeString);
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateTimeString;
    }
  };

  const formatDateTimeLocal = (isoString: string) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toISOString().slice(0, 16);
    } catch {
      return isoString;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Заголовок */}
        <div className="sticky top-0 bg-card border-b border-border p-4 flex items-center justify-between rounded-t-lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Icon name="CalendarIcon" size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-heading font-semibold">Создать событие</h2>
              <p className="text-xs text-muted-foreground">в Google Calendar</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-md transition-smooth"
          >
            <Icon name="XMarkIcon" size={20} className="text-muted-foreground" />
          </button>
        </div>

        {/* Контент */}
        <div className="p-6 space-y-4">
          {/* Ошибка */}
          {error && (
            <div className="p-4 rounded-lg bg-error/10 border border-error/20 text-error">
              <div className="flex items-start gap-2">
                <Icon name="ExclamationTriangleIcon" size={20} className="mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Форма */}
          <div>
            <label className="block text-sm font-medium mb-1">Название события *</label>
            <input
              type="text"
              value={formData.summary}
              onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
              placeholder="Встреча с командой"
              className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
              disabled={isCreating}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Время начала *</label>
              <input
                type="datetime-local"
                value={formatDateTimeLocal(formData.start_datetime)}
                onChange={(e) => {
                  const val = e.target.value;
                  const date = new Date(val);
                  setFormData({ ...formData, start_datetime: date.toISOString() });
                }}
                className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
                disabled={isCreating}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Время окончания *</label>
              <input
                type="datetime-local"
                value={formatDateTimeLocal(formData.end_datetime)}
                onChange={(e) => {
                  const val = e.target.value;
                  const date = new Date(val);
                  setFormData({ ...formData, end_datetime: date.toISOString() });
                }}
                className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
                disabled={isCreating}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Описание</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Описание встречи"
              rows={2}
              className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth resize-none"
              disabled={isCreating}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Местоположение</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="Офис, Zoom, и т.д."
              className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
              disabled={isCreating}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Участники (email через запятую)
            </label>
            <input
              type="text"
              value={formData.attendees}
              onChange={(e) => setFormData({ ...formData, attendees: e.target.value })}
              placeholder="user@example.com, another@example.com"
              className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
              disabled={isCreating}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Категория</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
                disabled={isCreating}
              >
                <option value="personal">Личное</option>
                <option value="work">Работа</option>
                <option value="meeting">Встреча</option>
                <option value="study">Учёба</option>
                <option value="other">Другое</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Приоритет</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 rounded-md border border-border bg-background focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
                disabled={isCreating}
              >
                <option value="low">Низкий</option>
                <option value="normal">Обычный</option>
                <option value="high">Высокий</option>
              </select>
            </div>
          </div>

          {/* Поиск свободного времени */}
          <div className="pt-2 border-t border-border">
            <button
              onClick={() => {
                setShowFreeTimeSearch(!showFreeTimeSearch);
                if (!showFreeTimeSearch) handleFindFreeTime();
              }}
              className="text-sm text-primary hover:underline flex items-center gap-2"
            >
              <Icon name="MagnifyingGlassIcon" size={16} />
              {showFreeTimeSearch ? 'Скрыть свободное время' : 'Найти свободное время'}
            </button>

            {showFreeTimeSearch && freeSlots.length > 0 && (
              <div className="mt-3 space-y-2 max-h-40 overflow-y-auto">
                {freeSlots.map((slot, index) => (
                  <button
                    key={index}
                    onClick={() => handleSelectFreeSlot(slot)}
                    className="w-full p-2 rounded-md border border-border bg-background hover:border-primary transition-smooth text-left text-sm"
                  >
                    {formatDateTime(slot.start)} - {formatDateTime(slot.end)} ({slot.duration_minutes} мин)
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Конфликты */}
          {conflicts.length > 0 && (
            <div className="pt-2 border-t border-border">
              <h3 className="text-sm font-semibold mb-2 flex items-center gap-2 text-warning">
                <Icon name="ExclamationTriangleIcon" size={16} />
                Конфликтующие события:
              </h3>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {conflicts.map((conflict) => (
                  <div
                    key={conflict.id}
                    className="p-2 rounded-md border border-warning/20 bg-warning/5 text-sm"
                  >
                    <p className="font-medium">{conflict.summary}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(conflict.start?.dateTime || conflict.start?.date)} -{' '}
                      {formatDateTime(conflict.end?.dateTime || conflict.end?.date)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Кнопки действий */}
        <div className="sticky bottom-0 bg-card border-t border-border p-4 flex gap-3 rounded-b-lg">
          <button
            onClick={handleCheckConflicts}
            disabled={isCreating || !formData.summary || !formData.start_datetime || !formData.end_datetime}
            className="flex-1 px-4 py-2 bg-warning text-warning-foreground rounded-md hover:bg-warning/90 transition-smooth disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Icon name="ExclamationTriangleIcon" size={16} />
            Проверить конфликты
          </button>

          <button
            onClick={handleCreateEvent}
            disabled={isCreating || !formData.summary || !formData.start_datetime || !formData.end_datetime}
            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-smooth disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isCreating ? (
              <>
                <Icon name="ArrowPathIcon" size={16} className="animate-spin" />
                Создание...
              </>
            ) : (
              <>
                <Icon name="PlusIcon" size={16} />
                Создать
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EventCreatorModal;
