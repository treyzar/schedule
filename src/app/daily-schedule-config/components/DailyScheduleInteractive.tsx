'use client';

import { useState, useEffect } from 'react';

// Предполагается, что эти компоненты существуют и импортированы.
// Если их нет, вы можете временно закомментировать импорты и
// заменить вызовы компонентов на простые <div> для теста.
import TimelineGrid from './TimelineGrid';
import EventDetailsModal from './EventDetailsModal';
import DayConfigPanel from './DayConfigPanel';
import ScheduleStats from './ScheduleStats';
import QuickTemplates from './QuickTemplates';
import Icon from '@/components/ui/AppIcon';

// --- Интерфейсы для типизации данных ---

interface ScheduleEvent {
  id: string;
  title: string;
  startTime: string; // Ожидается в формате HH:mm
  endTime: string; // Ожидается в формате HH:mm
  category: 'work' | 'personal' | 'break' | 'meeting';
  color: string;
  description?: string;
}

interface DayConfig {
  workHoursStart: string;
  workHoursEnd: string;
  breakDuration: number;
  priorityTasks: number;
  autoOptimize: boolean;
}

interface Template {
  id: string;
  name: string;
  description: string;
  icon: string;
  events: Array<{
    title: string;
    startTime: string;
    endTime: string;
    category: 'work' | 'personal' | 'break' | 'meeting';
  }>;
}

// --- Основной компонент ---

const DailyScheduleInteractive = () => {
  // --- Состояния компонента ---
  const [isHydrated, setIsHydrated] = useState(false);
  const [events, setEvents] = useState<ScheduleEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ScheduleEvent | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [dayConfig, setDayConfig] = useState<DayConfig>({
    workHoursStart: '09:00',
    workHoursEnd: '18:00',
    breakDuration: 30,
    priorityTasks: 3,
    autoOptimize: true,
  });

  useEffect(() => {
    setIsHydrated(true);

    const fetchInitialData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // --- ИЗМЕНЯЕМ URL ЗАПРОСА ---
        const response = await fetch('http://localhost:8001/parse_calendar/initial-data/', {
          credentials: 'include',
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `Ошибка сервера: ${response.status}`);
        }

        const data = await response.json();
        const fetchedEvents = data.calendar_events || []; // <-- Получаем события из объекта

        // ... (код форматирования событий остается тем же) ...
        const formattedEvents = fetchedEvents.map((event: any) => ({
          id: event.id,
          title: event.summary || 'Без названия',
          startTime: new Date(event.start.dateTime || event.start.date).toLocaleTimeString(
            'ru-RU',
            {
              hour: '2-digit',
              minute: '2-digit',
            }
          ),
          endTime: new Date(event.end.dateTime || event.end.date).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit',
          }),
          description: event.description || '',
          category: 'meeting',
          color: '#F59E0B',
        }));

        setEvents(formattedEvents);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    // Логика с ?auth=success больше не нужна, т.к. бэкенд делает всю работу.
    // Просто запускаем fetch при загрузке.
    fetchInitialData();
  }, []);

  // --- Обработчики действий пользователя ---

  const handleEventClick = (event: ScheduleEvent) => {
    setSelectedEvent(event);
    setIsModalOpen(true);
  };

  const handleTimeSlotClick = (hour: number, minute: number) => {
    const newEvent: ScheduleEvent = {
      id: `new-${Date.now()}`,
      title: 'Новое событие',
      startTime: `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
      endTime: `${(hour + 1).toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
      category: 'work',
      color: '#2D5A87',
      description: '',
    };
    setSelectedEvent(newEvent);
    setIsModalOpen(true);
  };

  const handleSaveEvent = (eventToSave: ScheduleEvent) => {
    const existingIndex = events.findIndex((e) => e.id === eventToSave.id);

    if (existingIndex >= 0) {
      // --- Обновление существующего события ---
      const updatedEvents = [...events]; // Создаем копию массива для иммутабельности
      updatedEvents[existingIndex] = eventToSave;
      setEvents(updatedEvents);
    } else {
      // --- Добавление нового события ---
      // Если у события временный ID, генерируем постоянный (в реальном приложении это делает бэкенд)
      const finalEvent = eventToSave.id.startsWith('new-')
        ? { ...eventToSave, id: `evt-${Date.now()}` }
        : eventToSave;
      setEvents([...events, finalEvent]);
    }
  };

  const handleDeleteEvent = (eventId: string) => {
    if (window.confirm('Вы уверены, что хотите удалить это событие?')) {
      // Фильтруем массив, возвращая новый массив без удаленного элемента
      setEvents(events.filter((e) => e.id !== eventId));
    }
  };

  const handleApplyTemplate = (template: Template) => {
    const templateEvents: ScheduleEvent[] = template.events.map((event, index) => ({
      id: `template-${Date.now()}-${index}`,
      title: event.title,
      startTime: event.startTime,
      endTime: event.endTime,
      category: event.category,
      color:
        event.category === 'work'
          ? '#2D5A87'
          : event.category === 'personal'
            ? '#4A7C59'
            : event.category === 'break'
              ? '#D97706'
              : '#F59E0B',
      description: `Событие из шаблона "${template.name}"`,
    }));
    // Полностью заменяем текущие события на события из шаблона
    setEvents(templateEvents);
  };

  // --- Логика отображения в зависимости от состояния ---

  const renderTimelineContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-96">
          <Icon name="LoaderCircle" size={32} className="animate-spin text-primary" />
          <p className="ml-4 text-muted-foreground">Загрузка событий...</p>
        </div>
      );
    }
    if (error) {
      const isAuthError = error.toLowerCase().includes('authenticated');
      return (
        <div className="p-6 text-center bg-red-50 border border-red-200 rounded-lg">
          <p className="font-semibold text-red-700">Произошла ошибка</p>
          <p className="text-red-600 mt-1">{error}</p>
          {error && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">
                Пожалуйста, войдите в ваш Google аккаунт, чтобы продолжить.
              </p>
              <a href="http://localhost:8000/parse_calendar/authorize/">
                <button className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg">
                  Войти через Google
                </button>
              </a>
            </div>
          )}
        </div>
      );
    }
    return (
      <TimelineGrid
        events={events}
        onEventClick={handleEventClick}
        onTimeSlotClick={handleTimeSlotClick}
      />
    );
  };

  if (!isHydrated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <Icon name="ClockIcon" size={48} className="text-primary animate-pulse" />
          <p className="text-lg font-body text-muted-foreground">Загрузка расписания...</p>
        </div>
      </div>
    );
  }

  // --- Основная JSX-разметка компонента ---
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold text-foreground">Дневное расписание</h1>
          <p className="text-sm font-caption text-muted-foreground mt-2">Вторник, 13 января 2026</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => console.log('Previous day')}
            className="p-2 rounded-md hover:bg-muted transition-smooth"
            title="Предыдущий день"
          >
            <Icon name="ChevronLeftIcon" size={20} className="text-muted-foreground" />
          </button>
          <button
            onClick={() => console.log('Today')}
            className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:shadow-elevation-md transition-smooth"
          >
            <span className="text-sm font-body font-medium">Сегодня</span>
          </button>
          <button
            onClick={() => console.log('Next day')}
            className="p-2 rounded-md hover:bg-muted transition-smooth"
            title="Следующий день"
          >
            <Icon name="ChevronRightIcon" size={20} className="text-muted-foreground" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">{renderTimelineContent()}</div>
        <div className="space-y-6">
          <ScheduleStats events={events} />
          <DayConfigPanel config={dayConfig} onConfigChange={setDayConfig} />
          <QuickTemplates onApplyTemplate={handleApplyTemplate} />
        </div>
      </div>

      <EventDetailsModal
        event={selectedEvent}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedEvent(null);
        }}
        onSave={handleSaveEvent}
        onDelete={handleDeleteEvent}
      />
    </div>
  );
};

export default DailyScheduleInteractive;
