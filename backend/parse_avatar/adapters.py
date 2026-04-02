"""
Адаптеры для разных версий API Skyeng
Основано на реальной структуре данных из SKYENG_STRUCTURE_REPORT.txt
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAPIAdapter:
    """Базовый класс для адаптеров API"""
    
    API_VERSION = 'unknown'
    
    def parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсит ответ API в унифицированный формат.
        
        Returns:
            Dict с полями:
            - has_active_program: bool
            - stream: dict или None
            - program: dict или None
            - modules: list (с уроками)
            - metrics: dict
        """
        raise NotImplementedError
    
    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """Парсит ISO datetime строку"""
        if not dt_string:
            return None
        try:
            # Обработка разных форматов
            if 'Z' in dt_string:
                dt_string = dt_string.replace('Z', '+00:00')
            return datetime.fromisoformat(dt_string)
        except (ValueError, TypeError):
            return None


class APIv1ProfessionAdapter(BaseAPIAdapter):
    """
    Адаптер для API v1 - Профориентация, Soft-skill, Менеджмент проектов, Курс Сингулярности
    
    Структура ответа:
    {
        "programId": int,
        "userId": int,
        "programTitle": str,
        "stream": {
            "streamName": str,
            "curatorFullName": None,
            "streamUrl": str,
        },
        "modules": [
            {
                "moduleTitle": str,
                "moduleId": int,
                "firstEventDate": str,
                "finalWork": None,
                "lessons": [...],
                "lives": [],
                "isComplete": bool,
            },
        ],
        "metrics": {
            "lessonMetric": { "totalComplete": int, "total": int, "avgComplete": int },
            "homeworkMetric": { "totalComplete": int, "total": int, "avgScore": float },
            "courseWorkMetric": { "totalComplete": int, "total": int, "avgScore": None },
        },
        "callToAction": {...},
    }
    """
    
    API_VERSION = 'v1_profession'
    
    def parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'has_active_program': False,
            'stream': None,
            'program': None,
            'modules': [],
            'metrics': {},
        }
        
        # Программа
        if data.get('programId'):
            result['has_active_program'] = True
            result['program'] = {
                'id': data.get('programId'),
                'title': data.get('programTitle', ''),
            }
        
        # Поток
        if data.get('stream'):
            stream_data = data['stream']
            result['stream'] = {
                'title': stream_data.get('streamName', ''),
                'curator': stream_data.get('curatorFullName'),
                'url': stream_data.get('streamUrl', ''),
            }
        
        # Модули с уроками
        if data.get('modules'):
            result['modules'] = self._parse_modules(data['modules'])
        
        # Метрики
        if data.get('metrics'):
            result['metrics'] = self._parse_metrics(data['metrics'])
        
        return result
    
    def _parse_modules(self, modules_data: List[Dict]) -> List[Dict]:
        """Парсит модули с уроками"""
        modules = []
        for module in modules_data:
            parsed_module = {
                'id': module.get('moduleId'),
                'title': module.get('moduleTitle', ''),
                'first_event_date': self._parse_datetime(module.get('firstEventDate')),
                'is_complete': module.get('isComplete', False),
                'lessons': self._parse_lessons(module.get('lessons', [])),
            }
            modules.append(parsed_module)
        return modules
    
    def _parse_lessons(self, lessons_data: List[Dict]) -> List[Dict]:
        """Парсит список уроков"""
        lessons = []
        for lesson in lessons_data:
            homework_data = lesson.get('homework', {})
            parsed = {
                'id': lesson.get('streamLessonTitle'),  # Уникальный ключ
                'title': lesson.get('streamLessonTitle', ''),
                'url': lesson.get('streamLessonLink'),
                'start_at': self._parse_datetime(lesson.get('startAt')),
                'deadline': self._parse_datetime(lesson.get('deadline')),
                'completeness': lesson.get('completeness', 0),
                'score': lesson.get('score'),
                'lesson_type': lesson.get('lessonType', 'Regular'),
                'homework': {
                    'has': homework_data.get('has', False),
                    'url': homework_data.get('homeWorkUrl'),
                    'completed': homework_data.get('isHomeworkCompleted'),
                    'rate': homework_data.get('homeworkRate'),
                    'mark': homework_data.get('lastTicketMark'),
                    'status': homework_data.get('status', 'new'),
                    'deadline': self._parse_datetime(homework_data.get('homeworkDeadline')),
                } if homework_data else None,
            }
            lessons.append(parsed)
        return lessons
    
    def _parse_metrics(self, metrics_data: Dict) -> Dict:
        """Парсит метрики"""
        lesson_metric = metrics_data.get('lessonMetric', {})
        homework_metric = metrics_data.get('homeworkMetric', {})
        coursework_metric = metrics_data.get('courseWorkMetric', {})
        
        return {
            'lessons_current': lesson_metric.get('totalComplete', 0),
            'lessons_total': lesson_metric.get('total', 0),
            'lessons_rating': lesson_metric.get('avgComplete'),
            'homework_current': homework_metric.get('totalComplete', 0),
            'homework_total': homework_metric.get('total', 0),
            'homework_rating': homework_metric.get('avgScore'),
            'coursework_current': coursework_metric.get('totalComplete', 0),
            'coursework_total': coursework_metric.get('total', 0),
            'coursework_rating': coursework_metric.get('avgScore'),
        }


class APIv1PythonAdapter(BaseAPIAdapter):
    """
    Адаптер для API v1 - Python
    
    Структура отличается - данные в scheduleData
    """
    
    API_VERSION = 'v1_python'
    
    def parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'has_active_program': False,
            'stream': None,
            'program': None,
            'modules': [],
            'metrics': {},
        }
        
        # Данные в scheduleData
        schedule_data = data.get('scheduleData', {})
        
        if not schedule_data:
            return result
        
        # Программа
        if schedule_data.get('programId'):
            result['has_active_program'] = True
            result['program'] = {
                'id': schedule_data.get('programId'),
                'title': schedule_data.get('programTitle', ''),
            }
        
        # Поток
        if schedule_data.get('stream'):
            stream_data = schedule_data['stream']
            result['stream'] = {
                'title': stream_data.get('streamName', ''),
                'curator': stream_data.get('curatorFullName'),
                'url': stream_data.get('streamUrl', ''),
            }
        
        # Модули
        if schedule_data.get('modules'):
            result['modules'] = self._parse_modules(schedule_data['modules'])
        
        # Метрики
        if schedule_data.get('metrics'):
            result['metrics'] = self._parse_metrics(schedule_data['metrics'])
        
        return result
    
    def _parse_modules(self, modules_data: List[Dict]) -> List[Dict]:
        """Парсит модули с уроками"""
        modules = []
        for module in modules_data:
            parsed_module = {
                'id': module.get('moduleId'),
                'title': module.get('moduleTitle', ''),
                'first_event_date': self._parse_datetime(module.get('firstEventDate')),
                'is_complete': module.get('isComplete', False),
                'lessons': self._parse_lessons(module.get('lessons', [])),
            }
            modules.append(parsed_module)
        return modules
    
    def _parse_lessons(self, lessons_data: List[Dict]) -> List[Dict]:
        """Парсит список уроков"""
        lessons = []
        for lesson in lessons_data:
            homework_data = lesson.get('homework', {})
            parsed = {
                'title': lesson.get('streamLessonTitle', ''),
                'url': lesson.get('streamLessonLink'),
                'start_at': self._parse_datetime(lesson.get('startAt')),
                'deadline': self._parse_datetime(lesson.get('deadline')),
                'completeness': lesson.get('completeness', 0),
                'score': lesson.get('score'),
                'lesson_type': lesson.get('lessonType', 'Regular'),
                'homework': {
                    'has': homework_data.get('has', False),
                    'url': homework_data.get('homeWorkUrl'),
                    'completed': homework_data.get('isHomeworkCompleted'),
                    'rate': homework_data.get('homeworkRate'),
                    'mark': homework_data.get('lastTicketMark'),
                    'status': homework_data.get('status', 'new'),
                } if homework_data else None,
            }
            lessons.append(parsed)
        return lessons
    
    def _parse_metrics(self, metrics_data: Dict) -> Dict:
        """Парсит метрики"""
        lesson_metric = metrics_data.get('lessonMetric', {})
        homework_metric = metrics_data.get('homeworkMetric', {})
        coursework_metric = metrics_data.get('courseWorkMetric', {})
        
        return {
            'lessons_current': lesson_metric.get('totalComplete', 0),
            'lessons_total': lesson_metric.get('total', 0),
            'lessons_rating': lesson_metric.get('avgComplete'),
            'homework_current': homework_metric.get('totalComplete', 0),
            'homework_total': homework_metric.get('total', 0),
            'homework_rating': homework_metric.get('avgScore'),
            'coursework_current': coursework_metric.get('totalComplete', 0),
            'coursework_total': coursework_metric.get('total', 0),
            'coursework_rating': coursework_metric.get('avgScore'),
        }


class APIv1MathAdapter(BaseAPIAdapter):
    """
    Адаптер для API v1 - Математика
    
    Уникальная структура с журналом оценок и экзаменами
    """
    
    API_VERSION = 'v1_math'
    
    def parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'has_active_program': True,  # Математика всегда активна
            'stream': None,
            'program': None,
            'modules': [],
            'metrics': {},
            'journal': [],
            'exam_stats': {},
        }
        
        # Журнал оценок
        if data.get('journal'):
            result['journal'] = self._parse_journal(data['journal'])
        
        # Статистика экзаменов
        if data.get('journalStats'):
            result['exam_stats'] = data['journalStats']
        
        # Подготовка к экзаменам
        if data.get('examsPrepare'):
            result['exam_prepare'] = data['examsPrepare']
        
        # События (уроки)
        if data.get('eventDays'):
            result['modules'] = self._parse_event_days(data['eventDays'])
        
        # Метрики
        if data.get('metrics'):
            result['metrics'] = self._parse_metrics(data['metrics'])
        
        return result
    
    def _parse_journal(self, journal_data: List[Dict]) -> List[Dict]:
        """Парсит журнал оценок"""
        journal = []
        for entry in journal_data:
            parsed = {
                'date': entry.get('startedAt'),
                'title': entry.get('originalTitle', ''),
                'grade': entry.get('originalGrade'),
                'total_grade': entry.get('totalGrade'),
                'is_confirmed_absence': entry.get('originalIsConfirmedAbsence', False),
                'retakes': entry.get('retakes', []),
            }
            journal.append(parsed)
        return journal
    
    def _parse_event_days(self, event_days: List[Dict]) -> List[Dict]:
        """Парсит дни с событиями как модули"""
        modules = []
        for day in event_days:
            if day.get('events'):
                module = {
                    'id': day.get('date'),
                    'title': day.get('date', ''),
                    'date': day.get('date'),
                    'is_past': day.get('isPast', False),
                    'is_today': day.get('isToday', False),
                    'lessons': self._parse_events(day['events']),
                }
                modules.append(module)
        return modules
    
    def _parse_events(self, events_data: List[Dict]) -> List[Dict]:
        """Парсит события (уроки)"""
        lessons = []
        for event in events_data:
            parsed = {
                'id': event.get('id'),
                'title': event.get('title', ''),
                'started_at': event.get('startedAt'),
                'finished_at': event.get('finishedAt'),
                'status': event.get('status', ''),
                'grade': event.get('gradeCalculated'),
                'is_retake': event.get('isRetake', False),
                'preparation_percent': event.get('preparationPercent'),
                'url': event.get('place'),  # online/offline
            }
            lessons.append(parsed)
        return lessons
    
    def _parse_metrics(self, metrics_data: Dict) -> Dict:
        """Парсит метрики"""
        exam_metric = metrics_data.get('exam', {})
        score_metric = metrics_data.get('score', {})
        
        return {
            'exam_level': exam_metric.get('level'),
            'exam_progress': exam_metric.get('progress'),
            'score_level': score_metric.get('level'),
            'score_progress': score_metric.get('progress'),
        }


class APIv3EnglishAdapter(BaseAPIAdapter):
    """
    Адаптер для API v3 - English
    
    Самая сложная структура с CEFR уровнями, AI уроками, тестами
    """
    
    API_VERSION = 'v3_english'
    
    def parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'has_active_program': True,
            'stream': None,
            'program': None,
            'modules': [],
            'metrics': {},
            'cefr': {},
            'chart': {},
        }
        
        # Метрики
        if data.get('metrics'):
            result['metrics'] = self._parse_metrics(data['metrics'])
        
        # CEFR уровни
        if data.get('cefr'):
            result['cefr'] = data['cefr']
        
        # Расписание (модули с уроками)
        if data.get('schedule'):
            result['modules'] = self._parse_schedule(data['schedule'])
        
        # Диаграмма уровней
        if data.get('chart'):
            result['chart'] = data['chart']
        
        # Следующий урок
        if data.get('nextLesson'):
            result['next_lesson'] = self._parse_lesson(data['nextLesson'])
        
        return result
    
    def _parse_metrics(self, metrics_data: Dict) -> Dict:
        """Парсит метрики English"""
        ai_lessons = metrics_data.get('aiTeacherLessons', {})
        tests = metrics_data.get('tests', {})
        drilling = metrics_data.get('drilling', {})
        stt = metrics_data.get('stt', {})
        sr = metrics_data.get('sr', {})
        
        return {
            'ai_lessons_current': ai_lessons.get('current', 0),
            'ai_lessons_total': ai_lessons.get('total', 0),
            'ai_lessons_rating': ai_lessons.get('rating', {}).get('value'),
            'tests_current': tests.get('current', 0),
            'tests_total': tests.get('total', 0),
            'tests_rating': tests.get('rating', {}).get('value'),
            'drilling_current': drilling.get('current', 0),
            'drilling_total': drilling.get('total', 0),
            'stt_current': stt.get('current', 0),
            'stt_total': stt.get('total', 0),
            'sr_current': sr.get('current', 0),
            'sr_total': sr.get('total', 0),
        }
    
    def _parse_schedule(self, schedule_data: Dict) -> List[Dict]:
        """Парсит расписание (hidden + open)"""
        modules = []
        
        # Hidden модули
        for hidden_module in schedule_data.get('hidden', []):
            module = {
                'title': hidden_module.get('title', ''),
                'type': 'hidden',
                'lessons': [self._parse_lesson(lesson) for lesson in hidden_module.get('lessons', [])],
            }
            modules.append(module)
        
        # Open модули (активные)
        for open_module in schedule_data.get('open', []):
            module = {
                'title': open_module.get('title', ''),
                'type': 'open',
                'lessons': [self._parse_lesson(lesson) for lesson in open_module.get('lessons', [])],
            }
            modules.append(module)
        
        return modules
    
    def _parse_lesson(self, lesson_data: Dict) -> Dict:
        """Парсит урок"""
        return {
            'id': lesson_data.get('taskId') or lesson_data.get('streamTaskId'),
            'task_id': lesson_data.get('taskId'),
            'stream_task_id': lesson_data.get('streamTaskId'),
            'title': lesson_data.get('title', ''),
            'type': lesson_data.get('type', 'lesson'),
            'status': lesson_data.get('status', ''),
            'score': lesson_data.get('score'),
            'available_from': self._parse_datetime(lesson_data.get('availableFrom')),
            'deadline_at': self._parse_datetime(lesson_data.get('deadlineAt')),
            'completed_at': self._parse_datetime(lesson_data.get('completedAt')),
            'teacher_name': lesson_data.get('teacherName'),
            'task_url': lesson_data.get('taskUrl'),
            'record_url': lesson_data.get('recordUrl'),
            'homework': lesson_data.get('homework'),
            'joined_at': self._parse_datetime(lesson_data.get('joinedAt')),
            'disabled': lesson_data.get('disabled', False),
            'can_redo': lesson_data.get('canRedo', False),
            'passed': lesson_data.get('passed', False),
        }


class APIv2SchoolAdapter(BaseAPIAdapter):
    """
    Адаптер для API v2 - Школьные предметы (Биология, История, Физика, etc.)
    
    Структура:
    {
        "stream": { "title": str },
        "program": { "title": str },
        "metrics": {
            "lessonsMetric": { "current": int, "total": int, "rating": {...} },
            "homeworkMetric": {...},
            "journalMetric": {...},
            "testsMetric": {...},
        },
        "schedule": {
            "hidden": [...],
            "open": [
                {
                    "title": str,
                    "lessons": [...]
                }
            ]
        }
    }
    """
    
    API_VERSION = 'v2_school'
    
    def parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'has_active_program': False,
            'stream': None,
            'program': None,
            'modules': [],
            'metrics': {},
        }
        
        # Поток
        if data.get('stream'):
            result['has_active_program'] = True
            result['stream'] = {
                'title': data['stream'].get('title', ''),
            }
        
        # Программа
        if data.get('program'):
            result['has_active_program'] = True
            result['program'] = {
                'title': data['program'].get('title', ''),
            }
        
        # Модули из schedule
        if data.get('schedule'):
            result['modules'] = self._parse_schedule(data['schedule'])
        
        # Метрики
        if data.get('metrics'):
            result['metrics'] = self._parse_metrics(data['metrics'])
        
        return result
    
    def _parse_schedule(self, schedule_data: Dict) -> List[Dict]:
        """Парсит расписание (hidden + open)"""
        modules = []
        
        # Hidden модули
        for hidden_module in schedule_data.get('hidden', []):
            module = {
                'title': hidden_module.get('title', ''),
                'type': 'hidden',
                'lessons': [self._parse_lesson(lesson) for lesson in hidden_module.get('lessons', [])],
            }
            modules.append(module)
        
        # Open модули (активные)
        for open_module in schedule_data.get('open', []):
            module = {
                'title': open_module.get('title', ''),
                'type': 'open',
                'lessons': [self._parse_lesson(lesson) for lesson in open_module.get('lessons', [])],
            }
            modules.append(module)
        
        return modules
    
    def _parse_lesson(self, lesson_data: Dict) -> Dict:
        """Парсит урок"""
        homework_data = lesson_data.get('homework')
        
        return {
            'id': lesson_data.get('streamTaskId') or lesson_data.get('taskId'),
            'task_id': lesson_data.get('taskId'),
            'stream_task_id': lesson_data.get('streamTaskId'),
            'type': lesson_data.get('type', 'self_study'),
            'title': lesson_data.get('title', ''),
            'available_at': self._parse_datetime(lesson_data.get('availableAt')),
            'deadline_at': self._parse_datetime(lesson_data.get('deadlineAt')),
            'teacher_name': lesson_data.get('teacherName'),
            'task_url': lesson_data.get('taskUrl'),
            'record_url': lesson_data.get('recordUrl'),
            'score': lesson_data.get('score'),
            'completeness': lesson_data.get('completeness'),
            'homework': {
                'score': homework_data.get('score') if homework_data else None,
                'url': homework_data.get('taskUrl') if homework_data else None,
                'completeness': homework_data.get('completeness') if homework_data else None,
            } if homework_data else None,
            'joined_at': self._parse_datetime(lesson_data.get('joinedAt')),
            'closed_at': self._parse_datetime(lesson_data.get('closedAt')),
            'disabled': lesson_data.get('disabled', False),
            'can_redo': lesson_data.get('canRedo', False),
            'passed': lesson_data.get('passed', False),
        }
    
    def _parse_metrics(self, metrics_data: Dict) -> Dict:
        """Парсит метрики"""
        lessons = metrics_data.get('lessonsMetric', {})
        homework = metrics_data.get('homeworkMetric', {})
        journal = metrics_data.get('journalMetric', {})
        tests = metrics_data.get('testsMetric', {})
        
        def get_rating(rating_data):
            if rating_data:
                return rating_data.get('value')
            return None
        
        return {
            'lessons_current': lessons.get('current', 0),
            'lessons_total': lessons.get('total', 0),
            'lessons_rating': get_rating(lessons.get('rating')),
            'homework_current': homework.get('current', 0),
            'homework_total': homework.get('total', 0),
            'homework_rating': get_rating(homework.get('rating')),
            'journal_current': journal.get('current', 0),
            'journal_total': journal.get('total', 0),
            'journal_rating': get_rating(journal.get('rating')),
            'tests_current': tests.get('current', 0),
            'tests_total': tests.get('total', 0),
            'tests_rating': get_rating(tests.get('rating')),
        }


def get_adapter(subject_key: str) -> BaseAPIAdapter:
    """
    Фабричный метод для получения адаптера по предмету.
    
    Args:
        subject_key: Ключ предмета (например, 'physics', 'english', 'math')
    
    Returns:
        Соответствующий адаптер
    """
    # API v3
    if subject_key == 'english':
        return APIv3EnglishAdapter()
    
    # API v1 - разные типы
    if subject_key == 'python':
        return APIv1PythonAdapter()
    
    if subject_key == 'math':
        return APIv1MathAdapter()
    
    if subject_key in ['career_guidance', 'soft_skills', 'managment_of_project', 'lessons_about_main']:
        return APIv1ProfessionAdapter()
    
    # API v2 - школьные предметы
    if subject_key in ['biology', 'history', 'social_studies', 'physics', 'geography', 
                       'literature', 'basics_of_security', 'chemistry', 'russian']:
        return APIv2SchoolAdapter()
    
    # По умолчанию используем v2
    return APIv2SchoolAdapter()
