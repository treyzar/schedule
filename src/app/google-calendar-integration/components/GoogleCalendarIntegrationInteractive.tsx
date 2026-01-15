'use client';

import { useState, useEffect } from 'react';
import ConnectionStatus from './ConnectionStatus';
import CalendarList from './CalendarList';
import SyncSettings from './SyncSettings';
import AdvancedSettings from './AdvancedSettings';
import ConnectButton from './ConnectButton';

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
  const [isHydrated, setIsHydrated] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [lastSync, setLastSync] = useState('2 минуты назад');
  const [calendars, setCalendars] = useState<Calendar[]>([
    {
      id: '1',
      name: 'Рабочий календарь',
      color: '#3B82F6',
      eventCount: 24,
      isSelected: true,
    },
    {
      id: '2',
      name: 'Личные дела',
      color: '#10B981',
      eventCount: 15,
      isSelected: true,
    },
    {
      id: '3',
      name: 'Семейные события',
      color: '#F59E0B',
      eventCount: 8,
      isSelected: false,
    },
    {
      id: '4',
      name: 'Праздники в России',
      color: '#DC2626',
      eventCount: 12,
      isSelected: true,
    },
  ]);

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
  }, []);

  const handleConnect = () => {
    setTimeout(() => {
      setIsConnected(true);
      setLastSync('Только что');
    }, 1500);
  };

  const handleDisconnect = () => {
    setTimeout(() => {
      setIsConnected(false);
      setLastSync(undefined);
    }, 1000);
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

  if (!isHydrated) {
    return (
      <div className="space-y-6">
        <div className="h-32 bg-muted rounded-lg animate-pulse" />
        <div className="h-64 bg-muted rounded-lg animate-pulse" />
        <div className="h-96 bg-muted rounded-lg animate-pulse" />
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
        </>
      )}
    </div>
  );
};

export default GoogleCalendarIntegrationInteractive;
