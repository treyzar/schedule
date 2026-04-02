'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import WeekNavigator from './WeekNavigator';
import WeeklyStats from './WeeklyStats';
import WeeklyGrid from './WeeklyGrid';
import EventDetailsModal from './EventDetailsModal';
import FilterPanel from './FilterPanel';
import EventCreatorModal from '@/components/ui/EventCreatorModal';

// Интерфейсы и константы
interface Event {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  day: number;
  category: string;
  color: string;
  description?: string;
  source: string;
  priority: string;
  _originalStart: Date;
  _originalEnd: Date;
}

const filterOptions = {
  categories: ['Работа', 'Личное', 'Встречи', 'Обучение'],
  sources: ['Google Calendar', 'Личный кабинет'],
  priorities: ['Высокий', 'Средний', 'Низкий'],
};

const getColorClass = (colorId: string | undefined): string => {
  const colorMap: Record<string, string> = {
    '1': 'bg-secondary',
    '2': 'bg-teal-500',
    '3': 'bg-purple-500',
    '4': 'bg-rose-500',
    '5': 'bg-yellow-500',
    '6': 'bg-orange-500',
    '7': 'bg-cyan-500',
    '8': 'bg-gray-500',
    '9': 'bg-blue-600',
    '10': 'bg-green-500',
    '11': 'bg-red-600',
  };
  return colorId ? colorMap[colorId] || 'bg-primary' : 'bg-primary';
};

// Функция для получения начальной даты из sessionStorage
const getInitialDate = (): Date => {
  // Проверяем, что мы в браузере, а не на сервере (для Next.js)
  if (typeof window !== 'undefined') {
    const savedDate = sessionStorage.getItem('currentScheduleWeek');
    // Если дата была сохранена, используем ее
    if (savedDate) {
      return new Date(savedDate);
    }
  }
  // В противном случае, возвращаем текущую дату
  return new Date();
};

const WeeklyScheduleInteractive = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  // Используем новую функцию для инициализации состояния
  const [currentWeek, setCurrentWeek] = useState<Date>(getInitialDate);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [activeFilters, setActiveFilters] = useState({
    categories: [] as string[],
    sources: [] as string[],
    priorities: [] as string[],
  });
  const [needsRefresh, setNeedsRefresh] = useState(0);

  // Состояния для модального окна создания события
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createModalInitialData, setCreateModalInitialData] = useState<{
    start_datetime?: string;
    end_datetime?: string;
  }>({});

  // Сохраняем дату в sessionStorage при каждом ее изменении
  useEffect(() => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('currentScheduleWeek', currentWeek.toISOString());
    }
  }, [currentWeek]);

  // Загрузка данных (теперь зависит от сохраненной недели)
  useEffect(() => {
    const fetchEventsForWeek = async () => {
      setIsLoading(true);
      const startOfWeek = new Date(currentWeek);
      const dayOfWeek = currentWeek.getDay();
      startOfWeek.setDate(currentWeek.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));
      startOfWeek.setHours(0, 0, 0, 0);
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      const startDate = startOfWeek.toISOString().split('T')[0];
      const endDate = endOfWeek.toISOString().split('T')[0];

      try {
        const response = await fetch(
          `http://localhost:8000/parse_calendar/events/?start_date=${startDate}&end_date=${endDate}`,
          { credentials: 'include' }
        );
        if (response.status === 401) throw new Error('Not authenticated. Please log in.');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const googleEvents = await response.json();
        if (!Array.isArray(googleEvents)) throw new Error('API response is not an array');

        const formattedEvents = googleEvents.map((gEvent: any): Event => {
          const originalStart = new Date(gEvent.start.dateTime || `${gEvent.start.date}T00:00:00`);
          const originalEnd = new Date(gEvent.end.dateTime || `${gEvent.end.date}T23:59:59`);
          const dayIndex = originalStart.getDay();
          const correctedDay = dayIndex === 0 ? 6 : dayIndex - 1;
          return {
            id: gEvent.id,
            title: gEvent.summary || 'Без названия',
            startTime: originalStart.toLocaleTimeString('ru-RU', {
              hour: '2-digit',
              minute: '2-digit',
            }),
            endTime: originalEnd.toLocaleTimeString('ru-RU', {
              hour: '2-digit',
              minute: '2-digit',
            }),
            day: correctedDay,
            category: gEvent.extendedProperties?.private?.category || 'Работа',
            color: getColorClass(gEvent.colorId),
            description: gEvent.description,
            source: 'Google Calendar',
            priority: gEvent.extendedProperties?.private?.priority || 'Средний',
            _originalStart: originalStart,
            _originalEnd: originalEnd,
          };
        });
        setEvents(formattedEvents);
      } catch (error) {
        console.error('Failed to fetch events:', error);
        setEvents([]);
      } finally {
        setIsLoading(false);
      }
    };
    fetchEventsForWeek();
  }, [currentWeek, needsRefresh]);

  const forceRefresh = () => setNeedsRefresh((count) => count + 1);

  // --- Функции управления событиями (CRUD) ---
  const handleEventDrop = useCallback(
    async (eventId: string, newDay: number, newStartTime: string) => {
      const eventToMove = events.find((e) => e.id === eventId);
      if (!eventToMove) return;

      const startOfWeek = new Date(currentWeek);
      const dayOfWeek = currentWeek.getDay();
      startOfWeek.setDate(currentWeek.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));

      const newStartDate = new Date(startOfWeek);
      newStartDate.setDate(startOfWeek.getDate() + newDay);
      const [hours, minutes] = newStartTime.split(':').map(Number);
      newStartDate.setHours(hours, minutes, 0, 0);

      const duration = eventToMove._originalEnd.getTime() - eventToMove._originalStart.getTime();
      const newEndDate = new Date(newStartDate.getTime() + duration);

      try {
        const response = await fetch(`http://localhost:8000/parse_calendar/events/${eventId}/`, {
          method: 'PATCH',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            start: newStartDate.toISOString(),
            end: newEndDate.toISOString(),
          }),
        });
        if (!response.ok) throw new Error('Failed to move event');
        forceRefresh();
      } catch (error) {
        console.error(error);
        alert('Не удалось переместить событие');
      }
    },
    [events, currentWeek]
  );

  const handleEventEdit = useCallback(async (event: Event) => {
    const newTitle = prompt('Введите новое название события:', event.title);
    if (!newTitle || newTitle === event.title) {
      setSelectedEvent(null);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/parse_calendar/events/${event.id}/`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ summary: newTitle }),
      });
      if (!response.ok) throw new Error('Failed to edit event');
      forceRefresh();
    } catch (error) {
      console.error(error);
      alert('Не удалось изменить событие');
    } finally {
      setSelectedEvent(null);
    }
  }, []);

  const handleEventDelete = useCallback(
    async (eventId: string) => {
      if (!confirm('Вы уверены, что хотите удалить это событие?')) return;

      const originalEvents = events;
      setEvents((prev) => prev.filter((e) => e.id !== eventId));
      setSelectedEvent(null);

      try {
        const response = await fetch(`http://localhost:8000/parse_calendar/events/${eventId}/`, {
          method: 'DELETE',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        });
        if (!response.ok && response.status !== 204) {
          throw new Error('Failed to delete event on server');
        }
      } catch (error) {
        console.error(error);
        alert('Не удалось удалить событие. Восстанавливаем данные...');
        setEvents(originalEvents);
      }
    },
    [events]
  );

  const handleTimeSlotClick = useCallback((day: number, hour: number) => {
    // Вычисляем дату для выбранного дня недели и часа
    const startOfWeek = new Date(currentWeek);
    const dayOfWeek = currentWeek.getDay();
    startOfWeek.setDate(currentWeek.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));
    
    const selectedDate = new Date(startOfWeek);
    selectedDate.setDate(startOfWeek.getDate() + day);
    selectedDate.setHours(hour, 0, 0, 0);
    
    const endDate = new Date(selectedDate);
    endDate.setHours(hour + 1, 0, 0, 0);

    setCreateModalInitialData({
      start_datetime: selectedDate.toISOString(),
      end_datetime: endDate.toISOString(),
    });
    setIsCreateModalOpen(true);
  }, [currentWeek]);

  const filteredEvents = useMemo(
    () =>
      events.filter(
        (event) =>
          (activeFilters.categories.length === 0 ||
            activeFilters.categories.includes(event.category)) &&
          (activeFilters.sources.length === 0 || activeFilters.sources.includes(event.source)) &&
          (activeFilters.priorities.length === 0 ||
            activeFilters.priorities.includes(event.priority))
      ),
    [events, activeFilters]
  );

  const stats = useMemo(() => {
    const totalMinutes = filteredEvents.reduce((acc, event) => {
      const duration = event._originalEnd.getTime() - event._originalStart.getTime();
      return acc + (duration > 0 ? duration / 60000 : 0);
    }, 0);
    const totalScheduledHours = Math.round((totalMinutes / 60) * 10) / 10;
    const busyDays = new Set(filteredEvents.map((e) => e.day)).size;
    return {
      totalScheduledHours,
      freeHours: 7 * 24 - totalScheduledHours,
      busyDays,
      averageHoursPerDay:
        busyDays > 0 ? parseFloat((totalScheduledHours / busyDays).toFixed(1)) : 0,
    };
  }, [filteredEvents]);

  if (isLoading && events.length === 0) {
    return (
      <div className="space-y-6">
        <div className="h-20 bg-card border border-border animate-pulse rounded-lg" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-card border border-border animate-pulse rounded-lg" />
          ))}
        </div>
        <div className="h-96 bg-card border border-border animate-pulse rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <WeekNavigator currentWeek={currentWeek} onWeekChange={setCurrentWeek} />
      <WeeklyStats stats={stats} />
      <FilterPanel
        filters={filterOptions}
        activeFilters={activeFilters}
        onFilterChange={(type, value) =>
          setActiveFilters((prev) => ({
            ...prev,
            [type]: prev[type as keyof typeof prev].includes(value)
              ? prev[type as keyof typeof prev].filter((f) => f !== value)
              : [...prev[type as keyof typeof prev], value],
          }))
        }
      />
      <WeeklyGrid
        events={filteredEvents}
        currentWeek={currentWeek}
        onEventClick={setSelectedEvent}
        onEventDrop={handleEventDrop}
        onTimeSlotClick={handleTimeSlotClick}
      />
      <EventDetailsModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        onEdit={handleEventEdit}
        onDelete={handleEventDelete}
      />

      {/* Модальное окно создания нового события */}
      <EventCreatorModal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setCreateModalInitialData({});
        }}
        initialData={createModalInitialData}
        onSuccess={(event) => {
          // Перезагружаем страницу для обновления событий
          window.location.reload();
        }}
      />
    </div>
  );
};

export default WeeklyScheduleInteractive;
