'use client';

import { useState } from 'react';
import Icon from '@/components/ui/AppIcon';

interface SourceType {
  id: string;
  name: string;
  description: string;
  icon: string;
  requiresAuth: boolean;
}

interface AddSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (sourceType: string) => void;
}

export default function AddSourceModal({ isOpen, onClose, onAdd }: AddSourceModalProps) {
  const [isHydrated, setIsHydrated] = useState(false);
  const [selectedSource, setSelectedSource] = useState<string>('');

  useState(() => {
    setIsHydrated(true);
  });

  const sourceTypes: SourceType[] = [
    {
      id: 'google-calendar',
      name: 'Google Calendar',
      description: 'Синхронизация с Google Calendar через OAuth 2.0',
      icon: 'CalendarIcon',
      requiresAuth: true,
    },
    {
      id: 'outlook-calendar',
      name: 'Outlook Calendar',
      description: 'Интеграция с Microsoft Outlook Calendar',
      icon: 'CalendarDaysIcon',
      requiresAuth: true,
    },
    {
      id: 'ical-feed',
      name: 'iCal Feed',
      description: 'Подключение календаря через iCal URL',
      icon: 'LinkIcon',
      requiresAuth: false,
    },
    {
      id: 'university-portal',
      name: 'Портал университета',
      description: 'Парсинг расписания из личного кабинета университета',
      icon: 'AcademicCapIcon',
      requiresAuth: true,
    },
  ];

  const handleAdd = () => {
    if (selectedSource) {
      onAdd(selectedSource);
      setSelectedSource('');
      onClose();
    }
  };

  if (!isOpen || !isHydrated) return null;

  return (
    <>
      <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[200]" onClick={onClose} />
      <div className="fixed inset-0 z-[201] flex items-center justify-center p-4">
        <div className="bg-card border border-border rounded-lg shadow-elevation-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-xl font-heading font-semibold text-foreground">
              Добавить источник календаря
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-muted transition-smooth"
              aria-label="Закрыть"
            >
              <Icon name="XMarkIcon" size={24} className="text-muted-foreground" />
            </button>
          </div>

          <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sourceTypes.map((source) => (
                <button
                  key={source.id}
                  onClick={() => setSelectedSource(source.id)}
                  className={`
                    p-4 border rounded-lg text-left transition-smooth
                    hover:shadow-elevation-md
                    ${
                      selectedSource === source.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50'
                    }
                  `}
                >
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Icon name={source.icon as any} size={20} className="text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-body font-semibold text-foreground mb-1">
                        {source.name}
                      </h3>
                      <p className="text-xs font-caption text-muted-foreground">
                        {source.description}
                      </p>
                    </div>
                  </div>
                  {source.requiresAuth && (
                    <div className="flex items-center gap-2 text-xs font-caption text-muted-foreground">
                      <Icon name="LockClosedIcon" size={14} />
                      <span>Требуется авторизация</span>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 p-6 border-t border-border">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-smooth text-sm font-body text-foreground"
            >
              Отмена
            </button>
            <button
              onClick={handleAdd}
              disabled={!selectedSource}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:shadow-elevation-md transition-smooth disabled:opacity-50 disabled:cursor-not-allowed text-sm font-body font-medium"
            >
              Добавить источник
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
