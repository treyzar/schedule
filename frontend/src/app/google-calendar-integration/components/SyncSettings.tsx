'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface SyncSettingsData {
  syncInterval: string;
  bidirectionalSync: boolean;
  conflictResolution: string;
  autoSync: boolean;
}

interface SyncSettingsProps {
  settings: SyncSettingsData;
  onSettingsChange: (settings: SyncSettingsData) => void;
}

const SyncSettings = ({ settings, onSettingsChange }: SyncSettingsProps) => {
  const [isHydrated, setIsHydrated] = useState(false);
  const [localSettings, setLocalSettings] = useState(settings);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleChange = (key: keyof SyncSettingsData, value: any) => {
    const updated = { ...localSettings, [key]: value };
    setLocalSettings(updated);
    onSettingsChange(updated);
  };

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-sm">
        <div className="h-6 bg-muted rounded w-48 mb-4 animate-pulse" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 bg-muted rounded w-32 animate-pulse" />
              <div className="h-10 bg-muted rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-sm">
      <h3 className="text-lg font-heading font-semibold text-foreground mb-4">
        Настройки синхронизации
      </h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-body font-medium text-foreground mb-2">
            Интервал синхронизации
          </label>
          <select
            value={localSettings.syncInterval}
            onChange={(e) => handleChange('syncInterval', e.target.value)}
            className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
          >
            <option value="5min">Каждые 5 минут</option>
            <option value="15min">Каждые 15 минут</option>
            <option value="30min">Каждые 30 минут</option>
            <option value="1hour">Каждый час</option>
            <option value="manual">Вручную</option>
          </select>
        </div>

        <div className="flex items-center justify-between p-3 rounded-md border border-border">
          <div className="flex items-center gap-3">
            <Icon name="ArrowsRightLeftIcon" size={20} className="text-muted-foreground" />
            <div>
              <p className="text-sm font-body font-medium text-foreground">
                Двусторонняя синхронизация
              </p>
              <p className="text-xs text-muted-foreground">
                Изменения синхронизируются в обе стороны
              </p>
            </div>
          </div>
          <button
            onClick={() => handleChange('bidirectionalSync', !localSettings.bidirectionalSync)}
            className={`relative w-12 h-6 rounded-full transition-smooth ${
              localSettings.bidirectionalSync ? 'bg-primary' : 'bg-muted'
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                localSettings.bidirectionalSync ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        <div>
          <label className="block text-sm font-body font-medium text-foreground mb-2">
            Разрешение конфликтов
          </label>
          <select
            value={localSettings.conflictResolution}
            onChange={(e) => handleChange('conflictResolution', e.target.value)}
            className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
          >
            <option value="local">Приоритет локальным изменениям</option>
            <option value="remote">Приоритет Google Calendar</option>
            <option value="newest">Приоритет новейшим изменениям</option>
            <option value="manual">Запрашивать вручную</option>
          </select>
        </div>

        <div className="flex items-center justify-between p-3 rounded-md border border-border">
          <div className="flex items-center gap-3">
            <Icon name="BoltIcon" size={20} className="text-muted-foreground" />
            <div>
              <p className="text-sm font-body font-medium text-foreground">
                Автоматическая синхронизация
              </p>
              <p className="text-xs text-muted-foreground">Синхронизировать при изменениях</p>
            </div>
          </div>
          <button
            onClick={() => handleChange('autoSync', !localSettings.autoSync)}
            className={`relative w-12 h-6 rounded-full transition-smooth ${
              localSettings.autoSync ? 'bg-primary' : 'bg-muted'
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                localSettings.autoSync ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SyncSettings;
