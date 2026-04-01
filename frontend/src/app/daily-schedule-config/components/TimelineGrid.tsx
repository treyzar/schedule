'use client';

import { useState, useEffect, useMemo } from 'react';
import Icon from '@/components/ui/AppIcon';

// --- ИНТЕРФЕЙСЫ ---
// Интерфейс для данных, приходящих в компонент
interface ScheduleEvent {
  id: string;
  title: string;
  startTime: string; // Ожидается формат "HH:mm"
  endTime: string;
  category: 'work' | 'personal' | 'break' | 'meeting';
  color: string;
  description?: string;
}

// Новый интерфейс для события с рассчитанными CSS-свойствами
interface LayoutEvent extends ScheduleEvent {
  top: number; // в px
  height: number; // в px
  left: number; // в %
  width: number; // в %
  zIndex: number;
}

// Интерфейс для временных слотов
interface TimeSlot {
  hour: number;
  minute: number;
  label: string;
}

// Интерфейс для props компонента
interface TimelineGridProps {
  events: ScheduleEvent[];
  onEventClick: (event: ScheduleEvent) => void;
  onTimeSlotClick: (hour: number, minute: number) => void;
}

// --- ОСНОВНОЙ КОМПОНЕНТ ---
const TimelineGrid = ({ events, onEventClick, onTimeSlotClick }: TimelineGridProps) => {
  // --- Состояния компонента ---
  const [isHydrated, setIsHydrated] = useState(false);
  const [draggedEvent, setDraggedEvent] = useState<string | null>(null);

  // --- Константы и подготовка данных ---
  // Генерируем слоты времени для отображения сетки
  const timeSlots: TimeSlot[] = useMemo(() => {
    const slots: TimeSlot[] = [];
    for (let hour = 6; hour <= 23; hour++) {
      slots.push({ hour, minute: 0, label: `${hour.toString().padStart(2, '0')}:00` });
      slots.push({ hour, minute: 30, label: `${hour.toString().padStart(2, '0')}:30` });
    }
    return slots;
  }, []);

  const SLOT_HEIGHT_PX = 60; // Высота одного 30-минутного слота в пикселях

  // --- ГЛАВНЫЙ АЛГОРИТМ РАСЧЕТА МАКЕТА ---
  // useMemo кэширует результат, и пересчет происходит только при изменении 'events'
  const layoutEvents: LayoutEvent[] = useMemo(() => {
    if (!events || events.length === 0) return [];

    const timeToMinutes = (time: string): number => {
      const [hours, minutes] = time.split(':').map(Number);
      return hours * 60 + minutes;
    };

    // 1. Конвертируем время в минуты и сортируем события
    const sortedEvents = [...events]
      .map((event) => ({
        ...event,
        startMinutes: timeToMinutes(event.startTime),
        endMinutes: timeToMinutes(event.endTime),
      }))
      // Сортируем по началу, а при равенстве - по убыванию длительности, чтобы длинные события были левее
      .sort((a, b) => a.startMinutes - b.startMinutes || b.endMinutes - a.endMinutes);

    // 2. Группируем пересекающиеся события
    const eventGroups: (typeof sortedEvents)[][] = [];
    if (sortedEvents.length > 0) {
      // Начинаем первую группу с первого события
      eventGroups.push([sortedEvents[0]]);
      for (let i = 1; i < sortedEvents.length; i++) {
        const currentEvent = sortedEvents[i];
        const lastGroup = eventGroups[eventGroups.length - 1];

        // Находим максимальное время окончания в текущей группе
        const maxEndTimeInGroup = Math.max(...lastGroup.map((e) => e.endMinutes));

        // Если текущее событие начинается раньше, чем закончится группа, оно пересекается
        if (currentEvent.startMinutes < maxEndTimeInGroup) {
          lastGroup.push(currentEvent);
        } else {
          // Иначе начинаем новую группу
          eventGroups.push([currentEvent]);
        }
      }
    }

    // 3. Рассчитываем layout для каждой группы
    const newLayoutEvents: LayoutEvent[] = [];
    eventGroups.forEach((group) => {
      const columns: (typeof group)[][] = [];
      // Сортируем события внутри группы по времени начала для правильного распределения
      group.sort((a, b) => a.startMinutes - b.startMinutes);

      group.forEach((event) => {
        let placed = false;
        // Ищем первую доступную колонку
        for (const col of columns) {
          const lastEventInColumn = col[col.length - 1];
          if (event.startMinutes >= lastEventInColumn.endMinutes) {
            col.push(event);
            placed = true;
            break;
          }
        }
        // Если не нашли свободного места, создаем новую колонку
        if (!placed) {
          columns.push([event]);
        }
      });

      const numColumns = columns.length;
      columns.forEach((col, colIndex) => {
        col.forEach((event) => {
          // Рассчитываем позицию и размеры в пикселях
          const top = ((event.startMinutes - 6 * 60) / 30) * SLOT_HEIGHT_PX;
          const height = ((event.endMinutes - event.startMinutes) / 30) * SLOT_HEIGHT_PX;

          newLayoutEvents.push({
            ...event,
            top,
            height,
            left: (colIndex / numColumns) * 100, // Позиция в %
            width: (1 / numColumns) * 100, // Ширина в %
            zIndex: 10 + colIndex, // Чтобы события левее были "выше"
          });
        });
      });
    });

    return newLayoutEvents;
  }, [events]); // Зависимость - массив "сырых" событий

  // --- Вспомогательные функции (без изменений) ---
  useEffect(() => {
    setIsHydrated(true);
  }, []);
  const getCategoryColor = (category: ScheduleEvent['category']) => {
    switch (category) {
      case 'work':
        return 'bg-primary/20 border-primary text-primary';
      case 'personal':
        return 'bg-secondary/20 border-secondary text-secondary';
      case 'break':
        return 'bg-accent/20 border-accent text-accent';
      case 'meeting':
        return 'bg-warning/20 border-warning text-warning';
      default:
        return 'bg-muted border-border text-foreground';
    }
  };
  const handleDragStart = (eventId: string) => {
    if (isHydrated) setDraggedEvent(eventId);
  };
  const handleDragEnd = () => {
    if (isHydrated) setDraggedEvent(null);
  };

  // --- Прелоадер на время гидратации ---
  if (!isHydrated) {
    return (
      <div className="relative bg-card rounded-lg border border-border overflow-hidden">
        <div className="h-[1080px] flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <Icon name="ClockIcon" size={48} className="text-muted-foreground animate-pulse" />
            <p className="text-sm text-muted-foreground">Загрузка расписания...</p>
          </div>
        </div>
      </div>
    );
  }

  // --- JSX-РАЗМЕТКА КОМПОНЕНТА ---
  return (
    <div className="relative bg-card rounded-lg border border-border overflow-hidden">
      <div className="sticky top-0 z-20 bg-card/80 backdrop-blur-sm border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-heading font-semibold text-foreground">Временная шкала</h3>
          {/* ... (кнопки зума) ... */}
        </div>
      </div>

      <div className="relative">
        {/* Рендер временных слотов (сетки) */}
        {timeSlots.map((slot) => (
          <div
            key={`${slot.hour}-${slot.minute}`}
            className="flex border-b border-border hover:bg-muted/30 transition-smooth cursor-pointer"
            style={{ height: `${SLOT_HEIGHT_PX}px` }}
            onClick={() => onTimeSlotClick(slot.hour, slot.minute)}
          >
            <div className="w-20 flex-shrink-0 px-4 py-2 border-r border-border">
              <span className="text-xs font-caption text-muted-foreground">{slot.label}</span>
            </div>
            {/* Разделитель для получасовых слотов */}
            <div className="flex-1 relative">
              {slot.minute === 0 && <div className="absolute inset-x-0 top-0 h-px bg-border/50" />}
            </div>
          </div>
        ))}

        {/* Рендер событий поверх сетки */}
        <div className="absolute inset-0 left-20 pointer-events-none">
          {layoutEvents.map((event) => (
            <div
              key={event.id}
              className={`absolute p-3 pointer-events-auto cursor-move transition-all duration-200 hover:shadow-elevation-md rounded-lg border-l-4 ${getCategoryColor(event.category)} ${draggedEvent === event.id ? 'opacity-50 scale-95' : ''}`}
              style={{
                top: `${event.top}px`,
                height: `${event.height}px`,
                left: `calc(${event.left}% + 4px)`,
                width: `calc(${event.width}% - 8px)`,
                zIndex: event.zIndex,
              }}
              draggable
              onDragStart={() => handleDragStart(event.id)}
              onDragEnd={handleDragEnd}
              onClick={(e) => {
                e.stopPropagation();
                onEventClick(event);
              }}
            >
              <div className="flex items-start justify-between gap-2 h-full flex-col">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-body font-medium truncate">{event.title}</p>
                </div>
                <p className="text-xs font-caption opacity-80 mt-1">
                  {event.startTime} - {event.endTime}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TimelineGrid;
