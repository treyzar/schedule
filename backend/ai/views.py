"""
API endpoints для AI-помощника.
Включая создание событий из естественного языка.
"""

import logging
from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any, List

from django.utils import timezone as django_timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from config import get_config
from exceptions import (
    AIError,
    AIIntentParseError,
    GoogleCalendarError,
    MissingRequiredFieldError,
)
from .intent_parser import AIIntentParser, IntentType, ParsedIntent, ExtractedEventData

logger = logging.getLogger(__name__)


def prepare_google_credentials_for_api(google_credentials: Dict[str, Any]):
    """
    Конвертирует google_credentials из session в формат для Google OAuth Credentials.
    
    Google OAuth библиотека ожидает параметр 'expiry' вместо 'expires_at'.
    
    Args:
        google_credentials: Dict из session с ключом 'expires_at'
        
    Returns:
        Dict с ключом 'expiry' вместо 'expires_at'
    """
    # Удаляем лишние ключи и конвертируем expires_at в expiry
    creds_data = {
        k: v for k, v in google_credentials.items()
        if k not in ('expires_at', 'email')
    }
    # Конвертируем ISO строку в datetime для expiry
    if 'expires_at' in google_credentials and google_credentials['expires_at']:
        try:
            expiry_dt = datetime.fromisoformat(google_credentials['expires_at'])
            creds_data['expiry'] = expiry_dt
        except (ValueError, TypeError):
            pass
    
    return creds_data


# =============================================================================
# === Оригинальные классы (сохранены для обратной совместимости) ===
# =============================================================================

class ScheduleContextView(APIView):
    """
    API endpoint для получения контекста расписания для AI.
    Возвращает события за указанный период в сжатом формате.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Получить контекст расписания для AI.

        Query parameters:
        - period: 'day', 'week', 'month' (по умолчанию 'week')
        - date: дата в формате YYYY-MM-DD (по умолчанию сегодня)
        """
        try:
            period = request.query_params.get('period', 'week')
            date_str = request.query_params.get('date', datetime.now().strftime('%Y-%m-%d'))

            try:
                base_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Неверный формат даты. Используйте YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Определяем диапазон дат
            if period == 'day':
                start_date = base_date
                end_date = base_date
            elif period == 'week':
                from datetime import timedelta
                start_date = base_date - timedelta(days=base_date.weekday())
                end_date = start_date + timedelta(days=6)
            elif period == 'month':
                start_date = base_date.replace(day=1)
                if base_date.month == 12:
                    end_date = base_date.replace(year=base_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = base_date.replace(month=base_date.month + 1, day=1) - timedelta(days=1)
            else:
                return Response(
                    {'error': 'period должен быть day, week или month'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Получаем события из сессии Google Calendar
            google_credentials = request.session.get('google_credentials')
            events = []

            if google_credentials:
                try:
                    from google.oauth2.credentials import Credentials
                    from googleapiclient.discovery import build

                    creds_data = prepare_google_credentials_for_api(google_credentials)
                    creds = Credentials(**creds_data)
                    service = build('calendar', 'v3', credentials=creds)

                    time_min = datetime.combine(start_date, time.min).isoformat() + 'Z'
                    time_max = datetime.combine(end_date + timedelta(days=1), time.min).isoformat() + 'Z'

                    events_result = service.events().list(
                        calendarId='primary',
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()

                    raw_events = events_result.get('items', [])

                    # Форматируем события для AI
                    for event in raw_events:
                        start = event.get('start', {})
                        end = event.get('end', {})

                        start_dt = start.get('dateTime', start.get('date', ''))
                        end_dt = end.get('dateTime', end.get('date', ''))

                        events.append({
                            'id': event.get('id', ''),
                            'title': event.get('summary', 'Без названия'),
                            'description': event.get('description', ''),
                            'start': start_dt,
                            'end': end_dt,
                            'location': event.get('location', ''),
                            'category': event.get('extendedProperties', {}).get('private', {}).get('category', ''),
                            'priority': event.get('extendedProperties', {}).get('private', {}).get('priority', ''),
                        })

                except Exception as e:
                    logger.error(f"Error fetching Google Calendar events: {e}")

            # Вычисляем статистику
            total_events = len(events)
            total_duration_minutes = 0
            events_by_category = {}
            events_by_day = {}

            for event in events:
                try:
                    start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds() / 60
                    total_duration_minutes += duration

                    category = event.get('category', 'uncategorized') or 'uncategorized'
                    events_by_category[category] = events_by_category.get(category, 0) + 1

                    day_key = start.strftime('%Y-%m-%d')
                    if day_key not in events_by_day:
                        events_by_day[day_key] = []
                    events_by_day[day_key].append({
                        'title': event['title'],
                        'start': event['start'],
                        'end': event['end'],
                        'duration': duration
                    })
                except Exception as e:
                    logger.error(f"Error processing event: {e}")

            # Формируем текстовую сводку
            context_text = self._build_context_text(
                period=period, start_date=start_date, end_date=end_date,
                events=events, total_events=total_events,
                total_duration_minutes=total_duration_minutes,
                events_by_category=events_by_category, events_by_day=events_by_day
            )

            return Response({
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'events': events,
                'statistics': {
                    'total_events': total_events,
                    'total_duration_hours': round(total_duration_minutes / 60, 1),
                    'events_by_category': events_by_category,
                },
                'context_text': context_text,
            })

        except Exception as e:
            logger.error(f"Error in ScheduleContextView: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_context_text(self, period, start_date, end_date, events, total_events,
                           total_duration_minutes, events_by_category, events_by_day):
        """Создаёт текстовую сводку для AI."""
        lines = []
        period_names = {'day': 'день', 'week': 'неделю', 'month': 'месяц'}
        lines.append(f"Расписание на {period_names.get(period, 'период')} с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}:")
        lines.append("")
        lines.append(f"Всего событий: {total_events}")
        lines.append(f"Общая продолжительность: {round(total_duration_minutes / 60, 1)} часов")
        lines.append("")
        if events_by_category:
            lines.append("События по категориям:")
            for category, count in sorted(events_by_category.items(), key=lambda x: -x[1]):
                lines.append(f"  - {category}: {count}")
            lines.append("")
        if events:
            lines.append("Ближайшие события:")
            for event in events[:10]:
                try:
                    start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    time_str = start.strftime('%H:%M')
                    lines.append(f"  - [{time_str}] {event['title']}")
                except:
                    lines.append(f"  - {event['title']}")
        return "\n".join(lines)


class ChatView(APIView):
    """HTTP чат (fallback для WebSocket)"""
    permission_classes = [AllowAny]

    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({"error": "Message is empty"}, status=status.HTTP_400_BAD_REQUEST)

        dialog_history = request.session.get('chat_history', [])
        dialog_history.append({"role": "user", "content": user_message})

        messages_for_api = [
            {"role": "system", "content": "You are a helpful and friendly assistant."},
        ]
        messages_for_api.extend(dialog_history)

        try:
            from openai import OpenAI
            config = get_config()
            
            client = OpenAI(
                base_url=config.ollama.base_url,
                api_key='ollama',
            )

            stream = client.chat.completions.create(
                model=config.ollama.model_name,
                messages=messages_for_api,
                temperature=0.7,
                stream=True,
            )

            def event_stream():
                full_response = ""
                try:
                    for chunk in stream:
                        token = chunk.choices[0].delta.content or ""
                        if token:
                            full_response += token
                            yield token

                    dialog_history.append({"role": "assistant", "content": full_response})
                    request.session['chat_history'] = dialog_history

                except Exception as e:
                    if dialog_history and dialog_history[-1]["role"] == "user":
                        dialog_history.pop()
                    request.session['chat_history'] = dialog_history
                    yield f" [ERROR: {e}]"

            from django.http import StreamingHttpResponse
            return StreamingHttpResponse(event_stream(), content_type='text/plain')

        except Exception as e:
            return Response({"error": f"Не удалось связаться с моделью. Ошибка: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# === Новые классы для AI Intent Parser ===
# =============================================================================


class ParseIntentView(APIView):
    """
    Парсит намерение пользователя из текста.
    
    POST /api/ai/intent/parse/
    Body: {"text": "Создай встречу завтра в 15:00", "context": "..."}
    
    Response:
    {
        "intent_type": "create_event",
        "confidence": 0.95,
        "extracted_data": {...},
        "clarification_needed": false,
        "suggested_action": "create"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        text = request.data.get('text')
        if not text:
            raise MissingRequiredFieldError('text')
        
        context = request.data.get('context')
        
        try:
            parser = AIIntentParser()
            # В реальной реализации нужно использовать asyncio
            # Для Django можно использовать async_to_sync
            from asgiref.sync import async_to_sync
            intent = async_to_sync(parser.parse)(text, context)
            
            return Response(intent.to_dict())
            
        except Exception as e:
            logger.error(f"Error parsing intent: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to parse intent', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateEventFromNaturalLanguage(APIView):
    """
    Создаёт событие из естественного языка.
    
    POST /api/ai/events/create/
    Body: {"text": "Встреча с командой завтра в 15:00 на час"}
    
    Response (success):
    {
        "status": "created",
        "event": {...}
    }
    
    Response (clarification needed):
    {
        "status": "clarification_needed",
        "questions": ["Когда встреча?", "Как называется?"]
    }
    
    Response (conflict):
    {
        "status": "conflict",
        "conflicts": [...],
        "alternatives": ["Завтра в 10:00", "Послезавтра в 14:00"]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        text = request.data.get('text')
        if not text:
            raise MissingRequiredFieldError('text')
        
        try:
            # 1. Парсим намерение
            parser = AIIntentParser()
            from asgiref.sync import async_to_sync
            intent = async_to_sync(parser.parse)(text)
            
            # 2. Проверяем тип намерения
            if intent.intent_type != IntentType.CREATE_EVENT:
                return Response(
                    {
                        'error': 'Intent is not create_event',
                        'detected_intent': intent.intent_type.value
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 3. Если нужны уточнения - возвращаем вопросы
            if intent.clarification_needed:
                return Response({
                    'status': 'clarification_needed',
                    'questions': intent.clarification_questions or [],
                    'confidence': intent.confidence,
                })
            
            # 4. Проверяем наличие данных
            if not intent.extracted_data:
                return Response(
                    {'error': 'No event data extracted'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 5. Валидируем обязательные поля
            validation_errors = self._validate_event_data(intent.extracted_data)
            if validation_errors:
                return Response({
                    'status': 'validation_error',
                    'errors': validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 6. Получаем credentials из сессии
            google_credentials = request.session.get('google_credentials')
            if not google_credentials:
                return Response(
                    {'error': 'Google credentials not found. Please authenticate first.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # 7. Создаём событие
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds_data = prepare_google_credentials_for_api(google_credentials)
            creds = Credentials(**creds_data)
            service = build('calendar', 'v3', credentials=creds)
            
            event_data = self._build_event_dict(intent.extracted_data)
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            logger.info(f"Created event from natural language: {created_event.get('id')}")
            
            return Response({
                'status': 'created',
                'event': created_event,
                'intent_confidence': intent.confidence,
            })
            
        except Exception as e:
            logger.error(f"Error creating event: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to create event', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_event_data(self, data: ExtractedEventData) -> List[str]:
        """Валидирует данные события"""
        errors = []
        
        if not data.title or len(data.title.strip()) == 0:
            errors.append("Название события обязательно")
        
        if not data.start_datetime and not data.duration_minutes:
            errors.append("Укажите время начала или длительность события")
        
        if data.start_datetime and data.end_datetime:
            try:
                start = datetime.fromisoformat(data.start_datetime.replace('Z', '+00:00'))
                end = datetime.fromisoformat(data.end_datetime.replace('Z', '+00:00'))
                if end <= start:
                    errors.append("Время окончания должно быть позже времени начала")
            except ValueError:
                errors.append("Неверный формат даты/времени")
        
        return errors
    
    def _build_event_dict(self, data: ExtractedEventData) -> Dict[str, Any]:
        """Строит dict события для Google Calendar API"""
        event = {
            'summary': data.title,
        }
        
        if data.description:
            event['description'] = data.description
        
        if data.location:
            event['location'] = data.location
        
        # Время начала и окончания
        if data.start_datetime and data.end_datetime:
            event['start'] = {'dateTime': data.start_datetime, 'timeZone': 'Europe/Moscow'}
            event['end'] = {'dateTime': data.end_datetime, 'timeZone': 'Europe/Moscow'}
        elif data.start_datetime and data.duration_minutes:
            start = datetime.fromisoformat(data.start_datetime.replace('Z', '+00:00'))
            end = start + timedelta(minutes=data.duration_minutes)
            event['start'] = {'dateTime': start.isoformat(), 'timeZone': 'Europe/Moscow'}
            event['end'] = {'dateTime': end.isoformat(), 'timeZone': 'Europe/Moscow'}
        else:
            # Если время не указано, создаём событие на целый день
            event['start'] = {'date': datetime.now().strftime('%Y-%m-%d')}
            event['end'] = {'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
        
        # Расширенные свойства для категоризации
        if data.category or data.priority:
            event['extendedProperties'] = {'private': {}}
            if data.category:
                event['extendedProperties']['private']['category'] = data.category
            if data.priority:
                event['extendedProperties']['private']['priority'] = data.priority
        
        return event


class CheckEventConflictView(APIView):
    """
    Проверяет конфликты для предлагаемого события.
    
    POST /api/ai/events/check-conflict/
    Body: {
        "start_datetime": "2024-04-02T15:00:00+03:00",
        "end_datetime": "2024-04-02T16:00:00+03:00"
    }
    
    Response:
    {
        "has_conflict": true,
        "conflicts": [
            {"event_id": "...", "summary": "Meeting", "start": "...", "end": "..."}
        ],
        "alternatives": ["Завтра в 10:00", ...]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        start_str = request.data.get('start_datetime')
        end_str = request.data.get('end_datetime')
        
        if not start_str or not end_str:
            raise MissingRequiredFieldError('start_datetime and end_datetime')
        
        try:
            # Получаем credentials
            google_credentials = request.session.get('google_credentials')
            if not google_credentials:
                return Response(
                    {'error': 'Google credentials not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds_data = prepare_google_credentials_for_api(google_credentials)
            creds = Credentials(**creds_data)
            service = build('calendar', 'v3', credentials=creds)

            # Получаем события за период
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_str,
                timeMax=end_str,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Проверяем пересечения
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            
            conflicts = []
            for event in events:
                event_start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
                event_end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
                
                if event_start and event_end:
                    event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    event_end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
                    
                    # Проверяем пересечение
                    if start_dt < event_end_dt and end_dt > event_start_dt:
                        conflicts.append({
                            'event_id': event.get('id'),
                            'summary': event.get('summary', 'Без названия'),
                            'start': event_start,
                            'end': event_end,
                        })
            
            # Запрашиваем альтернативы если есть конфликты
            alternatives = []
            if conflicts:
                parser = AIIntentParser()
                from asgiref.sync import async_to_sync
                alternatives = async_to_sync(parser.suggest_alternative_times)(conflicts)
            
            return Response({
                'has_conflict': len(conflicts) > 0,
                'conflicts': conflicts,
                'alternatives': alternatives,
            })
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to check conflicts', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FindFreeTimeView(APIView):
    """
    Находит свободное время в расписании.
    
    POST /api/ai/events/find-free-time/
    Body: {
        "duration_minutes": 60,
        "date_range": {"start": "2024-04-01", "end": "2024-04-07"},
        "working_hours": {"start": "09:00", "end": "18:00"}
    }
    
    Response:
    {
        "free_slots": [
            {"date": "2024-04-02", "start": "10:00", "end": "11:00"},
            ...
        ]
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        duration_minutes = request.data.get('duration_minutes', 60)
        date_range = request.data.get('date_range', {})
        working_hours = request.data.get('working_hours', {'start': '09:00', 'end': '18:00'})
        
        try:
            # Получаем credentials
            google_credentials = request.session.get('google_credentials')
            if not google_credentials:
                return Response(
                    {'error': 'Google credentials not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds_data = prepare_google_credentials_for_api(google_credentials)
            creds = Credentials(**creds_data)
            service = build('calendar', 'v3', credentials=creds)

            start_date = date_range.get('start', datetime.now().strftime('%Y-%m-%d'))
            end_date = date_range.get('end', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
            
            # Получаем события
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_date + 'T00:00:00',
                timeMax=end_date + 'T23:59:59',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Находим свободные слоты
            free_slots = self._find_free_slots(
                events,
                duration_minutes,
                start_date,
                end_date,
                working_hours
            )
            
            return Response({
                'free_slots': free_slots[:10],  # Возвращаем первые 10 слотов
                'total_found': len(free_slots),
            })
            
        except Exception as e:
            logger.error(f"Error finding free time: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to find free time', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _find_free_slots(
        self,
        events: List[dict],
        duration_minutes: int,
        start_date: str,
        end_date: str,
        working_hours: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Находит свободные слоты в расписании"""
        from datetime import datetime, timedelta
        
        work_start = datetime.strptime(working_hours['start'], '%H:%M').time()
        work_end = datetime.strptime(working_hours['end'], '%H:%M').time()
        
        # Группируем события по дням
        events_by_day = {}
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
            end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
            
            if start and end:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                day_key = start_dt.strftime('%Y-%m-%d')
                if day_key not in events_by_day:
                    events_by_day[day_key] = []
                events_by_day[day_key].append((start_dt, end_dt))
        
        # Находим свободные слоты
        free_slots = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current <= end:
            day_key = current.strftime('%Y-%-%d')
            day_events = sorted(events_by_day.get(day_key, []), key=lambda x: x[0])
            
            # Проверяем слоты в рабочие часы
            slot_start = datetime.combine(current.date(), work_start)
            slot_end = datetime.combine(current.date(), work_end)
            
            # Находим промежутки между событиями
            last_end = slot_start
            for event_start, event_end in day_events:
                if event_start > last_end:
                    gap_minutes = (event_start - last_end).total_seconds() / 60
                    if gap_minutes >= duration_minutes:
                        free_slots.append({
                            'date': day_key,
                            'start': last_end.strftime('%H:%M'),
                            'end': event_start.strftime('%H:%M'),
                            'duration_minutes': int(gap_minutes),
                        })
                last_end = max(last_end, event_end)
            
            # Последний слот после всех событий
            if last_end < slot_end:
                gap_minutes = (slot_end - last_end).total_seconds() / 60
                if gap_minutes >= duration_minutes:
                    free_slots.append({
                        'date': day_key,
                        'start': last_end.strftime('%H:%M'),
                        'end': slot_end.strftime('%H:%M'),
                        'duration_minutes': int(gap_minutes),
                    })
            
            current += timedelta(days=1)
        
        return free_slots
