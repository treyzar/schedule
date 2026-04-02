'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface IntegrationStatus {
  name: string;
  status: 'connected' | 'syncing' | 'error' | 'disconnected';
  lastSync?: string;
  icon: string;
}

const StatusIndicator = () => {
  const [showDetails, setShowDetails] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([]);

  // Загружаем реальный статус интеграций с бэкенда
  useEffect(() => {
    const fetchIntegrationStatus = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('http://localhost:8000/parse_calendar/status/', {
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          setIntegrations([
            {
              name: 'Google Calendar',
              status: data.is_authenticated ? 'connected' : 'disconnected',
              lastSync: data.last_sync || undefined,
              icon: 'CalendarIcon',
            },
          ]);
        } else {
          // Если ошибка - показываем как отключено
          setIntegrations([
            {
              name: 'Google Calendar',
              status: 'disconnected',
              icon: 'CalendarIcon',
            },
          ]);
        }
      } catch (error) {
        console.error('Failed to fetch integration status:', error);
        setIntegrations([
          {
            name: 'Google Calendar',
            status: 'error',
            icon: 'CalendarIcon',
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchIntegrationStatus();
  }, []);

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

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/parse_calendar/logout/', {
        method: 'POST',
        credentials: 'include',
      });
      // Обновляем статус после выхода
      setIntegrations(prev => prev.map(i => ({ ...i, status: 'disconnected' as const })));
      setShowDetails(false);
    } catch (error) {
      console.error('Failed to logout:', error);
    }
  };

  const handleConnect = () => {
    window.location.href = 'http://localhost:8000/parse_calendar/authorize/';
  };

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
            <div className="p-3 border-t border-border space-y-2">
              {integrations.some(i => i.status === 'connected') ? (
                <>
                  <button
                    onClick={() => {
                      setShowDetails(false);
                      window.location.href = '/daily-schedule-config';
                    }}
                    className="w-full px-4 py-2 text-sm font-body text-primary hover:bg-muted rounded-md transition-smooth"
                  >
                    Открыть календарь
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-2 text-sm font-body text-error hover:bg-error/10 rounded-md transition-smooth"
                  >
                    Отключить
                  </button>
                </>
              ) : (
                <button
                  onClick={handleConnect}
                  className="w-full px-4 py-2 text-sm font-body text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-smooth"
                >
                  Подключить
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StatusIndicator;
