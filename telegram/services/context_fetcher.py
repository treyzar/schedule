"""
Сервис для сбора контекста из различных источников (Google Calendar, Skyeng)
для последующей передачи AI ассистенту.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio

import pytz

from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone('Europe/Moscow')


class ContextFetcher:
    """
    Сервис для сбора контекста из Google Calendar и Skyeng.
    
    Разделяет ответственность за получение данных из разных источников
    и их форматирование.
    """
    
    def __init__(
        self,
        google_events_fetcher,
        skyeng_data_fetcher,
        skyeng_subject_page_fetcher
    ):
        self.google_events_fetcher = google_events_fetcher
        self.skyeng_data_fetcher = skyeng_data_fetcher
        self.skyeng_subject_page_fetcher = skyeng_subject_page_fetcher
    
    async def fetch_full_context(self, state: FSMContext) -> str:
        """
        Собирает полный контекст из всех источников.
        
        Args:
            state: FSMContext для доступа к данным пользователя
            
        Returns:
            Отформатированная строка с контекстом
        """
        now = datetime.now(TIMEZONE)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        sections = [
            self._get_datetime_section(now),
            await self._get_google_calendar_section(state, start_of_day, end_of_day),
            await self._get_skyeng_section(state),
        ]
        
        return "\n".join([s for s in sections if s])
    
    def _get_datetime_section(self, now: datetime) -> str:
        """Секция с текущей датой и временем"""
        return f"ТЕКУЩАЯ ДАТА И ВРЕМЯ: {now.strftime('%d.%m.%Y %H:%M')}"
    
    async def _get_google_calendar_section(
        self,
        state: FSMContext,
        start: datetime,
        end: datetime
    ) -> str:
        """Секция с событиями Google Calendar"""
        events = await self.google_events_fetcher(
            state,
            start.isoformat(),
            end.isoformat()
        )
        
        if events is None:
            return "\nКАЛЕНДАРЬ GOOGLE: Нет подключения или произошла ошибка."
        
        if not events:
            return "\nКАЛЕНДАРЬ GOOGLE НА СЕГОДНЯ: Записей нет."
        
        lines = ["\nКАЛЕНДАРЬ GOOGLE НА СЕГОДНЯ:"]
        event_lines = []
        
        for event in events:
            start_info = event.get('start', {})
            summary = event.get('summary', 'Без названия')
            
            if 'dateTime' in start_info:
                time_str = datetime.fromisoformat(start_info['dateTime']).strftime('%H:%M')
                event_lines.append(f"{time_str} - {summary}")
            elif 'date' in start_info:
                event_lines.append(f"Весь день - {summary}")
        
        event_lines.sort()
        lines.extend([f"- {line}" for line in event_lines])
        return "\n".join(lines)
    
    async def _get_skyeng_section(self, state: FSMContext) -> str:
        """Секция с данными Skyeng"""
        try:
            # Получаем базовые данные через API
            lessons, tasks, grades = await asyncio.gather(
                self.skyeng_data_fetcher(state, 'lessons'),
                self.skyeng_data_fetcher(state, 'tasks', days=1),
                self.skyeng_data_fetcher(state, 'grades')
            )
            
            # Получаем расширенные данные для специальных предметов
            extended_data = {}
            for subject_enum in ['math', 'career_guidance']:
                data = await self.skyeng_subject_page_fetcher(state, subject_enum)
                if data:
                    extended_data[subject_enum] = data
            
            return self._format_skyeng_data(lessons, tasks, grades, extended_data)
            
        except Exception as e:
            logger.error(f"Ошибка при чтении данных Skyeng: {e}")
            return "\nSKYENG: Произошла ошибка при получении данных."
    
    def _format_skyeng_data(
        self,
        lessons: List[str],
        tasks: List[str],
        grades: List[str],
        extended_data: Dict[str, Dict]
    ) -> str:
        """Форматирует данные Skyeng в строку"""
        lines = []
        
        # Уроки
        if lessons:
            lines.append("\nУРОКИ SKYENG НА СЕГОДНЯ:")
            lines.extend([f"- {lesson}" for lesson in lessons])
        else:
            lines.append("\nУРОКИ SKYENG НА СЕГОДНЯ: Уроков нет.")
        
        # Запланированные уроки по математике
        math_data = extended_data.get('math', {})
        if math_data.get('scheduled_lessons'):
            lines.append("\nЗАПЛАНИРОВАННЫЕ УРОКИ ПО МАТЕМАТИКЕ:")
            for lesson in math_data['scheduled_lessons'][:3]:
                lines.append(f"- {lesson['time']}: {lesson['title']}")
        
        # Домашние задания
        if tasks:
            lines.append("\nДОМАШНИЕ ЗАДАНИЯ SKYENG (дедлайн сегодня/завтра):")
            lines.extend([f"- {task}" for task in tasks])
        else:
            lines.append("\nДОМАШНИЕ ЗАДАНИЯ SKYENG: Срочных заданий нет.")
        
        # Оценки за тесты по математике
        if math_data.get('test_scores'):
            lines.append("\nОЦЕНКИ ЗА ТЕСТЫ ПО МАТЕМАТИКЕ:")
            for score in math_data['test_scores'][:3]:
                lines.append(f"- {score}")
        
        # Профориентация
        career_data = extended_data.get('career_guidance', {})
        if career_data.get('program_progress'):
            lines.append(f"\nПРОГРЕСС ПО ПРОФОРИЕНТАЦИИ: {career_data['program_progress']}")
        
        if career_data.get('homework_scores'):
            lines.append("\nОЦЕНКИ ЗА ДЗ ПО ПРОФОРИЕНТАЦИИ:")
            for score in career_data['homework_scores'][:3]:
                lines.append(f"- {score}")
        
        # Средний балл
        if grades:
            lines.append("\nСРЕДНИЙ БАЛЛ SKYENG:")
            lines.extend([f"- {grade}" for grade in grades])
        else:
            lines.append("\nСРЕДНИЙ БАЛЛ SKYENG: Оценок пока нет.")
        
        # Допуск к экзамену
        if math_data.get('exam_access_info'):
            lines.append(f"\nДОПУСК К ЭКЗАМЕНУ ПО МАТЕМАТИКЕ: {math_data['exam_access_info']}")
        
        return "\n".join(lines)


async def create_context_fetcher() -> ContextFetcher:
    """
    Factory function для создания ContextFetcher с зависимостями.
    Импортируем функции здесь, чтобы избежать циклических импортов.
    """
    from telegram.bot import (
        fetch_google_events,
        fetch_skyeng_data,
        fetch_skyeng_subject_page_data
    )
    
    return ContextFetcher(
        google_events_fetcher=fetch_google_events,
        skyeng_data_fetcher=fetch_skyeng_data,
        skyeng_subject_page_fetcher=fetch_skyeng_subject_page_data
    )
