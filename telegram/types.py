"""
Типы данных для Telegram бота
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class SubjectEnum(str, Enum):
    """Перечисление предметов"""
    PHYSICS = "physics"
    MATH = "math"
    RUSSIAN = "russian"
    ENGLISH = "english"
    INFORMATICS = "informatics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    CAREER_GUIDANCE = "career_guidance"


class DataType(str, Enum):
    """Типы данных Skyeng"""
    LESSONS = "lessons"
    TASKS = "tasks"
    GRADES = "grades"


@dataclass
class SkyengLesson:
    """Модель урока Skyeng"""
    id: str
    subject: str
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    teacher: str = ""
    homework: Optional[Dict[str, Any]] = None


@dataclass
class SkyengTask:
    """Модель домашнего задания"""
    subject: str
    title: str
    deadline: datetime
    completed: bool = False


@dataclass
class SubjectGrade:
    """Оценка по предмету"""
    subject: str
    average_grade: float
    scores: List[float] = field(default_factory=list)


@dataclass
class MathData:
    """Расширенные данные по математике"""
    test_scores: List[str] = field(default_factory=list)
    exam_access_info: Optional[str] = None
    scheduled_lessons: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CareerGuidanceData:
    """Расширенные данные по профориентации"""
    program_progress: Optional[str] = None
    homework_scores: List[str] = field(default_factory=list)


@dataclass
class GoogleEvent:
    """Событие Google Calendar"""
    summary: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_all_day: bool = False
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'GoogleEvent':
        """Создает объект из ответа Google API"""
        start_info = data.get('start', {})
        end_info = data.get('end', {})
        
        is_all_day = 'date' in start_info
        start_time = None
        end_time = None
        
        if 'dateTime' in start_info:
            start_time = datetime.fromisoformat(start_info['dateTime'])
        elif 'date' in start_info:
            start_time = datetime.fromisoformat(start_info['date'])
            is_all_day = True
            
        if 'dateTime' in end_info:
            end_time = datetime.fromisoformat(end_info['dateTime'])
        elif 'date' in end_info:
            end_time = datetime.fromisoformat(end_info['date'])
        
        return cls(
            summary=data.get('summary', 'Без названия'),
            start_time=start_time,
            end_time=end_time,
            is_all_day=is_all_day,
            raw_data=data
        )
    
    def format_time(self) -> str:
        """Форматирует время события для отображения"""
        if self.is_all_day:
            return "Весь день"
        if self.start_time:
            return self.start_time.strftime('%H:%M')
        return "Время не указано"
