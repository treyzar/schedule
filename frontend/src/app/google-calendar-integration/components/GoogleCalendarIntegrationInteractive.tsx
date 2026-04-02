'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import ConnectionStatus from './ConnectionStatus';
import CalendarList from './CalendarList';
import SyncSettings from './SyncSettings';
import AdvancedSettings from './AdvancedSettings';
import ConnectButton from './ConnectButton';
import GoogleEventCreator from './GoogleEventCreator';
import Icon from '@/components/ui/AppIcon';

interface Calendar {
  id: string;
  name: string;
  color: string;
  eventCount: number;
  isSelected: boolean;
}

interface SyncSettingsData {
  syncInterval: string;
  bidirectionalSync: boolean;
  conflictResolution: string;
  autoSync: boolean;
}

interface AdvancedSettingsData {
  timezone: string;
  recurringEvents: boolean;
  notifications: boolean;
  eventFiltering: string;
}

const GoogleCalendarIntegrationInteractive = () => {
  const { is_authenticated, isLoading } = useAuth();
  const [isHydrated, setIsHydrated] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [calendars, setCalendars] = useState<Calendar[]>([]);
  const [isLoadingCalendars, setIsLoadingCalendars] = useState(true);

  const [syncSettings, setSyncSettings] = useState<SyncSettingsData>({
    syncInterval: '15min',
    bidirectionalSync: true,
    conflictResolution: 'newest',
    autoSync: true,
  });

  const [advancedSettings, setAdvancedSettings] = useState<AdvancedSettingsData>({
    timezone: 'Europe/Moscow',
    recurringEvents: true,
    notifications: true,
    eventFiltering: 'all',
  });

  useEffect(() => {
    setIsHydrated(true);
    
    // Загружаем статус авторизации и календари
    const loadCalendars = async () => {
      try {
        setIsLoadingCalendars(true);
        const statusResponse = await fetch('http://localhost:8000/parse_calendar/status/', {
          credentials: 'include',
        });
        
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setIsConnected(statusData.is_authenticated);
          setLastSync(statusData.last_sync);
          
          // Если подключены, загружаем календари
          if (statusData.is_authenticated) {
            // Загружаем события для получения информации о календарях
            const now = new Date();
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
            const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
            
            const eventsResponse = await fetch(
              `http://localhost:8000/parse_calendar/events/?start_date=${firstDay.toISOString().split('T')[0]}&end_date=${lastDay.toISOString().split('T')[0]}`,
              { credentials: 'include' }
            );
            
            if (eventsResponse.ok) {
              const events = await eventsResponse.json();
              // Группируем события по календарям (в реальном API нужно получить список календарей отдельно)
              setCalendars([
                {
                  id: 'primary',
                  name: 'Мой календарь',
                  color: '#3B82F6',
                  eventCount: events.length || 0,
                  isSelected: true,
                }
              ]);
            }
          }
        }
      } catch (error) {
        console.error('Failed to load calendars:', error);
      } finally {
        setIsLoadingCalendars(false);
      }
    };
    
    loadCalendars();
  }, []);

  const handleConnect = () => {
    // Перенаправляем на авторизацию
    window.location.href = 'http://localhost:8000/parse_calendar/authorize/';
  };

  const handleDisconnect = async () => {
    try {
      await fetch('http://localhost:8000/parse_calendar/logout/', {
        method: 'POST',
        credentials: 'include',
      });
      setIsConnected(false);
      setLastSync(null);
      setCalendars([]);
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
  };

  const handleReconnect = () => {
    handleConnect();
  };

  const handleCalendarSelection = (calendarId: string, isSelected: boolean) => {
    setCalendars((prev) =>
      prev.map((cal) => (cal.id === calendarId ? { ...cal, isSelected } : cal))
    );
  };

  const handleSyncSettingsChange = (settings: SyncSettingsData) => {
    setSyncSettings(settings);
  };

  const handleAdvancedSettingsChange = (settings: AdvancedSettingsData) => {
    setAdvancedSettings(settings);
  };

  if (!isHydrated || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Icon name="ArrowPathIcon" size={48} className="animate-spin text-primary mx-auto mb-4" />
          <p className="text-lg font-body text-foreground">Загрузка календарей...</p>
        </div>
      </div>
    );
  }

  if (!is_authenticated) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center max-w-md">
          <Icon name="ExclamationTriangleIcon" size={64} className="text-warning mx-auto mb-4" />
          <h2 className="text-xl font-heading font-semibold text-foreground mb-2">
            Требуется авторизация
          </h2>
          <p className="text-muted-foreground mb-6">
            Пожалуйста, авторизуйтесь через Google для доступа к настройкам календаря
          </p>
          <button
            onClick={handleConnect}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-smooth"
          >
            Авторизоваться
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ConnectionStatus
        isConnected={isConnected}
        lastSync={lastSync}
        onReconnect={handleReconnect}
      />

      {!isConnected && (
        <ConnectButton
          isConnected={isConnected}
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
        />
      )}

      {isConnected && (
        <>
          <CalendarList calendars={calendars} onSelectionChange={handleCalendarSelection} />

          <SyncSettings settings={syncSettings} onSettingsChange={handleSyncSettingsChange} />

          <AdvancedSettings
            settings={advancedSettings}
            onSettingsChange={handleAdvancedSettingsChange}
          />

          <ConnectButton
            isConnected={isConnected}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
          />

          {/* === Создание событий === */}
          <div className="pt-6 border-t border-border">
            <GoogleEventCreator />
          </div>
        </>
      )}
    </div>
  );
};

export default GoogleCalendarIntegrationInteractive;
