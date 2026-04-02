'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Icon from '@/components/ui/AppIcon';
import ChatMessage from './ChatMessage';
import QuickActionChips from './QuickActionChips';
import ContextSidebar, { CalendarEvent, TimeSlot, TimeStatistics } from './ContextSidebar';
import MessageInput from './MessageInput';
import TypingIndicator from './TypingIndicator';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: string;
  status?: 'sending' | 'sent' | 'error';
}

const API_BASE_URL = 'http://localhost:8000';

const AIChatInteractive = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnecting, setIsConnecting] = useState(true);
  const [isReceiving, setIsReceiving] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  // Реальные данные из календаря
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [freeTimeSlots, setFreeTimeSlots] = useState<TimeSlot[]>([]);
  const [statistics, setStatistics] = useState<TimeStatistics | null>(null);
  const [isLoadingContext, setIsLoadingContext] = useState(true);

  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isReceiving]);

  // Загрузка данных календаря для контекста
  const loadCalendarContext = useCallback(async () => {
    try {
      setIsLoadingContext(true);
      
      // Загружаем события за последние 7 дней и следующие 7 дней
      const now = new Date();
      const startDate = new Date(now);
      startDate.setDate(now.getDate() - 7);
      const endDate = new Date(now);
      endDate.setDate(now.getDate() + 7);

      const response = await fetch(
        `${API_BASE_URL}/parse_calendar/events/?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`,
        { credentials: 'include' }
      );

      if (response.ok) {
        const events = await response.json();
        setCalendarEvents(events || []);

        // Вычисляем свободные слоты
        const slots = calculateFreeTimeSlots(events || [], now);
        setFreeTimeSlots(slots);

        // Вычисляем статистику
        const stats = calculateStatistics(events || [], now);
        setStatistics(stats);
      }
    } catch (error) {
      console.error('Failed to load calendar context:', error);
    } finally {
      setIsLoadingContext(false);
    }
  }, []);

  // Вычисление свободных слотов (упрощённая версия)
  const calculateFreeTimeSlots = (events: CalendarEvent[], now: Date): TimeSlot[] => {
    const slots: TimeSlot[] = [];
    const daysToCheck = 7;

    for (let i = 0; i < daysToCheck; i++) {
      const date = new Date(now);
      date.setDate(now.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];

      // События на этот день
      const dayEvents = events.filter(event => {
        const eventDate = event.start.dateTime?.split('T')[0] || event.start.date;
        return eventDate === dateStr;
      });

      // Рабочие часы с 9:00 до 18:00
      const workStart = 9;
      const workEnd = 18;

      // Собираем занятые интервалы
      const busyIntervals = dayEvents.map(event => {
        const start = new Date(event.start.dateTime || event.start.date!);
        const end = new Date(event.end.dateTime || event.end.date!);
        return {
          start: start.getHours() * 60 + start.getMinutes(),
          end: end.getHours() * 60 + end.getMinutes(),
        };
      });

      busyIntervals.sort((a, b) => a.start - b.start);

      // Находим свободные слоты
      let currentTime = workStart * 60;
      for (const interval of busyIntervals) {
        if (interval.start > currentTime && interval.start < workEnd * 60) {
          slots.push({
            id: `${dateStr}-${currentTime}`,
            date: date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }),
            startTime: `${Math.floor(currentTime / 60).toString().padStart(2, '0')}:${(currentTime % 60).toString().padStart(2, '0')}`,
            endTime: `${Math.floor(interval.start / 60).toString().padStart(2, '0')}:${(interval.start % 60).toString().padStart(2, '0')}`,
            durationMinutes: interval.start - currentTime,
          });
        }
        currentTime = Math.max(currentTime, interval.end);
      }

      // Последний слот после всех событий
      if (currentTime < workEnd * 60) {
        slots.push({
          id: `${dateStr}-${currentTime}-end`,
          date: date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }),
          startTime: `${Math.floor(currentTime / 60).toString().padStart(2, '0')}:${(currentTime % 60).toString().padStart(2, '0')}`,
          endTime: `${workEnd}:00`,
          durationMinutes: workEnd * 60 - currentTime,
        });
      }
    }

    return slots;
  };

  // Обнаружение конфликтов в расписании
  const detectConflicts = (events: CalendarEvent[]): Array<{
    event1: CalendarEvent;
    event2: CalendarEvent;
    overlapMinutes: number;
  }> => {
    const conflicts: Array<{
      event1: CalendarEvent;
      event2: CalendarEvent;
      overlapMinutes: number;
    }> = [];

    for (let i = 0; i < events.length; i++) {
      for (let j = i + 1; j < events.length; j++) {
        const event1 = events[i];
        const event2 = events[j];

        const start1 = new Date(event1.start.dateTime || event1.start.date!);
        const end1 = new Date(event1.end.dateTime || event1.end.date!);
        const start2 = new Date(event2.start.dateTime || event2.start.date!);
        const end2 = new Date(event2.end.dateTime || event2.end.date!);

        // Проверяем пересечение
        const overlapStart = new Date(Math.max(start1.getTime(), start2.getTime()));
        const overlapEnd = new Date(Math.min(end1.getTime(), end2.getTime()));

        if (overlapStart < overlapEnd) {
          const overlapMinutes = (overlapEnd.getTime() - overlapStart.getTime()) / 1000 / 60;
          conflicts.push({
            event1,
            event2,
            overlapMinutes,
          });
        }
      }
    }

    return conflicts;
  };

  // Вычисление статистики
  const calculateStatistics = (events: CalendarEvent[], now: Date): TimeStatistics => {
    const weekStart = new Date(now);
    const dayOfWeek = now.getDay();
    weekStart.setDate(now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));
    weekStart.setHours(0, 0, 0, 0);

    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    weekEnd.setHours(23, 59, 59, 999);

    const weekEvents = events.filter(event => {
      const eventDate = new Date(event.start.dateTime || event.start.date!);
      return eventDate >= weekStart && eventDate <= weekEnd;
    });

    let totalMeetings = 0;
    let totalTasks = 0;
    let totalDuration = 0;
    const dayCounts: Record<number, number> = {};

    weekEvents.forEach(event => {
      const category = event.extendedProperties?.private?.category?.toLowerCase() || '';
      const start = new Date(event.start.dateTime || event.start.date!);
      const end = new Date(event.end.dateTime || event.end.date!);
      const duration = (end.getTime() - start.getTime()) / 1000 / 60; // минуты

      totalDuration += duration;
      const dayIndex = start.getDay();
      dayCounts[dayIndex] = (dayCounts[dayIndex] || 0) + duration;

      if (category.includes('встреча') || category.includes('meeting') || category.includes('работа')) {
        totalMeetings++;
      } else if (category.includes('задача') || category.includes('task')) {
        totalTasks++;
      }
    });

    const busiestDayIndex = Object.entries(dayCounts).reduce((a, b) => 
      dayCounts[Number(a[0])] > dayCounts[Number(b[0])] ? a : b
    , ['0', 0])[0];

    const dayNames = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    const averageDayLength = totalDuration / 7 / 60; // часы

    // Свободное время = рабочие часы в неделю (40ч) - занятое время
    const workWeekMinutes = 40 * 60;
    const totalFreeTime = Math.max(0, workWeekMinutes - totalDuration);

    return {
      totalMeetings,
      totalTasks,
      totalFreeTime,
      busiestDay: dayNames[parseInt(busiestDayIndex)],
      averageDayLength: Math.round(averageDayLength * 10) / 10,
    };
  };

  useEffect(() => {
    loadCalendarContext();
  }, [loadCalendarContext]);

  useEffect(() => {
    const wsUrl = 'ws://localhost:8000/ws/ai/chat/';
    const socket = new WebSocket(wsUrl);
    ws.current = socket;

    socket.onopen = () => {
      setIsConnecting(false);
    };

    socket.onclose = () => {
      setIsConnecting(true);
      setIsReceiving(false);
    };
    socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setIsConnecting(true);
      setIsReceiving(false);
    };

    socket.onmessage = (event) => {
      console.log('Received final message from WS:', event.data.full_response);

      setIsReceiving(false);

      try {
        const data = JSON.parse(event.data);

        const aiMessage: Message = {
          id: Date.now().toString(),
          type: 'ai',
          content: data.full_response || `Ошибка: получен некорректный ответ от сервера.`,
          timestamp: new Date().toISOString(),
          status: data.error ? 'error' : 'sent',
        };

        setMessages((prev) => [...prev, aiMessage]);
      } catch (e) {
        console.error('Failed to parse final WebSocket message:', e);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            type: 'ai',
            content: `Ошибка: получен некорректный ответ от сервера.`,
            timestamp: new Date().toISOString(),
            status: 'error',
          },
        ]);
      }
    };

    return () => {
      if (socket.readyState === 1) {
        socket.close();
      }
    };
  }, []);

  const handleSendMessage = useCallback(
    (content: string) => {
      if (!content.trim() || isReceiving || isConnecting) return;

      if (ws.current?.readyState === WebSocket.OPEN) {
        const userMessage: Message = {
          id: Date.now().toString(),
          type: 'user',
          content,
          timestamp: new Date().toISOString(),
          status: 'sent',
        };
        setMessages((prev) => [...prev, userMessage]);
        
        // Добавляем контекст о расписании к сообщению
        const conflicts = detectConflicts(calendarEvents);
        const contextMessage = {
          message: content,
          context: {
            eventsCount: calendarEvents.length,
            conflictsCount: conflicts.length,
            hasStatistics: !!statistics,
          }
        };
        
        ws.current.send(JSON.stringify(contextMessage));
        setIsReceiving(true);
      } else {
        alert('Соединение с AI-сервисом не установлено. Попробуйте обновить страницу.');
      }
    },
    [isConnecting, isReceiving, calendarEvents, statistics]
  );

  const handleClearChat = useCallback(() => {
    setMessages([]);
    // Очищаем историю на сервере через WebSocket
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action: 'clear_history' }));
    }
  }, []);

  const handleExportChat = useCallback(() => {
    const chatText = messages.map(msg => 
      `[${new Date(msg.timestamp).toLocaleString('ru-RU')}] ${msg.type === 'user' ? 'Вы' : 'AI'}: ${msg.content}`
    ).join('\n\n');

    const blob = new Blob([chatText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [messages]);

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between p-4 border-b border-border bg-card">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center ${isConnecting ? 'bg-muted' : 'bg-primary'}`}
            >
              <Icon name="SparklesIcon" size={20} className="text-primary-foreground" />
            </div>
            <div>
              <h2 className="text-sm font-heading font-semibold text-foreground">AI Помощник</h2>
              <p
                className={`text-xs font-caption flex items-center gap-1 ${isConnecting ? 'text-warning' : 'text-success'}`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${isConnecting ? 'bg-warning' : 'bg-success'} ${!isConnecting && !isReceiving ? '' : 'animate-pulse'}`}
                />
                {isConnecting ? 'Подключение...' : isReceiving ? 'Генерация ответа...' : 'Онлайн'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportChat}
              disabled={messages.length === 0}
              className="p-2 rounded-md hover:bg-muted transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
              title="Экспорт чата"
              aria-label="Экспорт чата"
            >
              <Icon name="ArrowDownTrayIcon" size={20} />
            </button>
            <button
              onClick={handleClearChat}
              disabled={messages.length === 0}
              className="p-2 rounded-md hover:bg-muted transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
              title="Очистить чат"
              aria-label="Очистить чат"
            >
              <Icon name="TrashIcon" size={20} />
            </button>
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="lg:hidden p-2 rounded-md hover:bg-muted transition-smooth"
              aria-label="Открыть контекст"
            >
              <Icon name="InformationCircleIcon" size={20} />
            </button>
          </div>
        </div>

        <div
          className="flex-1 overflow-y-auto p-4 space-y-4"
          style={{ maxHeight: 'calc(100vh - 280px)' }}
        >
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <Icon name="SparklesIcon" size={40} className="text-primary" />
              </div>
              <h3 className="text-lg font-heading font-semibold text-foreground mb-2">
                AI Помощник по расписанию
              </h3>
              <p className="text-sm font-body text-muted-foreground max-w-md mb-6">
                Я могу помочь вам найти свободное время, проанализировать расписание, 
                обнаружить конфликты и оптимизировать использование времени.
              </p>
              <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
                <button
                  onClick={() => handleSendMessage('Найди свободное время на этой неделе для встречи на 1 час')}
                  className="p-3 rounded-lg border border-border bg-card hover:border-primary transition-smooth text-left"
                >
                  <Icon name="MagnifyingGlassIcon" size={20} className="text-primary mb-2" />
                  <p className="text-xs font-body font-medium">Найти время</p>
                  <p className="text-xs font-caption text-muted-foreground mt-1">Для встречи</p>
                </button>
                <button
                  onClick={() => handleSendMessage('Покажи все конфликты в моем расписании')}
                  className="p-3 rounded-lg border border-border bg-card hover:border-primary transition-smooth text-left"
                >
                  <Icon name="ExclamationTriangleIcon" size={20} className="text-warning mb-2" />
                  <p className="text-xs font-body font-medium">Конфликты</p>
                  <p className="text-xs font-caption text-muted-foreground mt-1">В расписании</p>
                </button>
                <button
                  onClick={() => handleSendMessage('Оптимизируй мое расписание на сегодня')}
                  className="p-3 rounded-lg border border-border bg-card hover:border-primary transition-smooth text-left"
                >
                  <Icon name="BoltIcon" size={20} className="text-success mb-2" />
                  <p className="text-xs font-body font-medium">Оптимизация</p>
                  <p className="text-xs font-caption text-muted-foreground mt-1">На сегодня</p>
                </button>
                <button
                  onClick={() => handleSendMessage('Покажи статистику использования времени за неделю')}
                  className="p-3 rounded-lg border border-border bg-card hover:border-primary transition-smooth text-left"
                >
                  <Icon name="ChartBarIcon" size={20} className="text-info mb-2" />
                  <p className="text-xs font-body font-medium">Статистика</p>
                  <p className="text-xs font-caption text-muted-foreground mt-1">За неделю</p>
                </button>
              </div>
            </div>
          )}
          
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isReceiving && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        <QuickActionChips onChipClick={handleSendMessage} />
        <MessageInput onSendMessage={handleSendMessage} disabled={isConnecting || isReceiving} />
      </div>
      
      <ContextSidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)}
        events={calendarEvents}
        freeSlots={freeTimeSlots}
        statistics={statistics}
        isLoading={isLoadingContext}
      />
    </div>
  );
};

export default AIChatInteractive;
