'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface ConnectButtonProps {
  isConnected: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

const ConnectButton = ({ isConnected, onConnect, onDisconnect }: ConnectButtonProps) => {
  const [isHydrated, setIsHydrated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const handleClick = async () => {
    setIsLoading(true);
    try {
      if (isConnected) {
        await onDisconnect();
      } else {
        await onConnect();
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!isHydrated) {
    return <div className="h-12 bg-muted rounded-lg animate-pulse" />;
  }

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`
        w-full flex items-center justify-center gap-3 px-6 py-3 rounded-lg font-body font-medium transition-smooth
        ${
          isConnected
            ? 'bg-error text-error-foreground hover:shadow-elevation-md'
            : 'bg-primary text-primary-foreground hover:shadow-elevation-md'
        }
        ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:-translate-y-[1px]'}
      `}
    >
      {isLoading ? (
        <>
          <Icon name="ArrowPathIcon" size={20} className="animate-spin" />
          <span>{isConnected ? 'Отключение...' : 'Подключение...'}</span>
        </>
      ) : (
        <>
          <Icon name={isConnected ? 'XMarkIcon' : 'LinkIcon'} size={20} />
          <span>{isConnected ? 'Отключить Google Calendar' : 'Подключить Google Calendar'}</span>
        </>
      )}
    </button>
  );
};

export default ConnectButton;
