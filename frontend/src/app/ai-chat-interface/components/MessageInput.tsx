'use client';

import { useState, useRef, useEffect } from 'react';
import Icon from '@/components/ui/AppIcon';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const MessageInput = ({ onSendMessage, disabled = false }: MessageInputProps) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-border bg-card p-4">
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Задайте вопрос о вашем расписании..."
            disabled={disabled}
            rows={1}
            className="w-full px-4 py-3 pr-12 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
          {message.length > 0 && (
            <button
              type="button"
              onClick={() => setMessage('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-muted transition-smooth"
              aria-label="Очистить"
            >
              <Icon name="XMarkIcon" size={18} className="text-muted-foreground" />
            </button>
          )}
        </div>

        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className="flex-shrink-0 p-3 rounded-full bg-primary text-primary-foreground hover:shadow-elevation-md transition-smooth disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Отправить сообщение"
        >
          <Icon name="PaperAirplaneIcon" size={20} />
        </button>
      </div>

      <div className="flex items-center gap-2 mt-2 text-xs font-caption text-muted-foreground">
        <Icon name="InformationCircleIcon" size={14} />
        <span>Нажмите Enter для отправки, Shift+Enter для новой строки</span>
      </div>
    </form>
  );
};

export default MessageInput;
