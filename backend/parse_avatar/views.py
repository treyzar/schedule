# parse_avatar/views.py

import requests
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from parse_avatar.services import SkyengParsingService, SUBJECTS_CONFIG

# Настраиваем логирование для отладки
logger = logging.getLogger(__name__)


def get_skyeng_session(session_cookies: Optional[Dict] = None) -> requests.Session:
    """
    Создаёт и настраивает сессию для работы с Skyeng.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'origin': 'https://id.skyeng.ru',
        'referer': 'https://id.skyeng.ru/',
    })
    
    if session_cookies:
        session.cookies.update(session_cookies)
    
    return session


def find_csrf_token(soup):
    """
    Ищет CSRF-токен в HTML-коде страницы Skyeng.
    """
    csrf_input = soup.find("input", {"name": "csrfToken"})
    if csrf_input and csrf_input.get("value"):
        return csrf_input.get("value")
    return None

class SkyengLoginView(APIView):
    """
    Обрабатывает логин в Skyeng и сохраняет cookie в сессию Django.
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                "status": "error",
                "message": "Необходимо указать логин и пароль"
            }, status=400)

        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                'origin': 'https://id.skyeng.ru',
                'referer': 'https://id.skyeng.ru/login',
            })

            # ШАГ 1: Получаем CSRF-токен
            login_page_url = "https://id.skyeng.ru/login"
            login_page_response = session.get(login_page_url)
            login_page_response.raise_for_status()
            soup = BeautifulSoup(login_page_response.text, "html.parser")
            
            csrf_token = find_csrf_token(soup)
            if not csrf_token:
                logger.error(f"CSRF-токен не найден на странице входа. HTML: {login_page_response.text[:500]}")
                return Response({"status": "error", "message": "Не удалось найти CSRF-токен"}, status=400)
            
            logger.info(f"CSRF-токен найден: {csrf_token[:10]}...")

            # ШАГ 2: Логинимся
            login_submit_url = "https://id.skyeng.ru/frame/login-submit"
            login_data = {
                "username": username,
                "password": password,
                "csrfToken": csrf_token,
            }
            login_headers = session.headers.copy()
            login_headers['X-CSRF-Token'] = csrf_token

            response_submit = session.post(login_submit_url, data=login_data, headers=login_headers)
            response_submit.raise_for_status()

            # ШАГ 3: Следуем за редиректом SSO (Ключевой шаг)
            try:
                login_result = response_submit.json()
                if login_result.get("success") and login_result.get("redirect"):
                    redirect_url = login_result.get("redirect")
                    logger.info(f"Успешный вход! Следуем по SSO редиректу: {redirect_url}")
                    # Этот запрос обновит cookie в нашей сессии
                    session.get(redirect_url, allow_redirects=True)
                else:
                    logger.error(f"Вход не удался. Ответ от Skyeng: {login_result}")
                    return Response({"status": "error", "message": "Вход не удался, неверный логин или пароль"}, status=401)
            except ValueError:
                logger.error(f"Ответ от Skyeng - не JSON. Ответ: {response_submit.text}")
                return Response({"status": "error", "message": "Неожиданный ответ от сервера Skyeng"}, status=500)

            # ШАГ 4: Сохраняем ТОЛЬКО словарь с cookie, а не весь объект Session
            user_cookies = session.cookies.get_dict()
            request.session['skyeng_cookies'] = user_cookies
            logger.info(f"Cookie успешно сохранены в сессию Django. Ключи: {list(user_cookies.keys())}")

            return Response({
                "status": "success",
                "message": "Вход выполнен успешно, сессия сохранена.",
                "cookies_saved": list(user_cookies.keys())
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка при входе: {e}", exc_info=True)
            return Response({"status": "error", "message": f"Произошла сетевая ошибка: {str(e)}"}, status=500)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при входе: {e}", exc_info=True)
            return Response({"status": "error", "message": f"Произошла непредвиденная ошибка: {str(e)}"}, status=500)


class SkyengAuthStatusView(APIView):
    """
    Проверка статуса авторизации в Skyeng.
    """
    def get(self, request):
        if 'skyeng_cookies' not in request.session:
            return Response({
                'is_authenticated': False,
                'username': None,
                'last_login': None
            })

        # Проверяем валидность cookie
        session_cookies = request.session.get('skyeng_cookies', {})
        username = request.session.get('skyeng_username', None)
        last_login = request.session.get('skyeng_last_login', None)
        
        # Пытаемся сделать тестовый запрос для проверки валидности сессии
        try:
            test_session = get_skyeng_session(session_cookies)
            test_url = "https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=english"
            response = test_session.get(test_url, timeout=5)
            
            is_valid = response.status_code == 200
            
            return Response({
                'is_authenticated': is_valid,
                'username': username,
                'last_login': last_login,
                'session_valid': is_valid
            })
        except Exception as e:
            logger.error(f"Ошибка проверки сессии Skyeng: {e}")
            return Response({
                'is_authenticated': False,
                'username': username,
                'last_login': last_login,
                'session_valid': False,
                'error': str(e)
            })


class SkyengLogoutView(APIView):
    """
    Выход из Skyeng (очистка сессии).
    """
    def post(self, request):
        if 'skyeng_cookies' in request.session:
            del request.session['skyeng_cookies']
        if 'skyeng_username' in request.session:
            del request.session['skyeng_username']
        if 'skyeng_last_login' in request.session:
            del request.session['skyeng_last_login']
        request.session.save()
        
        return Response({'success': True, 'message': 'Выполнен выход из Skyeng'})


class SkyengLessonsView(APIView):
    """
    Получение списка уроков пользователя за указанный период.
    """
    def get(self, request):
        if 'skyeng_cookies' not in request.session:
            return Response({
                'error': 'Вы не авторизованы в Skyeng. Пожалуйста, выполните вход.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Получаем даты из query параметров
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        # Если даты не указаны, берём текущий месяц
        if not start_date_str or not end_date_str:
            now = datetime.now()
            start_date = now.replace(day=1)
            end_date = now
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)

        session_cookies = request.session['skyeng_cookies']
        lessons = []
        errors = []

        try:
            data_session = get_skyeng_session(session_cookies)
            
            # Запрашиваем данные по всем предметам
            subjects = ['physics', 'math', 'russian', 'english', 'chemistry', 'biology', 'history', 'social']
            
            for subject in subjects:
                try:
                    url = f"https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum={subject}"
                    response = data_session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        subject_lessons = self._extract_lessons(data, subject, start_date, end_date)
                        lessons.extend(subject_lessons)
                        logger.info(f"✅ Получено {len(subject_lessons)} уроков по предмету '{subject}'")
                    else:
                        logger.warning(f"⚪ Предмет '{subject}' вернул статус {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка при получении уроков по предмету '{subject}': {e}")
                    errors.append({'subject': subject, 'error': str(e)})

            # Сортируем уроки по дате
            lessons.sort(key=lambda x: x.get('start_time', ''), reverse=True)

            return Response({
                'lessons': lessons,
                'total': len(lessons),
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'errors': errors
            })

        except Exception as e:
            logger.error(f"Ошибка при получении уроков: {e}", exc_info=True)
            return Response({
                'error': f'Произошла ошибка при получении уроков: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _extract_lessons(self, data: Dict, subject: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Извлекает уроки из ответа API Skyeng.
        """
        lessons = []
        
        try:
            # Извлекаем данные из stream
            stream_data = data.get('stream', {})
            if stream_data:
                lessons_list = stream_data.get('lessons', [])
                for lesson in lessons_list:
                    lesson_date_str = lesson.get('date') or lesson.get('start_time')
                    if not lesson_date_str:
                        continue
                    
                    try:
                        lesson_date = datetime.fromisoformat(lesson_date_str.replace('Z', '+00:00'))
                        if start_date <= lesson_date <= end_date:
                            lessons.append({
                                'id': lesson.get('id') or lesson.get('lesson_id'),
                                'subject': subject,
                                'title': lesson.get('title') or lesson.get('topic') or f'Урок по {subject}',
                                'start_time': lesson_date_str,
                                'end_time': lesson.get('end_time'),
                                'duration': lesson.get('duration'),
                                'teacher': lesson.get('teacher', {}).get('name', 'Неизвестно'),
                                'status': lesson.get('status') or lesson.get('lesson_status', 'scheduled'),
                                'room': lesson.get('room') or lesson.get('classroom'),
                                'homework': lesson.get('homework'),
                                'type': 'skyeng_lesson'
                            })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Ошибка парсинга даты урока: {e}")
                        continue

            # Извлекаем данные из program
            program_data = data.get('program', {})
            if program_data:
                # Дополнительные данные программы
                pass
                
        except Exception as e:
            logger.error(f"Ошибка извлечения уроков: {e}")
        
        return lessons


class SkyengActivitiesView(APIView):
    """
    Получение всех активностей пользователя (уроки, домашние задания, тесты).
    """
    def get(self, request):
        if 'skyeng_cookies' not in request.session:
            return Response({
                'error': 'Вы не авторизованы в Skyeng. Пожалуйста, выполните вход.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            now = datetime.now()
            start_date = now - timedelta(days=30)  # По умолчанию 30 дней
            end_date = now
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)

        session_cookies = request.session['skyeng_cookies']
        activities = []
        errors = []

        try:
            data_session = get_skyeng_session(session_cookies)
            
            # Получаем уроки
            lessons_response = self._get_all_lessons(data_session, start_date, end_date)
            activities.extend(lessons_response)
            
            # Получаем домашние задания
            homework_response = self._get_homework(data_session, start_date, end_date)
            activities.extend(homework_response)
            
            # Сортируем по дате
            activities.sort(key=lambda x: x.get('date') or x.get('start_time', ''), reverse=True)

            return Response({
                'activities': activities,
                'total': len(activities),
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'errors': errors
            })

        except Exception as e:
            logger.error(f"Ошибка при получении активностей: {e}", exc_info=True)
            return Response({
                'error': f'Произошла ошибка при получении активностей: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_all_lessons(self, session: requests.Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Получает все уроки."""
        lessons = []
        subjects = ['physics', 'math', 'russian', 'english', 'chemistry', 'biology', 'history', 'social']
        
        for subject in subjects:
            try:
                url = f"https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum={subject}"
                response = session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Используем тот же метод извлечения, что и в SkyengLessonsView
                    view = SkyengLessonsView()
                    subject_lessons = view._extract_lessons(data, subject, start_date, end_date)
                    lessons.extend(subject_lessons)
            except Exception as e:
                logger.error(f"Ошибка получения уроков по {subject}: {e}")
        
        return lessons

    def _get_homework(self, session: requests.Session, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Получает домашние задания."""
        homework_list = []
        # Здесь можно добавить парсинг домашних заданий
        # Пока заглушка для примера структуры
        logger.info("Парсинг домашних заданий будет добавлен в следующей версии")
        return homework_list


class SkyengAllSubjectsView(APIView):
    """
    Получает данные по всем предметам, используя новый сервис парсинга.
    """
    def get(self, request):
        if 'skyeng_cookies' not in request.session:
            return Response({
                'error': 'Вы не авторизованы. Пожалуйста, выполните вход сначала.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        user_cookies = request.session['skyeng_cookies']
        logger.info(f"Используем сохраненные cookie. Ключи: {list(user_cookies.keys())}")

        try:
            # Создаем сессию с cookies
            from parse_avatar.views import get_skyeng_session
            data_session = get_skyeng_session(user_cookies)
            
            # Используем новый сервис парсинга
            parsing_service = SkyengParsingService(session=data_session)
            
            # Парсим все предметы
            results = parsing_service.parse_all_subjects(user=request.user)
            
            logger.info(f"✅ Парсинг завершён: {len(results['success'])} успешно, "
                       f"{len(results['empty'])} пустых, {len(results['errors'])} ошибок")
            
            # Формируем ответ для frontend
            subjects = []
            for item in results['success']:
                subject = {
                    'subject_key': item['subject_key'],
                    'subject_name': item['subject_name'],
                    'has_active_program': item.get('has_stream') or item.get('has_program'),
                    'stream': item.get('has_stream'),
                    'program': item.get('has_program'),
                    'modules_count': item.get('modules_count', 0),
                    'metrics': self._normalize_metrics(item.get('metrics', {})),
                }
                subjects.append(subject)
            
            return Response({
                'success': True,
                'subjects': subjects,
                'total': len(subjects),
                'empty_count': len(results['empty']),
                'error_count': len(results['errors']),
            })
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге всех предметов: {e}", exc_info=True)
            return Response({
                'error': f'Ошибка при парсинге: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _normalize_metrics(self, metrics: Dict) -> Dict:
        """Нормализует метрики для frontend"""
        if not metrics:
            return {}
        
        # Собираем все возможные метрики
        lessons_current = metrics.get('lessons_current', 0)
        lessons_total = metrics.get('lessons_total', 0)
        
        # Прогресс
        progress = 0
        if lessons_total > 0:
            progress = round((lessons_current / lessons_total) * 100, 2)
        
        return {
            'lessons_current': lessons_current,
            'lessons_total': lessons_total,
            'lessons_rating': metrics.get('lessons_rating') or metrics.get('ai_lessons_rating'),
            'homework_current': metrics.get('homework_current', 0) or metrics.get('drilling_current', 0),
            'homework_total': metrics.get('homework_total', 0) or metrics.get('drilling_total', 0),
            'homework_rating': metrics.get('homework_rating'),
            'tests_current': metrics.get('tests_current', 0) or metrics.get('stt_current', 0),
            'tests_total': metrics.get('tests_total', 0) or metrics.get('stt_total', 0),
            'tests_rating': metrics.get('tests_rating'),
            'progress_percentage': progress,
        }


class SkyengSubjectsDetailView(APIView):
    """
    Получает детальную информацию по конкретному предмету.
    GET /parse_avatar/subjects/{subject_key}/
    """
    def get(self, request, subject_key):
        if 'skyeng_cookies' not in request.session:
            return Response({
                'error': 'Вы не авторизованы.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if subject_key not in SUBJECTS_CONFIG:
            return Response({
                'error': f'Предмет "{subject_key}" не найден.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user_cookies = request.session['skyeng_cookies']
            data_session = get_skyeng_session(user_cookies)
            
            parsing_service = SkyengParsingService(session=data_session)
            
            # Получаем данные из API
            config = SUBJECTS_CONFIG[subject_key]
            if not config['url']:
                return Response({
                    'error': 'Для этого предмета нет API.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Парсим и сохраняем
            results = parsing_service.parse_all_subjects(user=request.user)
            summary = parsing_service.get_subjects_summary(user=request.user)
            
            # Находим нужный предмет
            subject_data = next((s for s in summary if s['subject_key'] == subject_key), None)
            
            if not subject_data:
                return Response({
                    'error': 'Данные по предмету не найдены.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(subject_data)
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге предмета {subject_key}: {e}", exc_info=True)
            return Response({
                'error': f'Ошибка при парсинге: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

