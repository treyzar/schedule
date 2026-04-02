"""
Сервис для работы с Google Calendar.
Обновлённая версия с шифрованием credentials и защитой от race conditions.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

import aiohttp
from aiogram.fsm.context import FSMContext
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import get_config
from exceptions import (
    GoogleTokenExpiredError,
    GoogleCalendarError,
    CredentialStatus,
)
from shared.credentials import GoogleCredentials, CredentialType
from utils.async_locks import token_refresh_lock

from .types import GoogleEvent
from .constants import SCOPES, CLIENT_SECRET_PATH

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """
    Сервис для работы с Google Calendar.
    
    Пример использования:
        service = GoogleCalendarService()
        
        # Получение событий
        events = await service.fetch_events(state, start, end)
        
        # Создание события
        event = await service.create_event(state, title, start, end)
    """
    
    def __init__(self):
        config = get_config()
        self.scopes = config.google.scopes
        self._credentials_cache: Optional[GoogleCredentials] = None
    
    async def get_credentials(
        self,
        state: FSMContext,
        user_id: Optional[str] = None
    ) -> Optional[GoogleCredentials]:
        """
        Получает и обновляет credentials пользователя с защитой от race condition.
        
        Args:
            state: Состояние FSM
            user_id: ID пользователя для блокировки (опционально)
            
        Returns:
            GoogleCredentials объект или None
            
        Пример:
            creds = await service.get_credentials(state, user_id="123")
            if creds:
                service = build('calendar', 'v3', credentials=creds.to_google_credentials())
        """
        user_id = user_id or str(state.proxy().get('user_id', 'default'))
        
        # Используем блокировку для предотвращения race condition
        async with token_refresh_lock(user_id, 'google'):
            return await self._get_credentials_internal(state)
    
    async def _get_credentials_internal(
        self,
        state: FSMContext
    ) -> Optional[GoogleCredentials]:
        """Внутренний метод получения credentials (внутри блокировки)"""
        user_data = await state.get_data()
        creds_data = user_data.get('google_creds')
        
        if not creds_data:
            logger.warning("Google credentials not found in state")
            return None
        
        try:
            # Если credentials уже в кэше и не истекли, возвращаем их
            if self._credentials_cache and not self._credentials_cache.is_expired:
                return self._credentials_cache
            
            # Парсим credentials
            if isinstance(creds_data, str):
                import json
                creds_data = json.loads(creds_data)
            
            credentials = GoogleCredentials.from_dict(creds_data)
            
            # Если токен истек, пробуем обновить
            if credentials.is_expired and credentials.refresh_token:
                logger.info("Google token expired, attempting refresh...")
                refreshed = await self._refresh_credentials_internal(credentials, state)
                
                if refreshed:
                    self._credentials_cache = refreshed
                    return refreshed
                else:
                    logger.warning("Failed to refresh Google token")
                    return None
            
            # Кэшируем и возвращаем
            self._credentials_cache = credentials
            return credentials
            
        except Exception as e:
            logger.error(f"Error getting Google credentials: {e}", exc_info=True)
            return None
    
    async def _refresh_credentials_internal(
        self,
        credentials: GoogleCredentials,
        state: FSMContext
    ) -> Optional[GoogleCredentials]:
        """
        Обновляет истекшие credentials.
        
        Args:
            credentials: Истекшие credentials
            state: Состояние FSM
            
        Returns:
            Обновлённые credentials или None
        """
        try:
            google_creds = credentials.to_google_credentials()
            
            # Выполняем синхронный refresh в executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: google_creds.refresh(Request())
            )
            
            # Создаём новые credentials из обновлённых
            refreshed = GoogleCredentials.from_google_credentials(google_creds)
            
            # Сохраняем в state
            await state.update_data(google_creds=refreshed.to_dict())
            
            logger.info("Google credentials successfully refreshed")
            return refreshed
            
        except Exception as e:
            logger.error(f"Error refreshing Google credentials: {e}", exc_info=True)
            return None
    
    async def fetch_events(
        self,
        state: FSMContext,
        start: datetime,
        end: datetime,
        user_id: Optional[str] = None
    ) -> Optional[List[GoogleEvent]]:
        """
        Получает события из Google Calendar.
        
        Args:
            state: Состояние FSM
            start: Начало периода
            end: Конец периода
            user_id: ID пользователя для блокировки
            
        Returns:
            Список событий или None
        """
        credentials = await self.get_credentials(state, user_id)
        
        if not credentials:
            logger.warning("No Google credentials available")
            return None
        
        try:
            google_creds = credentials.to_google_credentials()
            service = build('calendar', 'v3', credentials=google_creds)
            
            # Выполняем синхронный вызов в асинхронном контексте
            loop = asyncio.get_event_loop()
            
            events_result = await loop.run_in_executor(
                None,
                lambda: service.events().list(
                    calendarId='primary',
                    timeMin=start.isoformat(),
                    timeMax=end.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
            )
            
            items = events_result.get('items', [])
            return [GoogleEvent.from_api_response(item) for item in items]
            
        except Exception as e:
            logger.error(f"Error fetching Google Calendar events: {e}", exc_info=True)
            raise GoogleCalendarError(
                message=f"Ошибка получения событий: {str(e)}"
            )
    
    async def create_event(
        self,
        state: FSMContext,
        summary: str,
        start_datetime: datetime,
        end_datetime: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Создаёт событие в Google Calendar.
        
        Args:
            state: Состояние FSM
            summary: Название события
            start_datetime: Время начала
            end_datetime: Время окончания
            description: Описание (опционально)
            location: Местоположение (опционально)
            user_id: ID пользователя для блокировки
            
        Returns:
            Dict с данными созданного события или None
        """
        credentials = await self.get_credentials(state, user_id)
        
        if not credentials:
            logger.warning("No Google credentials for event creation")
            return None
        
        try:
            google_creds = credentials.to_google_credentials()
            service = build('calendar', 'v3', credentials=google_creds)
            
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/Moscow',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/Moscow',
                },
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            
            loop = asyncio.get_event_loop()
            
            created_event = await loop.run_in_executor(
                None,
                lambda: service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
            )
            
            logger.info(f"Created Google Calendar event: {created_event.get('id')}")
            return created_event
            
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}", exc_info=True)
            raise GoogleCalendarError(
                message=f"Ошибка создания события: {str(e)}"
            )
    
    async def check_event_conflict(
        self,
        state: FSMContext,
        start_datetime: datetime,
        end_datetime: datetime,
        user_id: Optional[str] = None
    ) -> Tuple[bool, List[dict]]:
        """
        Проверяет конфликты с существующими событиями.
        
        Args:
            state: Состояние FSM
            start_datetime: Время начала проверяемого события
            end_datetime: Время окончания проверяемого события
            user_id: ID пользователя
            
        Returns:
            Tuple[bool, List[dict]]: (есть ли конфликт, список конфликтующих событий)
        """
        events = await self.fetch_events(state, start_datetime, end_datetime, user_id)
        
        if not events:
            return (False, [])
        
        # Проверяем пересечения
        conflicts = []
        for event in events:
            event_start = event.start_datetime
            event_end = event.end_datetime
            
            # Проверяем пересечение интервалов
            if (start_datetime < event_end and end_datetime > event_start):
                conflicts.append({
                    'event_id': event.id,
                    'summary': event.summary,
                    'start': event_start.isoformat(),
                    'end': event_end.isoformat(),
                })
        
        return (len(conflicts) > 0, conflicts)
    
    async def format_events_text(
        self,
        events: List[GoogleEvent]
    ) -> str:
        """
        Форматирует события в текст.
        
        Args:
            events: Список событий
            
        Returns:
            Отформатированный текст
        """
        if not events:
            return "Событий не найдено"
        
        lines = []
        for event in events:
            time_str = event.format_time()
            lines.append(f"{time_str} - {event.summary}")
        
        lines.sort()
        return "\n".join([f"- {line}" for line in lines])
