'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface ConnectionStatusProps {
  isConnected: boolean;
  lastSync?: string;
  onReconnect: () => void;
}

const ConnectionStatus = ({ isConnected, lastSync, onReconnect }: ConnectionStatusProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) {
    return (
      <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-muted animate-pulse" />
          <div className="flex-1">
            <div className="h-5 bg-muted rounded w-32 mb-2 animate-pulse" />
            <div className="h-4 bg-muted rounded w-48 animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-sm">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`flex items-center justify-center w-12 h-12 rounded-full ${
              isConnected ? 'bg-success/10' : 'bg-error/10'
            }`}
          >
            <Icon
              name={isConnected ? 'CheckCircleIcon' : 'XCircleIcon'}
              size={28}
              className={isConnected ? 'text-success' : 'text-error'}
            />
          </div>
          <div>
            <h3 className="text-lg font-heading font-semibold text-foreground">
              {isConnected ? 'Подключено' : 'Не подключено'}
            </h3>
            <p className="text-sm text-muted-foreground">
              {isConnected && lastSync
                ? `Последняя синхронизация: ${lastSync}`
                : 'Google Calendar не подключен'}
            </p>
          </div>
        </div>
        {!isConnected && (
          <button
            onClick={onReconnect}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:shadow-elevation-md transition-smooth"
          >
            <Icon name="ArrowPathIcon" size={20} />
            <span className="text-sm font-body font-medium">Переподключить</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default ConnectionStatus;
