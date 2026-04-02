'use client';

import { useState, useCallback } from 'react';
import Icon from '@/components/ui/AppIcon';

interface CalendarEvent {
  id: string;
  summary: string;
  start: { dateTime?: string; date?: string };
  end: { dateTime?: string; date?: string };
}

interface IntentResponse {
  intent_type: string;
  confidence: number;
  extracted_data?: {
    title: string;
    start_datetime?: string;
    end_datetime?: string;
    duration_minutes?: number;
    description?: string;
    location?: string;
  };
  clarification_needed: boolean;
  clarification_questions?: string[];
  suggested_action?: string;
}

interface CreateEventResponse {
  status: 'created' | 'clarification_needed' | 'conflict' | 'validation_error';
  event?: CalendarEvent;
  questions?: string[];
  conflicts?: Array<{
    event_id: string;
    summary: string;
    start: string;
    end: string;
  }>;
  alternatives?: string[];
  errors?: string[];
}

const AICreateEventWidget = () => {
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [intent, setIntent] = useState<IntentResponse | null>(null);
  const [result, setResult] = useState<CreateEventResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  /**
   * Отправляет текст на парсинг намерения
   */
  const handleParseIntent = useCallback(async () => {
    if (!inputText.trim()) return;

    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/ai/intent/parse/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText }),
      });

      if (!response.ok) {
        throw new Error('Failed to parse intent');
      }

      const data: IntentResponse = await response.json();
      setIntent(data);

      // Если намерение распознано и не требует уточнений, сразу создаём событие
      if (
        data.intent_type === 'create_event' &&
        !data.clarification_needed &&
        data.confidence > 0.7
      ) {
        await handleCreateEvent(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при анализе запроса');
    } finally {
      setIsProcessing(false);
    }
  }, [inputText]);

  /**
   * Создаёт событие на основе распарсенного намерения
   */
  const handleCreateEvent = useCallback(async (intentData?: IntentResponse) => {
    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/ai/events/create/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText }),
      });

      const data: CreateEventResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.errors?.[0] || 'Failed to create event');
      }

      setResult(data);

      if (data.status === 'created') {
        setInputText('');
        setIntent(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при создании события');
    } finally {
      setIsProcessing(false);
    }
  }, [inputText]);

  /**
   * Проверяет конфликты перед созданием
   */
  const handleCheckConflicts = useCallback(async () => {
    if (!intent?.extracted_data) return;

    setIsProcessing(true);
    setError(null);

    try {
      const { start_datetime, end_datetime } = intent.extracted_data;

      if (!start_datetime || !end_datetime) {
        setError('Укажите время начала и окончания события');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/ai/events/check-conflict/`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ start_datetime, end_datetime }),
      });

      const data = await response.json();

      if (data.has_conflict) {
        setResult({
          status: 'conflict',
          conflicts: data.conflicts,
          alternatives: data.alternatives,
        });
      } else {
        // Конфликтов нет, создаём событие
        await handleCreateEvent();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при проверке конфликтов');
    } finally {
      setIsProcessing(false);
    }
  }, [intent, handleCreateEvent]);

  /**
   * Форматирует дату для отображения
   */
  const formatDateTime = (dateTimeString?: string) => {
    if (!dateTimeString) return 'Не указано';
    try {
      const date = new Date(dateTimeString);
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateTimeString;
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4 space-y-4">
      {/* Заголовок */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
          <Icon name="SparklesIcon" size={20} className="text-primary" />
        </div>
        <div>
          <h3 className="text-sm font-heading font-semibold">Создать событие через AI</h3>
          <p className="text-xs text-muted-foreground">
            Напишите например: &quot;Встреча с командой завтра в 15:00 на час&quot;
          </p>
        </div>
      </div>

      {/* Поле ввода */}
      <div className="space-y-2">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Опишите событие естественным языком..."
          className="w-full min-h-[100px] p-3 rounded-lg border border-border bg-card focus:border-primary focus:ring-2 focus:ring-primary/20 transition-smooth resize-none"
          disabled={isProcessing}
        />
        
        <div className="flex gap-2">
          <button
            onClick={handleParseIntent}
            disabled={!inputText.trim() || isProcessing}
            className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-smooth disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <Icon name="ArrowPathIcon" size={16} className="animate-spin" />
                Обработка...
              </>
            ) : (
              <>
                <Icon name="SparklesIcon" size={16} />
                Распознать
              </>
            )}
          </button>
        </div>
      </div>

      {/* Ошибка */}
      {error && (
        <div className="p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
          <div className="flex items-start gap-2">
            <Icon name="ExclamationTriangleIcon" size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Результат парсинга намерения */}
      {intent && !result && (
        <div className="p-4 rounded-lg bg-card border border-border space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-heading font-semibold">Распознанное намерение</h4>
            <span className={`text-xs px-2 py-1 rounded-full ${
              intent.confidence > 0.8 ? 'bg-success/10 text-success' :
              intent.confidence > 0.5 ? 'bg-warning/10 text-warning' :
              'bg-error/10 text-error'
            }`}>
              {(intent.confidence * 100).toFixed(0)}% уверенность
            </span>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Тип:</span>
              <span className="font-medium">{intent.intent_type}</span>
            </div>
            
            {intent.extracted_data && (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Название:</span>
                  <span className="font-medium">{intent.extracted_data.title}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Начало:</span>
                  <span className="font-medium">
                    {formatDateTime(intent.extracted_data.start_datetime)}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Окончание:</span>
                  <span className="font-medium">
                    {formatDateTime(intent.extracted_data.end_datetime)}
                  </span>
                </div>

                {intent.extracted_data.description && (
                  <div>
                    <span className="text-muted-foreground">Описание:</span>
                    <p className="mt-1 text-foreground">{intent.extracted_data.description}</p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Уточняющие вопросы */}
          {intent.clarification_needed && intent.clarification_questions && (
            <div className="p-3 rounded-lg bg-warning/10 border border-warning/20">
              <p className="text-sm font-medium text-warning mb-2">Требуются уточнения:</p>
              <ul className="list-disc list-inside text-sm space-y-1">
                {intent.clarification_questions.map((q, i) => (
                  <li key={i} className="text-foreground">{q}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Кнопки действий */}
          <div className="flex gap-2 pt-2">
            {!intent.clarification_needed && (
              <>
                <button
                  onClick={handleCheckConflicts}
                  disabled={isProcessing}
                  className="flex-1 px-4 py-2 bg-success text-success-foreground rounded-md hover:bg-success/90 transition-smooth disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Icon name="CheckCircleIcon" size={16} />
                  Создать
                </button>
                
                <button
                  onClick={() => setIntent(null)}
                  className="px-4 py-2 bg-muted text-foreground rounded-md hover:bg-muted/80 transition-smooth"
                >
                  Отмена
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Результат создания */}
      {result && (
        <div className={`p-4 rounded-lg border ${
          result.status === 'created' ? 'bg-success/10 border-success/20' :
          result.status === 'conflict' ? 'bg-warning/10 border-warning/20' :
          'bg-error/10 border-error/20'
        }`}>
          <div className="flex items-start gap-3">
            <Icon 
              name={
                result.status === 'created' ? 'CheckCircleIcon' :
                result.status === 'conflict' ? 'ExclamationTriangleIcon' :
                'XCircleIcon'
              }
              size={20}
              className={
                result.status === 'created' ? 'text-success' :
                result.status === 'conflict' ? 'text-warning' :
                'text-error'
              }
            />
            
            <div className="flex-1">
              <h4 className={`text-sm font-semibold mb-2 ${
                result.status === 'created' ? 'text-success' :
                result.status === 'conflict' ? 'text-warning' :
                'text-error'
              }`}>
                {result.status === 'created' && 'Событие создано!'}
                {result.status === 'conflict' && 'Обнаружен конфликт'}
                {result.status === 'validation_error' && 'Ошибка валидации'}
              </h4>

              {result.status === 'created' && result.event && (
                <div className="text-sm space-y-1">
                  <p><strong>{result.event.summary}</strong></p>
                  <p className="text-muted-foreground">
                    {formatDateTime(result.event.start.dateTime || result.event.start.date)} - 
                    {formatDateTime(result.event.end.dateTime || result.event.end.date)}
                  </p>
                </div>
              )}

              {result.status === 'conflict' && result.conflicts && (
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium mb-1">Конфликтующие события:</p>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      {result.conflicts.map((conflict, i) => (
                        <li key={i} className="text-foreground">
                          {conflict.summary} ({formatDateTime(conflict.start)} - {formatDateTime(conflict.end)})
                        </li>
                      ))}
                    </ul>
                  </div>

                  {result.alternatives && result.alternatives.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-1">Предложенные альтернативы:</p>
                      <ul className="list-disc list-inside text-sm space-y-1">
                        {result.alternatives.map((alt, i) => (
                          <li key={i} className="text-foreground">{alt}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {result.status === 'validation_error' && result.errors && (
                <ul className="list-disc list-inside text-sm space-y-1">
                  {result.errors.map((err, i) => (
                    <li key={i} className="text-error">{err}</li>
                  ))}
                </ul>
              )}

              <button
                onClick={() => {
                  setResult(null);
                  setIntent(null);
                }}
                className="mt-3 px-4 py-2 text-sm rounded-md bg-background border border-border hover:bg-muted transition-smooth"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AICreateEventWidget;
