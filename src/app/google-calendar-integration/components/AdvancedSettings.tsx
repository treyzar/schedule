'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface AdvancedSettingsData {
  timezone: string;
  recurringEvents: boolean;
  notifications: boolean;
  eventFiltering: string;
}

interface AdvancedSettingsProps {
  settings: AdvancedSettingsData;
  onSettingsChange: (settings: AdvancedSettingsData) => void;
}

const AdvancedSettings = ({ settings, onSettingsChange }: AdvancedSettingsProps) => {
  const [isHydrated, setIsHydrated] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [localSettings, setLocalSettings] = useState(settings);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleChange = (key: keyof AdvancedSettingsData, value: any) => {
    const updated = { ...localSettings, [key]: value };
    setLocalSettings(updated);
    onSettingsChange(updated);
  };

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-sm">
        <div className="h-6 bg-muted rounded w-48 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border shadow-elevation-sm overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-6 hover:bg-muted transition-smooth"
      >
        <div className="flex items-center gap-3">
          <Icon name="Cog6ToothIcon" size={24} className="text-muted-foreground" />
          <h3 className="text-lg font-heading font-semibold text-foreground">
            Расширенные настройки
          </h3>
        </div>
        <Icon
          name="ChevronDownIcon"
          size={20}
          className={`text-muted-foreground transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {isExpanded && (
        <div className="px-6 pb-6 space-y-4 border-t border-border pt-4">
          <div>
            <label className="block text-sm font-body font-medium text-foreground mb-2">
              Часовой пояс
            </label>
            <select
              value={localSettings.timezone}
              onChange={(e) => handleChange('timezone', e.target.value)}
              className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
            >
              <option value="Europe/Moscow">Москва (UTC+3)</option>
              <option value="Europe/Samara">Самара (UTC+4)</option>
              <option value="Asia/Yekaterinburg">Екатеринбург (UTC+5)</option>
              <option value="Asia/Novosibirsk">Новосибирск (UTC+7)</option>
              <option value="Asia/Vladivostok">Владивосток (UTC+10)</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-3 rounded-md border border-border">
            <div className="flex items-center gap-3">
              <Icon name="ArrowPathIcon" size={20} className="text-muted-foreground" />
              <div>
                <p className="text-sm font-body font-medium text-foreground">
                  Повторяющиеся события
                </p>
                <p className="text-xs text-muted-foreground">Синхронизировать серии событий</p>
              </div>
            </div>
            <button
              onClick={() => handleChange('recurringEvents', !localSettings.recurringEvents)}
              className={`relative w-12 h-6 rounded-full transition-smooth ${
                localSettings.recurringEvents ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <span
                className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  localSettings.recurringEvents ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-md border border-border">
            <div className="flex items-center gap-3">
              <Icon name="BellIcon" size={20} className="text-muted-foreground" />
              <div>
                <p className="text-sm font-body font-medium text-foreground">
                  Уведомления о синхронизации
                </p>
                <p className="text-xs text-muted-foreground">Получать уведомления об обновлениях</p>
              </div>
            </div>
            <button
              onClick={() => handleChange('notifications', !localSettings.notifications)}
              className={`relative w-12 h-6 rounded-full transition-smooth ${
                localSettings.notifications ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <span
                className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  localSettings.notifications ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          <div>
            <label className="block text-sm font-body font-medium text-foreground mb-2">
              Фильтрация событий
            </label>
            <select
              value={localSettings.eventFiltering}
              onChange={(e) => handleChange('eventFiltering', e.target.value)}
              className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
            >
              <option value="all">Все события</option>
              <option value="confirmed">Только подтвержденные</option>
              <option value="future">Только будущие события</option>
              <option value="custom">Пользовательский фильтр</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedSettings;
