'use client';

import { useState, useCallback } from 'react';
import Icon from '@/components/ui/AppIcon';

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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const GoogleEventCreator = () => {
  // Форма создания события
  const [formData, setFormData] = useState({
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
  const [createdEvent, setCreatedEvent] = useState<GoogleEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [freeSlots, setFreeSlots] = useState<FreeSlot[]>([]);
  const [showFreeTimeSearch, setShowFreeTimeSearch] = useState(false);

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

      setCreatedEvent(data.event);
      setFormData({
        summary: '',
        description: '',
        location: '',
        start_datetime: '',
        end_datetime: '',
        attendees: '',
        category: 'personal',
        priority: 'normal',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при создании события');
    } finally {
      setIsCreating(false);
    }
  }, [formData]);

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
        // Конфликтов нет, создаём событие
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

  /**
   * Установить время из свободного слота
   */
  const handleSelectFreeSlot = useCallback((slot: FreeSlot) => {
    setFormData((prev) => ({
      ...prev,
      start_datetime: slot.start,
      end_datetime: slot.end,
    }));
    setShowFreeTimeSearch(false);
    setFreeSlots([]);
  }, []);

  /**
   * Форматирование даты для отображения
   */
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

  return (
    <div className="w-full max-w-3xl mx-auto p-4 space-y-6">
      {/* Заголовок */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
          <Icon name="CalendarIcon" size={24} className="text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-heading font-semibold">Создать событие в Google Calendar</h2>
          <p className="text-sm text-muted-foreground">
            Создавайте встречи прямо в вашем календаре
          </p>
        </div>
      </div>

      {/* Ошибка */}
      {error && (
        <div className="p-4 rounded-lg bg-error/10 border border-error/20 text-error">
          <div className="flex items-start gap-2">
            <Icon name="ExclamationTriangleIcon" size={20} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Успешное создание */}
      {createdEvent && (
        <div className="p-4 rounded-lg bg-success/10 border border-success/20">
          <div className="flex items-start gap-3">
            <Icon name="CheckCircleIcon" size={20} className="text-success mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-success mb-2">Событие создано!</h3>
              <p className="text-sm">
                <strong>{createdEvent.summary}</strong>
              </p>
              <p className="text-sm text-muted-foreground">
                {formatDateTime(createdEvent.start?.dateTime || createdEvent.start?.date)} -{' '}
                {formatDateTime(createdEvent.end?.dateTime || createdEvent.end?.date)}
              </p>
              {createdEvent.html_link && (
                <a
                  href={createdEvent.html_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline mt-2 inline-block"
                >
                  Открыть в Google Calendar →
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Форма создания события */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Название события *</label>
          <input
            type="text"
            value={formData.summary}
            onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
            placeholder="Встреча с командой"
            className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
            disabled={isCreating}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Время начала *</label>
            <input
              type="datetime-local"
              value={formData.start_datetime}
              onChange={(e) => setFormData({ ...formData, start_datetime: e.target.value })}
              className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
              disabled={isCreating}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Время окончания *</label>
            <input
              type="datetime-local"
              value={formData.end_datetime}
              onChange={(e) => setFormData({ ...formData, end_datetime: e.target.value })}
              className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
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
            rows={3}
            className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth resize-none"
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
            className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
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
            className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
            disabled={isCreating}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Категория</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
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
              className="w-full px-3 py-2 rounded-md border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth"
              disabled={isCreating}
            >
              <option value="low">Низкий</option>
              <option value="normal">Обычный</option>
              <option value="high">Высокий</option>
            </select>
          </div>
        </div>
      </div>

      {/* Кнопки действий */}
      <div className="flex gap-3 pt-4">
        <button
          onClick={handleCheckConflicts}
          disabled={isCreating || !formData.summary || !formData.start_datetime || !formData.end_datetime}
          className="flex-1 px-4 py-2 bg-warning text-warning-foreground rounded-md hover:bg-warning/90 transition-smooth disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Icon name="ExclamationTriangleIcon" size={16} />
          Проверить конфликты и создать
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
              Создать событие
            </>
          )}
        </button>
      </div>

      {/* Поиск свободного времени */}
      <div className="pt-4 border-t border-border">
        <button
          onClick={() => {
            setShowFreeTimeSearch(!showFreeTimeSearch);
            if (!showFreeTimeSearch) {
              handleFindFreeTime();
            }
          }}
          className="text-sm text-primary hover:underline flex items-center gap-2"
        >
          <Icon name="MagnifyingGlassIcon" size={16} />
          {showFreeTimeSearch ? 'Скрыть свободное время' : 'Найти свободное время'}
        </button>

        {showFreeTimeSearch && (
          <div className="mt-4 space-y-2">
            {freeSlots.length > 0 ? (
              freeSlots.map((slot, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectFreeSlot(slot)}
                  className="w-full p-3 rounded-md border border-border bg-card hover:border-primary transition-smooth text-left flex items-center justify-between"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {formatDateTime(slot.start)} - {formatDateTime(slot.end)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Длительность: {slot.duration_minutes} мин
                    </p>
                  </div>
                  <Icon name="ArrowRightIcon" size={16} className="text-muted-foreground" />
                </button>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">
                {isCreating ? 'Поиск...' : 'Свободное время не найдено'}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Конфликты */}
      {conflicts.length > 0 && (
        <div className="pt-4 border-t border-border">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <Icon name="ExclamationTriangleIcon" size={16} className="text-warning" />
            Конфликтующие события:
          </h3>
          <div className="space-y-2">
            {conflicts.map((conflict) => (
              <div
                key={conflict.id}
                className="p-3 rounded-md border border-warning/20 bg-warning/5"
              >
                <p className="text-sm font-medium">{conflict.summary}</p>
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
  );
};

export default GoogleEventCreator;
