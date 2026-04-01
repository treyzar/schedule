'use client';

import { useState, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface ChatMessageProps {
  message: {
    id: string;
    type: 'user' | 'ai';
    content: string;
    timestamp: string;
    status?: 'sending' | 'sent' | 'error';
    suggestions?: Array<{
      id: string;
      title: string;
      description: string;
      action: string;
    }>;
  };
  onActionClick?: (action: string, suggestionId: string) => void;
}

const ChatMessage = ({ message, onActionClick }: ChatMessageProps) => {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  if (!isHydrated) {
    return (
      <div
        className={`flex gap-3 mb-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
      >
        <div
          className={`max-w-[80%] rounded-lg p-4 ${
            message.type === 'user'
              ? 'bg-primary text-primary-foreground'
              : 'bg-card border border-border'
          }`}
        >
          <p className="text-sm font-body whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`flex gap-3 mb-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
      {message.type === 'ai' && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary flex items-center justify-center">
          <Icon name="SparklesIcon" size={20} className="text-primary-foreground" />
        </div>
      )}

      <div className={`max-w-[80%] ${message.type === 'user' ? 'order-first' : ''}`}>
        <div
          className={`rounded-lg p-4 ${
            message.type === 'user'
              ? 'bg-primary text-primary-foreground shadow-elevation-sm'
              : 'bg-card border border-border shadow-elevation-sm'
          }`}
        >
          <p className="text-sm font-body whitespace-pre-wrap">{message.content}</p>

          {message.suggestions && message.suggestions.length > 0 && (
            <div className="mt-4 space-y-2">
              {message.suggestions.map((suggestion) => (
                <div
                  key={suggestion.id}
                  className="p-3 rounded-md bg-muted border border-border hover:border-primary transition-smooth"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <h4 className="text-sm font-heading font-semibold text-foreground mb-1">
                        {suggestion.title}
                      </h4>
                      <p className="text-xs font-caption text-muted-foreground">
                        {suggestion.description}
                      </p>
                    </div>
                    <button
                      onClick={() => onActionClick?.(suggestion.action, suggestion.id)}
                      className="flex-shrink-0 px-3 py-1.5 text-xs font-body font-medium bg-primary text-primary-foreground rounded-md hover:shadow-elevation-md transition-smooth"
                    >
                      Применить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div
          className={`flex items-center gap-2 mt-1 px-2 ${
            message.type === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          <span className="text-xs font-caption text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
          {message.type === 'user' && message.status && (
            <Icon
              name={
                message.status === 'sent'
                  ? 'CheckIcon'
                  : message.status === 'error'
                    ? 'ExclamationCircleIcon'
                    : 'ClockIcon'
              }
              size={14}
              className={
                message.status === 'sent'
                  ? 'text-success'
                  : message.status === 'error'
                    ? 'text-error'
                    : 'text-muted-foreground'
              }
            />
          )}
        </div>
      </div>

      {message.type === 'user' && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-secondary flex items-center justify-center">
          <Icon name="UserIcon" size={20} className="text-secondary-foreground" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
