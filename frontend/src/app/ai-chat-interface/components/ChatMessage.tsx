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
  };
}

const ChatMessage = ({ message }: ChatMessageProps) => {
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

  // Простая функция для форматирования текста с поддержкой markdown-подобного синтаксиса
  const formatContent = (content: string) => {
    const lines = content.split('\n');
    const formattedLines = lines.map((line, index) => {
      // Заголовки
      if (line.startsWith('### ')) {
        return (
          <h3 key={index} className="text-sm font-heading font-semibold mt-4 mb-2">
            {line.replace('### ', '')}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={index} className="text-base font-heading font-semibold mt-3 mb-2">
            {line.replace('## ', '')}
          </h2>
        );
      }
      if (line.startsWith('# ')) {
        return (
          <h1 key={index} className="text-lg font-heading font-bold mt-3 mb-2">
            {line.replace('# ', '')}
          </h1>
        );
      }
      // Списки
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return (
          <li key={index} className="ml-4 text-sm">
            {line.substring(2)}
          </li>
        );
      }
      if (line.match(/^\d+\.\s/)) {
        return (
          <li key={index} className="ml-4 text-sm list-decimal">
            {line.replace(/^\d+\.\s/, '')}
          </li>
        );
      }
      // Жирный текст
      if (line.includes('**')) {
        const parts = line.split('**');
        return (
          <p key={index} className="text-sm mb-1">
            {parts.map((part, i) =>
              i % 2 === 1 ? (
                <strong key={i} className="font-semibold">
                  {part}
                </strong>
              ) : (
                part
              )
            )}
          </p>
        );
      }
      // Пустые строки
      if (line.trim() === '') {
        return <br key={index} />;
      }
      // Обычный текст
      return (
        <p key={index} className="text-sm mb-1">
          {line}
        </p>
      );
    });

    return formattedLines;
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
          <div className="font-body whitespace-pre-wrap">
            {message.type === 'ai' ? formatContent(message.content) : message.content}
          </div>
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
