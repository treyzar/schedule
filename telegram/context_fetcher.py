"""
Сервис для сбора контекста из различных источников
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pytz
from aiogram.fsm.context import FSMContext

from .types import GoogleEvent, SubjectEnum
from .services.google_calendar import GoogleCalendarService
from .services.skyeng_data import SkyengDataService

logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone('Europe/Moscow')


class ContextFetcher:
    """Сбор контекста для AI"""
    
    def __init__(self):
        self.google_service = GoogleCalendarService()
        self.skyeng_service = SkyengDataService()
    
    async def fetch_full_context(self, state: FSMContext) -> str:
        """
        Собирает полный контекст из всех источников.
        
        Args:
            state: Состояние FSM
            
        Returns:
            Строка с отформатированным контекстом
        """
        sections = [
            self._get_datetime_section(),
            await self._get_google_calendar_section(state),
            await self._get_skyeng_section(state),
        ]
        return "\n".join([s for s in sections if s])
    
    def _get_datetime_section(self) -> str:
        """Секция с текущей датой и временем"""
        now = datetime.now(TIMEZONE)
        return f"ТЕКУЩАЯ ДАТА И ВРЕМЯ: {now.strftime('%d.%m.%Y %H:%M')}"
    
    async def _get_google_calendar_section(self, state: FSMContext) -> str:
        """Секция с событиями Google Calendar"""
        now = datetime.now(TIMEZONE)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events = await self.google_service.fetch_events(state, start_of_day, end_of_day)
        
        if events is None:
            return "\nКАЛЕНДАРЬ GOOGLE: Нет подключения или произошла ошибка."
        
        if not events:
            return "\nКАЛЕНДАРЬ GOOGLE НА СЕГОДНЯ: Записей нет."
        
        return self._format_google_events(events)
    
    def _format_google_events(self, events: List[GoogleEvent]) -> str:
        """Форматирует события Google Calendar"""
        lines = ["\nКАЛЕНДАРЬ GOOGLE НА СЕГОДНЯ:"]
        formatted_events = []
        
        for event in events:
            time_str = event.format_time()
            formatted_events.append(f"{time_str} - {event.summary}")
        
        formatted_events.sort()
        lines.extend([f"- {line}" for line in formatted_events])
        return "\n".join(lines)
    
    async def _get_skyeng_section(self, state: FSMContext) -> str:
        """Секция с данными Skyeng"""
        try:
            lessons, tasks, grades = await self.skyeng_service.fetch_all_data(state)
            extended_data = await self.skyeng_service.fetch_extended_data(state)
            
            sections = []
            
            # Уроки
            sections.append(self._format_lessons(lessons, extended_data))
            
            # Задания
            sections.append(self._format_tasks(tasks))
            
            # Оценки
            sections.append(self._format_grades(grades, extended_data))
            
            return "\n".join([s for s in sections if s])
            
        except Exception as e:
            logger.error(f"Ошибка при чтении данных Skyeng: {e}")
            return "\nSKYENG: Произошла ошибка при получении данных."
    
    def _format_lessons(
        self,
        lessons: List[str],
        extended_data: Dict[str, Dict]
    ) -> str:
        """Форматирует уроки Skyeng"""
        lines = ["УРОКИ SKYENG НА СЕГОДНЯ:"]
        
        if lessons:
            lines[0] += " " + '\n- '.join(lessons)
        else:
            lines[0] += " Уроков нет."
        
        # Добавляем запланированные уроки по математике
        math_data = extended_data.get('math', {})
        if math_data.get('scheduled_lessons'):
            lines.append("\nЗАПЛАНИРОВАННЫЕ УРОКИ ПО МАТЕМАТИКЕ:")
            for lesson in math_data['scheduled_lessons'][:2]:
                lines.append(f"- {lesson.get('time', 'Время не указано')}: {lesson.get('title', 'Урок')}")
        
        return "\n".join(lines)
    
    def _format_tasks(self, tasks: List[str]) -> str:
        """Форматирует задания Skyeng"""
        lines = ["ДОМАШНИЕ ЗАДАНИЯ SKYENG (дедлайн сегодня/завтра):"]
        
        if tasks:
            lines[0] += " " + '\n- '.join(tasks)
        else:
            lines[0] += " Срочных заданий нет."
        
        return "\n".join(lines)
    
    def _format_grades(
        self,
        grades: List[str],
        extended_data: Dict[str, Dict]
    ) -> str:
        """Форматирует оценки Skyeng"""
        lines = ["СРЕДНИЙ БАЛЛ SKYENG:"]
        
        if grades:
            lines[0] += " " + '\n- '.join(grades)
        else:
            lines[0] += " Оценок пока нет."
        
        # Добавляем оценки за тесты по математике
        math_data = extended_data.get('math', {})
        if math_data.get('test_scores'):
            lines.append("\nОЦЕНКИ ЗА ТЕСТЫ ПО МАТЕМАТИКЕ:")
            for score in math_data['test_scores'][:3]:
                lines.append(f"- {score}")
        
        # Добавляем прогресс по профориентации
        cg_data = extended_data.get('career_guidance', {})
        if cg_data.get('program_progress'):
            lines.append(f"\nПРОГРЕСС ПО ПРОФОРИЕНТАЦИИ: {cg_data['program_progress']}")
        
        # Добавляем оценки за ДЗ по профориентации
        if cg_data.get('homework_scores'):
            lines.append("\nОЦЕНКИ ЗА ДЗ ПО ПРОФОРИЕНТАЦИИ:")
            for score in cg_data['homework_scores'][:3]:
                lines.append(f"- {score}")
        
        # Добавляем информацию о допуске к экзамену
        if math_data.get('exam_access_info'):
            lines.append(f"\nДОПУСК К ЭКЗАМЕНУ ПО МАТЕМАТИКЕ: {math_data['exam_access_info']}")
        
        return "\n".join(lines)
