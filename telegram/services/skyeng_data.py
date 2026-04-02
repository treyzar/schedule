"""
Сервис для работы с данными Skyeng
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

import aiohttp
import pytz
from bs4 import BeautifulSoup
from aiogram.fsm.context import FSMContext

from .skyeng_auth import SkyengAuthService
from ..constants import (
    SUBJECTS_MAP,
    SPECIAL_SUBJECTS,
    MAX_RECENT_SCORES,
    REQUEST_TIMEOUT_MEDIUM,
)

logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone('Europe/Moscow')


class SkyengDataService:
    """Сервис для получения данных из Skyeng"""
    
    def __init__(self):
        self.auth_service = SkyengAuthService()
    
    async def fetch_all_data(
        self,
        state: FSMContext
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Получает все данные Skyeng (уроки, задания, оценки).
        
        Args:
            state: Состояние FSM
            
        Returns:
            Tuple с (lessons, tasks, grades)
        """
        session = await self._get_session(state)
        if not session:
            return [], [], []
        
        try:
            lessons, tasks, grades = await asyncio.gather(
                self._fetch_lessons(session),
                self._fetch_tasks(session),
                self._fetch_grades(session),
            )
            return lessons, tasks, grades
        finally:
            if session and not session.closed:
                await session.close()
    
    async def fetch_extended_data(
        self,
        state: FSMContext
    ) -> Dict[str, Dict]:
        """
        Получает расширенные данные для специальных предметов.
        
        Args:
            state: Состояние FSM
            
        Returns:
            Dict с данными по предметам
        """
        session = await self._get_session(state)
        if not session:
            return {}
        
        try:
            extended_data = {}
            for subject_enum in SPECIAL_SUBJECTS:
                data = await self._fetch_subject_page_data(session, subject_enum)
                if data:
                    extended_data[subject_enum] = data
            return extended_data
        finally:
            if session and not session.closed:
                await session.close()
    
    async def _get_session(self, state: FSMContext) -> Optional[aiohttp.ClientSession]:
        """Получает сессию Skyeng из состояния"""
        data = await state.get_data()
        username = data.get('skyeng_user')
        password = data.get('skyeng_pass')
        
        if not username or not password:
            return None
        
        return await self.auth_service.async_login(username, password)
    
    async def _fetch_lessons(self, session: aiohttp.ClientSession) -> List[str]:
        """Получает уроки на сегодня"""
        output = []
        now = datetime.now(TIMEZONE).date()
        
        tasks = []
        for subj_enum in SUBJECTS_MAP.values():
            if subj_enum not in SPECIAL_SUBJECTS:
                url = f"https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum={subj_enum}"
                tasks.append(session.get(url))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception) or resp.status != 200:
                continue
            
            subj_name = list(SUBJECTS_MAP.keys())[i]
            data = await resp.json()
            all_modules = data.get('schedule', {}).get('open', []) + data.get('schedule', {}).get('closed', [])
            
            for m in all_modules:
                for l in m.get('lessons', []):
                    begin_at_str = l.get('beginAt')
                    if begin_at_str:
                        try:
                            begin_dt = datetime.fromisoformat(begin_at_str).astimezone(TIMEZONE)
                            if begin_dt.date() == now:
                                output.append(f"{begin_dt.strftime('%H:%M')} - {subj_name} ({l.get('title', 'Урок')})")
                        except:
                            continue
        
        output.sort()
        return output
    
    async def _fetch_tasks(self, session: aiohttp.ClientSession, days: int = 1) -> List[str]:
        """Получает домашние задания с дедлайном"""
        output = []
        now = datetime.now(TIMEZONE).date()
        
        for subj_name, subj_enum in SUBJECTS_MAP.items():
            if subj_enum in SPECIAL_SUBJECTS:
                continue
            
            url = f"https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum={subj_enum}"
            
            try:
                async with session.get(url, timeout=REQUEST_TIMEOUT_MEDIUM) as resp:
                    if resp.status != 200:
                        continue
                    
                    data = await resp.json()
                    all_modules = data.get('schedule', {}).get('open', []) + data.get('schedule', {}).get('closed', [])
                    
                    for m in all_modules:
                        for l in m.get('lessons', []):
                            hw = l.get('homework')
                            if hw and hw.get('score') is None and l.get('deadlineAt'):
                                try:
                                    dl = datetime.fromisoformat(l['deadlineAt']).astimezone(TIMEZONE).date()
                                    if now <= dl <= now + timedelta(days=days):
                                        output.append(f"{subj_name}: {l['title']} (до {dl.strftime('%d.%m')})")
                                except:
                                    continue
            except Exception as e:
                logger.warning(f"Ошибка получения заданий по {subj_name}: {e}")
        
        return output
    
    async def _fetch_grades(self, session: aiohttp.ClientSession) -> List[str]:
        """Получает средние оценки по предметам"""
        output = []
        
        for subj_name, subj_enum in SUBJECTS_MAP.items():
            if subj_enum in SPECIAL_SUBJECTS:
                continue
            
            url = f"https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum={subj_enum}"
            
            try:
                async with session.get(url, timeout=REQUEST_TIMEOUT_MEDIUM) as resp:
                    if resp.status != 200:
                        continue
                    
                    data = await resp.json()
                    all_modules = data.get('schedule', {}).get('open', []) + data.get('schedule', {}).get('closed', [])
                    
                    scores = []
                    for m in all_modules:
                        for l in m.get('lessons', []):
                            hw = l.get('homework')
                            if hw and hw.get('score') is not None:
                                try:
                                    scores.append(float(hw['score']))
                                except:
                                    pass
                    
                    if scores:
                        avg = sum(scores) / len(scores)
                        output.append(f"{subj_name}: {avg:.2f}")
                        
            except Exception as e:
                logger.warning(f"Ошибка получения оценок по {subj_name}: {e}")
        
        return output
    
    async def _fetch_subject_page_data(
        self,
        session: aiohttp.ClientSession,
        subject_enum: str
    ) -> Dict:
        """Получает расширенные данные со страницы предмета"""
        try:
            url = f"https://avatar.skyeng.ru/student/subject/{subject_enum}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            
            async with session.get(url, headers=headers, timeout=REQUEST_TIMEOUT_MEDIUM) as response:
                if response.status != 200:
                    return {}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                data = {}
                
                if subject_enum == "career_guidance":
                    data = self._parse_career_guidance(soup)
                elif subject_enum == "math":
                    data = self._parse_math(soup)
                
                return data
                
        except Exception as e:
            logger.error(f"Ошибка получения данных страницы {subject_enum}: {e}")
            return {}
    
    def _parse_career_guidance(self, soup: BeautifulSoup) -> Dict:
        """Парсит данные профориентации"""
        import re
        
        data = {
            'program_progress': None,
            'homework_scores': []
        }
        
        # Поиск прогресса
        progress_elem = soup.find(
            ['div', 'span'],
            class_=lambda x: x and any(word in x.lower() for word in ['progress', 'percent', 'progress-bar'])
        )
        
        if progress_elem:
            progress_text = progress_elem.get_text(strip=True)
            match = re.search(r'(\d+\.?\d*)\s*%', progress_text)
            if match:
                data['program_progress'] = f"{match.group(1)}%"
        
        # Поиск оценок за ДЗ
        score_elements = soup.find_all(
            ['div', 'span'],
            class_=lambda x: x and any(word in x.lower() for word in ['score', 'grade', 'mark', 'homework'])
        )
        
        for elem in score_elements:
            text = elem.get_text(strip=True)
            if re.search(r'\d', text) and len(text) < 20:
                data['homework_scores'].append(text)
        
        return data
    
    def _parse_math(self, soup: BeautifulSoup) -> Dict:
        """Парсит данные математики"""
        import re
        
        data = {
            'test_scores': [],
            'exam_access_info': None,
            'scheduled_lessons': []
        }
        
        # Оценки за тесты
        test_elements = soup.find_all(
            ['div', 'span'],
            text=lambda x: x and 'тест' in x.lower()
        )
        
        for elem in test_elements:
            parent = elem.parent
            if parent:
                score_text = parent.get_text(strip=True)
                if re.search(r'\d', score_text):
                    data['test_scores'].append(score_text)
        
        # Допуск к экзамену
        exam_elem = soup.find(
            ['div', 'span'],
            text=lambda x: x and any(word in x.lower() for word in ['экзамен', 'допуск', 'exam'])
        )
        
        if exam_elem:
            data['exam_access_info'] = exam_elem.parent.get_text(strip=True)
        
        # Запланированные уроки
        lesson_elements = soup.find_all(
            ['div', 'article', 'section'],
            class_=lambda x: x and any(word in x.lower() for word in ['lesson', 'class', 'schedule'])
        )
        
        for elem in lesson_elements:
            time_elem = elem.find(
                ['time', 'span'],
                class_=lambda x: x and any(word in x.lower() for word in ['time', 'date'])
            )
            title_elem = elem.find(
                ['h3', 'h4', 'div'],
                class_=lambda x: x and any(word in x.lower() for word in ['title', 'name', 'lesson-name'])
            )
            
            if time_elem or title_elem:
                lesson_info = {
                    'time': time_elem.get_text(strip=True) if time_elem else 'Время не указано',
                    'title': title_elem.get_text(strip=True) if title_elem else 'Урок'
                }
                data['scheduled_lessons'].append(lesson_info)
        
        return data
