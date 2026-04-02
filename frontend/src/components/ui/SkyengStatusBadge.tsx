'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface SkyengStatus {
  is_authenticated: boolean;
  connection_status: 'connected' | 'expired' | 'disconnected';
  email: string | null;
  token_expired: boolean;
  last_sync: string | null;
  requires_auth: boolean;
}

interface SkyengStatusBadgeProps {
  showDetails?: boolean;
  onStatusChange?: (status: SkyengStatus) => void;
  className?: string;
}

export default function SkyengStatusBadge({ 
  showDetails = false, 
  onStatusChange,
  className = '' 
}: SkyengStatusBadgeProps) {
  const [status, setStatus] = useState<SkyengStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/parse_calendar/skyeng-status/', {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        onStatusChange?.(data);
      }
    } catch (err) {
      console.error('Failed to fetch Skyeng status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/parse_calendar/skyeng-logout/', {
        method: 'POST',
        credentials: 'include',
      });
      await fetchStatus();
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  if (isLoading) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <Icon name="ArrowPathIcon" size={16} className="animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Загрузка...</span>
      </div>
    );
  }

  if (!status) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <Icon name="NoSymbolIcon" size={16} className="text-error" />
        <span className="text-sm text-error">Ошибка</span>
      </div>
    );
  }

  // Конфигурация для разных статусов
  const statusConfig = {
    connected: {
      icon: 'CheckCircleIcon',
      label: 'Подключено',
      color: 'text-success',
      bgColor: 'bg-success/10',
      borderColor: 'border-success/30',
    },
    expired: {
      icon: 'ExclamationTriangleIcon',
      label: 'Токен истёк',
      color: 'text-amber-600',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/30',
    },
    disconnected: {
      icon: 'NoSymbolIcon',
      label: 'Не подключено',
      color: 'text-error',
      bgColor: 'bg-error/10',
      borderColor: 'border-error/30',
    },
  };

  const config = statusConfig[status.connection_status];

  // Краткий бейдж
  if (!showDetails) {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border ${config.bgColor} ${config.borderColor}`}>
        <Icon name={config.icon} size={14} className={config.color} />
        <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
      </div>
    );
  }

  // Развёрнутая версия с деталями
  return (
    <div className={`bg-card border border-border rounded-xl p-4 ${className}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${config.bgColor} flex items-center justify-center`}>
            <Icon name={config.icon} size={24} className={config.color} />
          </div>
          <div>
            <h3 className="font-heading font-semibold text-foreground">Skyeng</h3>
            <p className={`text-sm ${config.color}`}>{config.label}</p>
          </div>
        </div>
        
        {status.is_authenticated && (
          <button
            onClick={handleLogout}
            className="p-2 hover:bg-muted/50 rounded-lg transition-colors"
            title="Выйти"
          >
            <Icon name="ArrowRightOnRectangleIcon" size={18} className="text-muted-foreground" />
          </button>
        )}
      </div>

      {status.email && (
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Icon name="EnvelopeIcon" size={14} />
            <span className="truncate">{status.email}</span>
          </div>
          
          {status.last_sync && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Icon name="ClockIcon" size={14} />
              <span>Синхронизация: {status.last_sync}</span>
            </div>
          )}
        </div>
      )}

      {status.requires_auth && (
        <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <div className="flex items-start gap-2">
            <Icon name="ExclamationCircleIcon" size={16} className="text-amber-600 mt-0.5" />
            <p className="text-xs text-amber-600">
              Необходимо авторизоваться в Skyeng для продолжения работы
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
