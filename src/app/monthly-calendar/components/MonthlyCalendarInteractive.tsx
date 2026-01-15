'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import MonthlyCalendarGrid from './MonthlyCalendarGrid';
import MonthNavigation from './MonthNavigation';
import MonthlyStatsSidebar from './MonthlyStatsSidebar';
import EventDetailsModal from './EventDetailsModal';
import MiniCalendar from './MiniCalendar';

// Интерфейс для событий, используется во всех дочерних компонентах
interface CalendarEvent {
  id: string;
  title: string;
  date: string; // YYYY-MM-DD
  time: string; // HH:mm
  category: 'work' | 'personal' | 'meeting' | 'deadline';
  priority: 'high' | 'medium' | 'low';
  description?: string;
  location?: string;
}

const MonthlyCalendarInteractive = () => {
  const router = useRouter();
  const [currentDate, setCurrentDate] = useState(new Date(2026, 0, 13)); // Устанавливаем текущую дату
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [needsRefresh, setNeedsRefresh] = useState(0);

  // --- ЗАГРУЗКА ДАННЫХ С БЭКЕНДА ---
  useEffect(() => {
    const fetchEventsForMonth = async () => {
      setIsLoading(true);

      // Рассчитываем первую и последнюю дату месяца
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const firstDay = new Date(year, month, 1);
      const lastDay = new Date(year, month + 1, 0);

      const startDate = firstDay.toISOString().split('T')[0];
      const endDate = lastDay.toISOString().split('T')[0];

      try {
        const response = await fetch(
          `http://localhost:8000/parse_calendar/events/?start_date=${startDate}&end_date=${endDate}`,
          {
            credentials: 'include', // <--- ОБЯЗАТЕЛЬНО для отправки cookie сессии
          }
        );

        if (response.status === 401) throw new Error('Not authenticated.');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const googleEvents = await response.json();
        if (!Array.isArray(googleEvents)) throw new Error('API response is not an array');

        // Трансформируем ответ от Google в наш формат CalendarEvent
        const formattedEvents: CalendarEvent[] = googleEvents.map((gEvent: any) => {
          const originalStart = new Date(gEvent.start.dateTime || `${gEvent.start.date}T00:00:00`);

          return {
            id: gEvent.id,
            title: gEvent.summary || 'Без названия',
            date: originalStart.toISOString().split('T')[0], // YYYY-MM-DD
            time: originalStart.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
            category: gEvent.extendedProperties?.private?.category || 'work',
            priority: gEvent.extendedProperties?.private?.priority || 'medium',
            description: gEvent.description,
            location: gEvent.location,
          };
        });

        setEvents(formattedEvents);
      } catch (error) {
        console.error('Failed to fetch monthly events:', error);
        setEvents([]); // Очищаем события в случае ошибки
      } finally {
        setIsLoading(false);
      }
    };

    fetchEventsForMonth();
  }, [currentDate, needsRefresh]); // Перезагружаем при смене месяца или принудительно

  // --- Обработчики навигации и действий ---

  const handlePreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const handleTodayClick = () => {
    setCurrentDate(new Date()); // Переходим на реальный сегодняшний день
  };

  const handleYearChange = (year: number) => {
    setCurrentDate(new Date(year, currentDate.getMonth(), 1));
  };

  const handleDateClick = (date: Date) => {
    // Здесь можно реализовать переход на дневное/недельное расписание для этой даты
    // Например, передав дату в URL
    router.push(`/daily-schedule-config?date=${date.toISOString().split('T')[0]}`);
  };

  const handleEventClick = (event: CalendarEvent) => {
    setSelectedEvent(event);
  };

  // --- Рендер компонента ---

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <div>
          {/* Скелетон для навигации и сетки */}
          <div className="h-12 mb-6 bg-card border border-border rounded-lg animate-pulse"></div>
          <div className="h-[600px] bg-card border border-border rounded-lg animate-pulse"></div>
        </div>
        <div className="hidden lg:block space-y-6">
          {/* Скелетон для сайдбара */}
          <div className="h-48 bg-card border border-border rounded-lg animate-pulse"></div>
          <div className="h-64 bg-card border border-border rounded-lg animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <div>
          <MonthNavigation
            currentDate={currentDate}
            onPreviousMonth={handlePreviousMonth}
            onNextMonth={handleNextMonth}
            onTodayClick={handleTodayClick}
            onYearChange={handleYearChange}
          />

          <MonthlyCalendarGrid
            currentDate={currentDate}
            events={events} // <-- Передаем реальные события
            onDateClick={handleDateClick}
            onEventClick={handleEventClick}
          />

          <div className="mt-6 lg:hidden">
            <MiniCalendar currentDate={currentDate} onMonthSelect={setCurrentDate} />
          </div>
        </div>

        <div className="space-y-6">
          <div className="hidden lg:block">
            <MiniCalendar currentDate={currentDate} onMonthSelect={setCurrentDate} />
          </div>

          <MonthlyStatsSidebar events={events} currentDate={currentDate} />
        </div>
      </div>

      <EventDetailsModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </>
  );
};

export default MonthlyCalendarInteractive;
