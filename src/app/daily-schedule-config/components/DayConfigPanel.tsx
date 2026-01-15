'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface DayConfig {
  workHoursStart: string;
  workHoursEnd: string;
  breakDuration: number;
  priorityTasks: number;
  autoOptimize: boolean;
}

interface DayConfigPanelProps {
  config: DayConfig;
  onConfigChange: (config: DayConfig) => void;
}

const DayConfigPanel = ({ config, onConfigChange }: DayConfigPanelProps) => {
  const [isHydrated, setIsHydrated] = useState(false);
  const [localConfig, setLocalConfig] = useState<DayConfig>(config);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-1/3" />
          <div className="h-10 bg-muted rounded" />
          <div className="h-10 bg-muted rounded" />
        </div>
      </div>
    );
  }

  const handleApply = () => {
    onConfigChange(localConfig);
    setIsExpanded(false);
  };

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-muted transition-smooth"
      >
        <div className="flex items-center gap-3">
          <Icon name="Cog6ToothIcon" size={24} className="text-primary" />
          <h3 className="text-lg font-heading font-semibold text-foreground">Настройки дня</h3>
        </div>
        <Icon
          name={isExpanded ? 'ChevronUpIcon' : 'ChevronDownIcon'}
          size={20}
          className="text-muted-foreground"
        />
      </button>

      {isExpanded && (
        <div className="px-6 pb-6 space-y-6 border-t border-border pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-body font-medium text-foreground mb-2">
                Начало рабочего дня
              </label>
              <input
                type="time"
                value={localConfig.workHoursStart}
                onChange={(e) => setLocalConfig({ ...localConfig, workHoursStart: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
              />
            </div>

            <div>
              <label className="block text-sm font-body font-medium text-foreground mb-2">
                Конец рабочего дня
              </label>
              <input
                type="time"
                value={localConfig.workHoursEnd}
                onChange={(e) => setLocalConfig({ ...localConfig, workHoursEnd: e.target.value })}
                className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-smooth"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-body font-medium text-foreground mb-2">
              Длительность перерывов (минуты)
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="15"
                max="60"
                step="15"
                value={localConfig.breakDuration}
                onChange={(e) =>
                  setLocalConfig({ ...localConfig, breakDuration: Number(e.target.value) })
                }
                className="flex-1"
              />
              <span className="text-sm font-data text-foreground font-medium w-16 text-right">
                {localConfig.breakDuration} мин
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-body font-medium text-foreground mb-2">
              Приоритетные задачи в день
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={localConfig.priorityTasks}
                onChange={(e) =>
                  setLocalConfig({ ...localConfig, priorityTasks: Number(e.target.value) })
                }
                className="flex-1"
              />
              <span className="text-sm font-data text-foreground font-medium w-16 text-right">
                {localConfig.priorityTasks}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-muted">
            <div className="flex items-center gap-3">
              <Icon name="BoltIcon" size={20} className="text-accent" />
              <div>
                <p className="text-sm font-body font-medium text-foreground">
                  Автоматическая оптимизация
                </p>
                <p className="text-xs font-caption text-muted-foreground mt-1">
                  AI будет автоматически оптимизировать расписание
                </p>
              </div>
            </div>
            <button
              onClick={() =>
                setLocalConfig({ ...localConfig, autoOptimize: !localConfig.autoOptimize })
              }
              className={`relative w-12 h-6 rounded-full transition-smooth ${
                localConfig.autoOptimize ? 'bg-primary' : 'bg-border'
              }`}
            >
              <span
                className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                  localConfig.autoOptimize ? 'translate-x-6' : ''
                }`}
              />
            </button>
          </div>

          <div className="flex items-center gap-3 pt-4 border-t border-border">
            <button
              onClick={() => {
                setLocalConfig(config);
                setIsExpanded(false);
              }}
              className="flex-1 px-6 py-3 rounded-lg border border-border hover:bg-muted transition-smooth"
            >
              <span className="text-sm font-body font-medium text-foreground">Отмена</span>
            </button>
            <button
              onClick={handleApply}
              className="flex-1 px-6 py-3 rounded-lg bg-primary text-primary-foreground hover:shadow-elevation-md transition-smooth"
            >
              <span className="text-sm font-body font-medium">Применить</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DayConfigPanel;
