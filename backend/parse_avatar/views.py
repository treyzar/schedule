# parse_avatar/views.py

import requests
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
import logging

# Настраиваем логирование для отладки
logger = logging.getLogger(__name__)

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


class SkyengAllSubjectsView(APIView):
    """
    Получает данные по всем предметам, используя сохраненные в сессии cookie.
    """
    def get(self, request):
        if 'skyeng_cookies' not in request.session:
            return Response({'error': 'Вы не авторизованы. Пожалуйста, выполните вход сначала.'}, status=401)

        user_cookies = request.session['skyeng_cookies']
        logger.info(f"Используем сохраненные cookie. Ключи: {list(user_cookies.keys())}")
        
        # Список всех возможных предметов в Skyeng
        subjects = ['physics', 'math', 'russian', 'english', 'chemistry', 'biology', 'history', 'social']
        
        results = {}
        errors = []

        # Создаем сессию для запроса данных
        data_session = requests.Session()
        data_session.cookies.update(user_cookies) # Загружаем cookie
        data_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        })

        for subject in subjects:
            try:
                url = f"https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum={subject}"
                response = data_session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Сохраняем, только если в ответе есть полезные данные
                    if data.get('stream') or data.get('program'):
                        results[subject] = data
                        logger.info(f"✅ Данные по предмету '{subject}' успешно получены.")
                    else:
                        logger.info(f"⚪ Для предмета '{subject}' нет активных программ.")
                else:
                    logger.warning(f"⚪ Предмет '{subject}' вернул статус {response.status_code}.")

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Ошибка при запросе данных по предмету '{subject}': {e}")
                errors.append({subject: str(e)})
        
        return Response({
            'subjects_found': list(results.keys()),
            'data': results,
            'errors': errors,
            'total_subjects_found': len(results)
        })

