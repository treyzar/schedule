'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

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

interface QuickTemplatesProps {
  onApplyTemplate: (template: Template) => void;
}

const QuickTemplates = ({ onApplyTemplate }: QuickTemplatesProps) => {
  const [isHydrated, setIsHydrated] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const templates: Template[] = [
    {
      id: 'productive-day',
      name: 'Продуктивный день',
      description: 'Оптимальное распределение рабочих задач с перерывами',
      icon: 'BoltIcon',
      events: [
        { title: 'Утренняя планёрка', startTime: '09:00', endTime: '09:30', category: 'meeting' },
        { title: 'Глубокая работа', startTime: '09:30', endTime: '11:30', category: 'work' },
        { title: 'Кофе-брейк', startTime: '11:30', endTime: '11:45', category: 'break' },
        { title: 'Работа над проектом', startTime: '11:45', endTime: '13:00', category: 'work' },
        { title: 'Обед', startTime: '13:00', endTime: '14:00', category: 'break' },
        {
          title: 'Встречи и коммуникация',
          startTime: '14:00',
          endTime: '16:00',
          category: 'meeting',
        },
        { title: 'Завершение задач', startTime: '16:00', endTime: '18:00', category: 'work' },
      ],
    },
    {
      id: 'balanced-day',
      name: 'Сбалансированный день',
      description: 'Баланс между работой и личными делами',
      icon: 'ScaleIcon',
      events: [
        { title: 'Утренняя зарядка', startTime: '07:00', endTime: '07:30', category: 'personal' },
        { title: 'Завтрак', startTime: '07:30', endTime: '08:00', category: 'break' },
        { title: 'Рабочие задачи', startTime: '09:00', endTime: '12:00', category: 'work' },
        { title: 'Обед', startTime: '12:00', endTime: '13:00', category: 'break' },
        { title: 'Встречи', startTime: '13:00', endTime: '15:00', category: 'meeting' },
        { title: 'Личные дела', startTime: '15:00', endTime: '17:00', category: 'personal' },
        { title: 'Вечерняя прогулка', startTime: '18:00', endTime: '19:00', category: 'personal' },
      ],
    },
    {
      id: 'meeting-heavy',
      name: 'День встреч',
      description: 'Расписание с множеством встреч и коротких рабочих блоков',
      icon: 'UsersIcon',
      events: [
        { title: 'Подготовка к встречам', startTime: '08:30', endTime: '09:00', category: 'work' },
        { title: 'Встреча с командой', startTime: '09:00', endTime: '10:00', category: 'meeting' },
        { title: 'Кофе-брейк', startTime: '10:00', endTime: '10:15', category: 'break' },
        { title: 'Встреча с клиентом', startTime: '10:15', endTime: '11:30', category: 'meeting' },
        { title: 'Обработка задач', startTime: '11:30', endTime: '12:30', category: 'work' },
        { title: 'Обед', startTime: '12:30', endTime: '13:30', category: 'break' },
        { title: 'Презентация проекта', startTime: '13:30', endTime: '15:00', category: 'meeting' },
        { title: 'Итоговая встреча', startTime: '15:30', endTime: '16:30', category: 'meeting' },
      ],
    },
    {
      id: 'focus-day',
      name: 'День концентрации',
      description: 'Минимум встреч, максимум глубокой работы',
      icon: 'FireIcon',
      events: [
        { title: 'Планирование дня', startTime: '08:00', endTime: '08:30', category: 'work' },
        {
          title: 'Глубокая работа - блок 1',
          startTime: '08:30',
          endTime: '11:00',
          category: 'work',
        },
        { title: 'Перерыв', startTime: '11:00', endTime: '11:15', category: 'break' },
        {
          title: 'Глубокая работа - блок 2',
          startTime: '11:15',
          endTime: '13:00',
          category: 'work',
        },
        { title: 'Обед', startTime: '13:00', endTime: '14:00', category: 'break' },
        {
          title: 'Глубокая работа - блок 3',
          startTime: '14:00',
          endTime: '16:30',
          category: 'work',
        },
        { title: 'Подведение итогов', startTime: '16:30', endTime: '17:00', category: 'work' },
      ],
    },
  ];

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-1/3" />
          <div className="grid grid-cols-2 gap-4">
            <div className="h-32 bg-muted rounded" />
            <div className="h-32 bg-muted rounded" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <div className="px-6 py-4 border-b border-border">
        <h3 className="text-lg font-heading font-semibold text-foreground">Быстрые шаблоны</h3>
        <p className="text-sm font-caption text-muted-foreground mt-1">
          Выберите готовый шаблон для быстрого заполнения расписания
        </p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {templates.map((template) => (
            <button
              key={template.id}
              onClick={() => {
                setSelectedTemplate(template.id);
                onApplyTemplate(template);
              }}
              className={`p-4 rounded-lg border-2 transition-smooth text-left hover:shadow-elevation-md ${
                selectedTemplate === template.id
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-muted-foreground'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Icon name={template.icon as any} size={24} className="text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-body font-semibold text-foreground mb-1">
                    {template.name}
                  </h4>
                  <p className="text-xs font-caption text-muted-foreground line-clamp-2">
                    {template.description}
                  </p>
                  <div className="flex items-center gap-2 mt-3">
                    <Icon name="ClockIcon" size={14} className="text-muted-foreground" />
                    <span className="text-xs font-caption text-muted-foreground">
                      {template.events.length} событий
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-6 p-4 rounded-lg bg-muted">
          <div className="flex items-start gap-3">
            <Icon
              name="InformationCircleIcon"
              size={20}
              className="text-primary flex-shrink-0 mt-0.5"
            />
            <div>
              <p className="text-sm font-body text-foreground">
                Применение шаблона заменит текущее расписание
              </p>
              <p className="text-xs font-caption text-muted-foreground mt-1">
                Вы можете отредактировать события после применения шаблона
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickTemplates;
