'use client';

import { useState } from 'react';
import Icon from '@/components/ui/AppIcon';

interface CalendarSource {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'syncing' | 'error' | 'disconnected';
  lastSync: string;
  eventsCount: number;
  enabled: boolean;
  icon: string;
  healthScore: number;
}

interface SourceCardProps {
  source: CalendarSource;
  onToggle: (id: string, enabled: boolean) => void;
  onSync: (id: string) => void;
  onConfigure: (id: string) => void;
}

export default function SourceCard({ source, onToggle, onSync, onConfigure }: SourceCardProps) {
  const [isHydrated, setIsHydrated] = useState(false);

  useState(() => {
    setIsHydrated(true);
  });

  const getStatusColor = (status: CalendarSource['status']) => {
    switch (status) {
      case 'connected':
        return 'text-success';
      case 'syncing':
        return 'text-warning';
      case 'error':
        return 'text-error';
      case 'disconnected':
        return 'text-muted-foreground';
      default:
        return 'text-muted-foreground';
    }
  };

  const getStatusText = (status: CalendarSource['status']) => {
    switch (status) {
      case 'connected':
        return 'Подключено';
      case 'syncing':
        return 'Синхронизация';
      case 'error':
        return 'Ошибка';
      case 'disconnected':
        return 'Отключено';
      default:
        return 'Неизвестно';
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'bg-success';
    if (score >= 50) return 'bg-warning';
    return 'bg-error';
  };

  if (!isHydrated) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-elevation-sm">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-muted" />
            <div>
              <div className="h-5 w-32 bg-muted rounded mb-2" />
              <div className="h-4 w-24 bg-muted rounded" />
            </div>
          </div>
          <div className="w-12 h-6 bg-muted rounded-full" />
        </div>
        <div className="space-y-3">
          <div className="h-4 w-full bg-muted rounded" />
          <div className="h-4 w-3/4 bg-muted rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-elevation-sm hover:shadow-elevation-md transition-smooth">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
            <Icon name={source.icon as any} size={24} className="text-primary" />
          </div>
          <div>
            <h3 className="text-base font-heading font-semibold text-foreground">{source.name}</h3>
            <p className="text-sm font-caption text-muted-foreground">{source.type}</p>
          </div>
        </div>
        <button
          onClick={() => onToggle(source.id, !source.enabled)}
          className={`
            relative w-12 h-6 rounded-full transition-smooth
            ${source.enabled ? 'bg-primary' : 'bg-muted'}
          `}
          aria-label={source.enabled ? 'Отключить источник' : 'Включить источник'}
        >
          <span
            className={`
              absolute top-1 w-4 h-4 rounded-full bg-white shadow-elevation-sm transition-smooth
              ${source.enabled ? 'left-7' : 'left-1'}
            `}
          />
        </button>
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-body text-muted-foreground">Статус:</span>
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${getStatusColor(source.status)}`}>
              {getStatusText(source.status)}
            </span>
            {source.status === 'syncing' && (
              <Icon name="ArrowPathIcon" size={16} className="text-warning animate-spin" />
            )}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-body text-muted-foreground">Последняя синхронизация:</span>
          <span className="text-sm font-body text-foreground">{source.lastSync}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-body text-muted-foreground">Событий обработано:</span>
          <span className="text-sm font-body text-foreground font-medium">
            {source.eventsCount}
          </span>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-body text-muted-foreground">Качество данных:</span>
            <span className="text-sm font-body text-foreground font-medium">
              {source.healthScore}%
            </span>
          </div>
          <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full ${getHealthColor(source.healthScore)} transition-smooth`}
              style={{ width: `${source.healthScore}%` }}
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onSync(source.id)}
          disabled={source.status === 'syncing' || !source.enabled}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:shadow-elevation-md transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Icon name="ArrowPathIcon" size={18} />
          <span className="text-sm font-body font-medium">Синхронизировать</span>
        </button>
        <button
          onClick={() => onConfigure(source.id)}
          className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-smooth"
          aria-label="Настроить источник"
        >
          <Icon name="Cog6ToothIcon" size={18} className="text-muted-foreground" />
        </button>
      </div>
    </div>
  );
}
