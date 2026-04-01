'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Icon from '@/components/ui/AppIcon';
import ChatMessage from './ChatMessage';
import QuickActionChips from './QuickActionChips';
import ContextSidebar from './ContextSidebar';
import MessageInput from './MessageInput';
import TypingIndicator from './TypingIndicator';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: string;
  status?: 'sending' | 'sent' | 'error';
}

const AIChatInteractive = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: 'Здравствуйте! Я ваш AI-помощник. Подключаюсь к ядру...',
      timestamp: new Date().toISOString(),
      status: 'sent',
    },
  ]);
  const [isConnecting, setIsConnecting] = useState(true);
  const [isReceiving, setIsReceiving] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isReceiving]);

  useEffect(() => {
    const wsUrl = 'ws://localhost:8001/ws/ai/chat/';
    const socket = new WebSocket(wsUrl);
    ws.current = socket;

    socket.onopen = () => {
      setIsConnecting(false);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === '1' ? { ...m, content: 'Я готов к работе. Чем могу помочь?' } : m
        )
      );
    };

    socket.onclose = () => {
      setIsConnecting(true);
      setIsReceiving(false);
    };
    socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setIsConnecting(true);
      setIsReceiving(false);
    };

    // --- ГЛАВНОЕ ИСПРАВЛЕНИЕ: обработчик сообщений ---
    socket.onmessage = (event) => {
      console.log('Received final message from WS:', event.data.full_response);

      // Сразу убираем индикатор печати
      setIsReceiving(false);

      try {
        const data = JSON.parse(event.data);

        // Создаем новое сообщение от AI
        const aiMessage: Message = {
          id: Date.now().toString(),
          type: 'ai',
          content: data.full_response || `Ошибка: получен некорректный ответ от сервера.`,
          timestamp: new Date().toISOString(),
          status: data.error ? 'error' : 'sent',
        };

        // --- ПУЛЕНЕПРОБИВАЕМЫЙ СПОСОБ ОБНОВЛЕНИЯ ---
        // Эта функция гарантированно получит самое свежее состояние `prev`,
        // включая сообщение, которое только что отправил пользователь.
        setMessages((prev) => [...prev, aiMessage]);
      } catch (e) {
        console.error('Failed to parse final WebSocket message:', e);
        // Обработка ошибки парсинга
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            type: 'ai',
            content: `Ошибка: получен некорректный ответ от сервера.`,
            timestamp: new Date().toISOString(),
            status: 'error',
          },
        ]);
      }
    };

    return () => {
      if (socket.readyState === 1) {
        socket.close();
      }
    };
  }, []); // <-- Пустой массив зависимостей. Эффект выполняется один раз.

  const handleSendMessage = useCallback(
    (content: string) => {
      if (!content.trim() || isReceiving || isConnecting) return;

      if (ws.current?.readyState === WebSocket.OPEN) {
        const userMessage: Message = {
          id: Date.now().toString(),
          type: 'user',
          content,
          timestamp: new Date().toISOString(),
          status: 'sent',
        };
        // Это обновление всегда работает правильно
        setMessages((prev) => [...prev, userMessage]);
        ws.current.send(JSON.stringify({ message: content }));
        setIsReceiving(true);
      } else {
        alert('Соединение с AI-сервисом не установлено. Попробуйте обновить страницу.');
      }
    },
    [isConnecting, isReceiving]
  );

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between p-4 border-b border-border bg-card">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center ${isConnecting ? 'bg-muted' : 'bg-primary'}`}
            >
              <Icon name="SparklesIcon" size={20} className="text-primary-foreground" />
            </div>
            <div>
              <h2 className="text-sm font-heading font-semibold text-foreground">AI Помощник</h2>
              <p
                className={`text-xs font-caption flex items-center gap-1 ${isConnecting ? 'text-warning' : 'text-success'}`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${isConnecting ? 'bg-warning' : 'bg-success'} ${!isConnecting && !isReceiving ? '' : 'animate-pulse'}`}
                />
                {isConnecting ? 'Подключение...' : isReceiving ? 'Генерация ответа...' : 'Онлайн'}
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-muted transition-smooth"
            aria-label="Открыть контекст"
          >
            <Icon name="InformationCircleIcon" size={20} />
          </button>
        </div>

        <div
          className="flex-1 overflow-y-auto p-4 space-y-4"
          style={{ maxHeight: 'calc(100vh - 280px)' }}
        >
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isReceiving && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        <QuickActionChips onChipClick={handleSendMessage} />
        <MessageInput onSendMessage={handleSendMessage} disabled={isConnecting || isReceiving} />
      </div>
      <ContextSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
    </div>
  );
};

export default AIChatInteractive;
