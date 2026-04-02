"""
Сервис парсинга всех предметов Skyeng
Основано на реальной структуре API
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

import requests
from django.db import transaction
from django.utils import timezone

from parse_avatar.adapters import get_adapter

logger = logging.getLogger(__name__)


# Конфигурация предметов и их API
SUBJECTS_CONFIG = {
    # API v1 - Профориентация и профессиональные предметы
    'career_guidance': {
        'name': 'Профориентация',
        'adapter': 'v1_profession',
        'url': 'https://edu-avatar.skyeng.ru/api/v1/college-student-cabinet/single-student-account/profession?subjectEnum=career_guidance',
    },
    'python': {
        'name': 'Python',
        'adapter': 'v1_python',
        'url': 'https://edu-avatar.skyeng.ru/api/v1/college-student-cabinet/single-student-account/python?subjectEnum=python',
    },
    'soft_skills': {
        'name': 'Soft Skills',
        'adapter': 'v1_profession',
        'url': 'https://edu-avatar.skyeng.ru/api/v1/college-student-cabinet/single-student-account/profession?subjectEnum=soft_skills',
    },
    'math': {
        'name': 'Математика',
        'adapter': 'v1_math',
        'url': 'https://edu-avatar.skyeng.ru/api/v1/college-student-cabinet/single-student-account/math',
    },
    'managment_of_project': {
        'name': 'Менеджмент проектов',
        'adapter': 'v1_profession',
        'url': 'https://edu-avatar.skyeng.ru/api/v1/college-student-cabinet/single-student-account/profession?subjectEnum=managment_of_project',
    },
    'lessons_about_main': {
        'name': 'Курс Сингулярности',
        'adapter': 'v1_profession',
        'url': 'https://edu-avatar.skyeng.ru/api/v1/college-student-cabinet/single-student-account/profession?subjectEnum=lessons_about_main',
    },
    'onboarding': {
        'name': 'Онбординг',
        'adapter': None,
        'url': None,  # Нет API
    },
    
    # API v2 - Школьные предметы
    'biology': {
        'name': 'Биология',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=biology',
    },
    'history': {
        'name': 'История',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=history',
    },
    'social_studies': {
        'name': 'Обществознание',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=social_studies',
    },
    'physics': {
        'name': 'Физика',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=physics',
    },
    'geography': {
        'name': 'География',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=geography',
    },
    'literature': {
        'name': 'Литература',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=literature',
    },
    'basics_of_security': {
        'name': 'Основы безопасности',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=basics_of_security',
    },
    'chemistry': {
        'name': 'Химия',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=chemistry',
    },
    'russian': {
        'name': 'Русский язык',
        'adapter': 'v2_school',
        'url': 'https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=russian',
    },
    
    # API v3 - Английский
    'english': {
        'name': 'Английский язык',
        'adapter': 'v3_english',
        'url': 'https://edu-avatar.skyeng.ru/api/v3/college-student-cabinet/single-student-account/english',
    },
}


class SkyengParsingService:
    """
    Сервис парсинга всех предметов Skyeng
    """
    
    def __init__(self, session: requests.Session, timeout: int = 30):
        self.session = session
        self.timeout = timeout
    
    def parse_all_subjects(self, user) -> Dict[str, any]:
        """
        Парсит все доступные предметы пользователя.
        
        Returns:
            Dict с результатами парсинга
        """
        results = {
            'success': [],
            'empty': [],
            'errors': [],
        }
        
        for subject_key, config in SUBJECTS_CONFIG.items():
            logger.info(f"Парсинг предмета: {config['name']}")
            
            try:
                if not config['url']:
                    logger.info(f"Предмет {config['name']} не имеет API")
                    results['empty'].append({
                        'subject_key': subject_key,
                        'subject_name': config['name'],
                        'reason': 'Нет API',
                    })
                    continue
                
                # Получаем данные из API
                data = self._fetch_subject_data(config['url'])
                
                if not data:
                    results['empty'].append({
                        'subject_key': subject_key,
                        'subject_name': config['name'],
                        'reason': 'Пустой ответ',
                    })
                    continue
                
                # Парсим данные через адаптер
                adapter = get_adapter(subject_key)
                parsed_data = adapter.parse_response(data)
                
                # Проверяем, есть ли активная программа
                has_active = parsed_data.get('has_active_program', False)
                has_modules = len(parsed_data.get('modules', [])) > 0
                
                if has_active or has_modules:
                    results['success'].append({
                        'subject_key': subject_key,
                        'subject_name': config['name'],
                        'adapter': config.get('adapter'),
                        'has_stream': bool(parsed_data.get('stream')),
                        'has_program': bool(parsed_data.get('program')),
                        'modules_count': len(parsed_data.get('modules', [])),
                        'metrics': parsed_data.get('metrics'),
                    })
                else:
                    results['empty'].append({
                        'subject_key': subject_key,
                        'subject_name': config['name'],
                        'reason': 'Нет активных программ',
                    })
                
            except Exception as e:
                logger.error(f"Ошибка парсинга {config['name']}: {e}", exc_info=True)
                results['errors'].append({
                    'subject_key': subject_key,
                    'subject_name': config['name'],
                    'error': str(e),
                })
        
        return results
    
    def _fetch_subject_data(self, url: str) -> Optional[Dict]:
        """Получает данные из API"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"API вернул 404: {url}")
                return None
            else:
                logger.warning(f"API вернул {response.status_code}: {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к {url}: {e}")
            return None
    
    def get_subjects_summary(self, user) -> List[Dict]:
        """
        Получает сводку по всем предметам пользователя.
        Возвращает данные из кэша (БД) или парсит заново.
        """
        # Для простоты возвращаем пустой список
        # В реальной реализации нужно загружать из БД
        return []
