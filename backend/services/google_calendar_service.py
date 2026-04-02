"""
Сервис для работы с Google Calendar.
Полная версия с поддержкой создания, обновления и удаления событий.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from django.conf import settings
from django.utils import timezone as django_timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from services.google_auth import GoogleAuthService
from exceptions import (
    GoogleCalendarError,
    GoogleEventNotFoundError,
    GoogleEventConflictError,
)

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """
    Сервис для работы с Google Calendar.
    
    Пример использования:
        service = GoogleCalendarService()
        
        # Получение сервиса с credentials из сессии
        calendar_service = service.get_service(request.session)
        
        # Создание события
        event = service.create_event(
            request.session,
            summary='Встреча',
            start_datetime=datetime.now(),
            end_datetime=datetime.now() + timedelta(hours=1)
        )
    """
    
    def __init__(self):
        self.auth_service = GoogleAuthService()
        self.default_timezone = 'Europe/Moscow'
    
    def get_service(self, session) -> Optional[Any]:
        """
        Получает авторизованный сервис Google Calendar.
        
        Args:
            session: Django session
            
        Returns:
            Сервис Google Calendar или None
        """
        credentials_data = session.get('google_credentials')
        if not credentials_data:
            logger.warning("Google credentials not found in session")
            return None
        
        return self.auth_service.get_calendar_service(credentials_data)
    
    def get_credentials_status(self, session) -> Dict[str, Any]:
        """
        Проверяет статус credentials.
        
        Args:
            session: Django session
            
        Returns:
            Dict со статусом credentials
        """
        credentials_data = session.get('google_credentials')
        if not credentials_data:
            return {
                'authenticated': False,
                'status': 'not_authenticated',
            }
        
        status, credentials = self.auth_service.check_credential_status(credentials_data)
        
        return {
            'authenticated': status == 'valid',
            'status': status,
            'credentials': credentials.to_dict() if credentials else None,
        }
    
    def create_event(
        self,
        session,
        summary: str,
        start_datetime: datetime,
        end_datetime: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        reminders: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Создаёт событие в Google Calendar.
        """
        # Проверяем credentials
        credentials_data = session.get('google_credentials')
        if not credentials_data:
            logger.error("Google credentials NOT found in session!")
            raise GoogleCalendarError(
                message="Необходимо авторизоваться в Google Calendar. Пожалуйста, пройдите авторизацию.",
                status_code=401
            )
        
        logger.info(f"Creating event: summary={summary}, start={start_datetime}, end={end_datetime}")
        logger.debug(f"Credentials keys: {credentials_data.keys() if isinstance(credentials_data, dict) else 'N/A'}")
        
        # Получаем сервис
        service = self.auth_service.get_calendar_service(credentials_data)
        if not service:
            logger.error("Failed to get calendar service - credentials may be invalid")
            raise GoogleCalendarError(
                message="Ошибка авторизации. Пожалуйста, пройдите авторизацию заново.",
                status_code=401
            )
        
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': self._format_datetime(start_datetime),
                    'timeZone': self.default_timezone,
                },
                'end': {
                    'dateTime': self._format_datetime(end_datetime),
                    'timeZone': self.default_timezone,
                },
            }
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Расширенные свойства
            if category or priority:
                event['extendedProperties'] = {'private': {}}
                if category:
                    event['extendedProperties']['private']['category'] = category
                if priority:
                    event['extendedProperties']['private']['priority'] = priority
            
            # Напоминания
            if reminders:
                event['reminders'] = reminders
            else:
                # Напоминание по умолчанию за 10 минут
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 10},
                    ]
                }
            
            logger.info(f"Sending event to Google API: {event}")
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'  # Отправить приглашения участникам
            ).execute()
            
            logger.info(f"✓ Created Google Calendar event: {created_event.get('id')}")
            logger.info(f"  HTML Link: {created_event.get('htmlLink')}")
            
            return self._parse_event(created_event)
            
        except HttpError as e:
            logger.error(f"✗ Google API error creating event: {e}", exc_info=True)
            error_content = e.content.decode('utf-8') if e.content else 'No content'
            logger.error(f"  Error content: {error_content}")
            
            if e.resp.status == 400:
                raise GoogleCalendarError(
                    message=f"Неверные параметры события: {error_content}",
                    status_code=400
                )
            elif e.resp.status == 401:
                raise GoogleCalendarError(
                    message="Ошибка авторизации. Пожалуйста, пройдите авторизацию заново.",
                    status_code=401
                )
            elif e.resp.status == 403:
                raise GoogleCalendarError(
                    message="Нет доступа к календарю. Проверьте права доступа.",
                    status_code=403
                )
            raise GoogleCalendarError(
                message=f"Ошибка создания события: {error_content}",
                status_code=e.resp.status
            )
        except Exception as e:
            logger.error(f"✗ Error creating event: {e}", exc_info=True)
            raise GoogleCalendarError(message=f"Ошибка создания события: {str(e)}")
    
    def update_event(
        self,
        session,
        event_id: str,
        summary: Optional[str] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Обновляет существующее событие.
        
        Args:
            session: Django session
            event_id: ID события
            summary: Новое название
            start_datetime: Новое время начала
            end_datetime: Новое время окончания
            description: Новое описание
            location: Новое местоположение
            status: Статус события (confirmed, cancelled, tentative)
            
        Returns:
            Dict с данными обновлённого события
        """
        service = self.get_service(session)
        if not service:
            raise GoogleCalendarError(
                message="Необходимо авторизоваться в Google Calendar",
                status_code=401
            )
        
        try:
            # Получаем текущее событие
            existing_event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Обновляем поля
            if summary:
                existing_event['summary'] = summary
            if description:
                existing_event['description'] = description
            if location:
                existing_event['location'] = location
            if status:
                existing_event['status'] = status
            if start_datetime:
                existing_event['start'] = {
                    'dateTime': self._format_datetime(start_datetime),
                    'timeZone': self.default_timezone,
                }
            if end_datetime:
                existing_event['end'] = {
                    'dateTime': self._format_datetime(end_datetime),
                    'timeZone': self.default_timezone,
                }
            
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=existing_event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f"Updated Google Calendar event: {event_id}")
            
            return self._parse_event(updated_event)
            
        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleEventNotFoundError(event_id)
            logger.error(f"Google API error updating event: {e}")
            raise GoogleCalendarError(
                message=f"Ошибка обновления события: {self._parse_http_error(e)}",
                status_code=e.resp.status
            )
        except Exception as e:
            logger.error(f"Error updating event: {e}", exc_info=True)
            raise GoogleCalendarError(message=f"Ошибка обновления события: {str(e)}")
    
    def delete_event(
        self,
        session,
        event_id: str,
        send_notifications: bool = True
    ) -> bool:
        """
        Удаляет событие из календаря.
        
        Args:
            session: Django session
            event_id: ID события
            send_notifications: Отправлять ли уведомления об отмене
            
        Returns:
            True если успешно
        """
        service = self.get_service(session)
        if not service:
            raise GoogleCalendarError(
                message="Необходимо авторизоваться в Google Calendar",
                status_code=401
            )
        
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleEventNotFoundError(event_id)
            logger.error(f"Google API error deleting event: {e}")
            raise GoogleCalendarError(
                message=f"Ошибка удаления события: {self._parse_http_error(e)}",
                status_code=e.resp.status
            )
        except Exception as e:
            logger.error(f"Error deleting event: {e}", exc_info=True)
            raise GoogleCalendarError(message=f"Ошибка удаления события: {str(e)}")
    
    def get_event(
        self,
        session,
        event_id: str
    ) -> Dict[str, Any]:
        """
        Получает событие по ID.
        
        Args:
            session: Django session
            event_id: ID события
            
        Returns:
            Dict с данными события
        """
        service = self.get_service(session)
        if not service:
            raise GoogleCalendarError(
                message="Необходимо авторизоваться в Google Calendar",
                status_code=401
            )
        
        try:
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return self._parse_event(event)
            
        except HttpError as e:
            if e.resp.status == 404:
                raise GoogleEventNotFoundError(event_id)
            logger.error(f"Google API error getting event: {e}")
            raise GoogleCalendarError(
                message=f"Ошибка получения события: {self._parse_http_error(e)}",
                status_code=e.resp.status
            )
    
    def list_events(
        self,
        session,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 250,
        calendar_id: str = 'primary',
    ) -> List[Dict[str, Any]]:
        """
        Получает список событий.
        
        Args:
            session: Django session
            time_min: Начало периода
            time_max: Конец периода
            max_results: Максимальное количество событий
            calendar_id: ID календаря
            
        Returns:
            Список событий
        """
        service = self.get_service(session)
        if not service:
            logger.warning("Google credentials not found")
            return []
        
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() if time_min else None,
                timeMax=time_max.isoformat() if time_max else None,
                singleEvents=True,
                orderBy='startTime',
                maxResults=max_results
            ).execute()
            
            events = events_result.get('items', [])
            return [self._parse_event(event) for event in events]
            
        except HttpError as e:
            logger.error(f"Google API error listing events: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing events: {e}", exc_info=True)
            return []
    
    def check_event_conflict(
        self,
        session,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_event_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Проверяет конфликты с существующими событиями.
        
        Args:
            session: Django session
            start_datetime: Время начала проверяемого периода
            end_datetime: Время окончания проверяемого периода
            exclude_event_id: ID события для исключения (при обновлении)
            
        Returns:
            Список конфликтующих событий
        """
        events = self.list_events(session, start_datetime, end_datetime)
        
        conflicts = []
        for event in events:
            if exclude_event_id and event.get('id') == exclude_event_id:
                continue
            
            # Проверяем пересечение
            event_start = self._parse_datetime(event.get('start'))
            event_end = self._parse_datetime(event.get('end'))
            
            if start_datetime < event_end and end_datetime > event_start:
                conflicts.append(event)
        
        return conflicts
    
    def find_free_time(
        self,
        session,
        duration_minutes: int,
        date_start: datetime,
        date_end: datetime,
        working_hours_start: int = 9,
        working_hours_end: int = 18,
    ) -> List[Dict[str, Any]]:
        """
        Находит свободное время в расписании.
        
        Args:
            session: Django session
            duration_minutes: Требуемая длительность в минутах
            date_start: Начало периода поиска
            date_end: Конец периода поиска
            working_hours_start: Начало рабочего дня (часы)
            working_hours_end: Конец рабочего дня (часы)
            
        Returns:
            Список свободных слотов
        """
        events = self.list_events(session, date_start, date_end)
        
        free_slots = []
        current_date = date_start.replace(hour=working_hours_start, minute=0, second=0, microsecond=0)
        
        while current_date.date() <= date_end.date():
            # Конец рабочего дня
            day_end = current_date.replace(hour=working_hours_end, minute=0)
            
            # События на этот день
            day_events = [
                e for e in events
                if self._parse_datetime(e.get('start')).date() == current_date.date()
            ]
            day_events.sort(key=lambda e: self._parse_datetime(e.get('start')))
            
            # Находим свободные слоты
            slot_start = current_date
            for event in day_events:
                event_start = self._parse_datetime(event.get('start'))
                event_end = self._parse_datetime(event.get('end'))
                
                if event_start > slot_start:
                    gap_minutes = (event_start - slot_start).total_seconds() / 60
                    if gap_minutes >= duration_minutes:
                        free_slots.append({
                            'start': slot_start.isoformat(),
                            'end': event_start.isoformat(),
                            'duration_minutes': int(gap_minutes),
                        })
                
                slot_start = max(slot_start, event_end)
            
            # Последний слот дня
            if slot_start < day_end:
                gap_minutes = (day_end - slot_start).total_seconds() / 60
                if gap_minutes >= duration_minutes:
                    free_slots.append({
                        'start': slot_start.isoformat(),
                        'end': day_end.isoformat(),
                        'duration_minutes': int(gap_minutes),
                    })
            
            # Следующий день
            current_date = current_date.replace(hour=working_hours_start) + timedelta(days=1)
        
        return free_slots[:10]  # Возвращаем первые 10 слотов
    
    # === Вспомогательные методы ===
    
    def _format_datetime(self, dt: datetime) -> str:
        """Форматирует datetime для Google API"""
        if dt.tzinfo is None:
            from django.utils import timezone as django_timezone
            import pytz
            dt = django_timezone.make_aware(dt, pytz.timezone(self.default_timezone))
        return dt.isoformat()
    
    def _parse_datetime(self, dt_dict: Optional[Dict]) -> datetime:
        """Парсит datetime из Google API"""
        if not dt_dict:
            return datetime.now()
        
        dt_str = dt_dict.get('dateTime') or dt_dict.get('date')
        if not dt_str:
            return datetime.now()
        
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            return datetime.now()
    
    def _parse_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит событие из Google API в удобный формат"""
        return {
            'id': event.get('id'),
            'summary': event.get('summary', 'Без названия'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start': event.get('start', {}),
            'end': event.get('end', {}),
            'status': event.get('status', 'confirmed'),
            'created': event.get('created'),
            'updated': event.get('updated'),
            'attendees': event.get('attendees', []),
            'organizer': event.get('organizer', {}),
            'html_link': event.get('htmlLink'),
            'category': event.get('extendedProperties', {}).get('private', {}).get('category'),
            'priority': event.get('extendedProperties', {}).get('private', {}).get('priority'),
        }
    
    def _parse_http_error(self, error: HttpError) -> str:
        """Парсит ошибку Google API"""
        try:
            error_content = error.content.decode('utf-8')
            error_data = eval(error_content)  # Google API возвращает dict в строке
            return error_data.get('error', {}).get('message', str(error))
        except:
            return str(error)
