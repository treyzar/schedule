'use client';

import { useState } from 'react';
import Icon from '@/components/ui/AppIcon';

interface IntegrationStatus {
  name: string;
  status: 'connected' | 'syncing' | 'error' | 'disconnected';
  lastSync?: string;
  icon: string;
}

const StatusIndicator = () => {
  const [showDetails, setShowDetails] = useState(false);
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([
    {
      name: 'Google Calendar',
      status: 'connected',
      lastSync: '2 минуты назад',
      icon: 'CalendarIcon',
    },
    {
      name: 'Парсинг личного кабинета',
      status: 'syncing',
      lastSync: 'Синхронизация...',
      icon: 'ArrowPathIcon',
    },
  ]);

  const getStatusColor = (status: IntegrationStatus['status']) => {
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

  const getStatusIcon = (status: IntegrationStatus['status']) => {
    switch (status) {
      case 'connected':
        return 'CheckCircleIcon';
      case 'syncing':
        return 'ArrowPathIcon';
      case 'error':
        return 'ExclamationCircleIcon';
      case 'disconnected':
        return 'XCircleIcon';
      default:
        return 'QuestionMarkCircleIcon';
    }
  };

  const overallStatus = integrations.some((i) => i.status === 'error')
    ? 'error'
    : integrations.some((i) => i.status === 'syncing')
      ? 'syncing'
      : integrations.every((i) => i.status === 'connected')
        ? 'connected'
        : 'disconnected';

  return (
    <div className="relative">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-smooth"
        title="Статус интеграций"
      >
        <Icon
          name={getStatusIcon(overallStatus)}
          size={20}
          className={`${getStatusColor(overallStatus)} ${
            overallStatus === 'syncing' ? 'animate-spin' : ''
          }`}
        />
        <span className="hidden lg:inline text-sm font-caption text-muted-foreground">Статус</span>
      </button>

      {showDetails && (
        <>
          <div className="fixed inset-0 z-[150]" onClick={() => setShowDetails(false)} />
          <div className="absolute right-0 top-full mt-2 w-80 bg-popover border border-border rounded-lg shadow-elevation-lg z-[200] overflow-hidden">
            <div className="p-4 border-b border-border">
              <h3 className="text-sm font-heading font-semibold text-foreground">
                Статус интеграций
              </h3>
            </div>
            <div className="p-2">
              {integrations.map((integration) => (
                <div
                  key={integration.name}
                  className="flex items-center gap-3 p-3 rounded-md hover:bg-muted transition-smooth"
                >
                  <Icon
                    name={integration.icon as any}
                    size={20}
                    className="text-muted-foreground flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-body text-foreground truncate">{integration.name}</p>
                    <p className="text-xs font-caption text-muted-foreground">
                      {integration.lastSync}
                    </p>
                  </div>
                  <Icon
                    name={getStatusIcon(integration.status)}
                    size={20}
                    className={`${getStatusColor(integration.status)} flex-shrink-0 ${
                      integration.status === 'syncing' ? 'animate-spin' : ''
                    }`}
                  />
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-border">
              <button
                onClick={() => {
                  setShowDetails(false);
                }}
                className="w-full px-4 py-2 text-sm font-body text-primary hover:bg-muted rounded-md transition-smooth"
              >
                Управление интеграциями
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StatusIndicator;
