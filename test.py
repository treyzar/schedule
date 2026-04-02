# physics.py

import json
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def find_csrf_token(soup):
    """
    Ищет CSRF-токен в HTML.
    """
    csrf_input = soup.find("input", {"name": "csrfToken"})
    if csrf_input and csrf_input.get("value"):
        return csrf_input.get("value")
    return None


class AuthenticationError(Exception):
    """Ошибка аутентификации."""
    pass


# ============================================
# ШАГ 1: Получение CSRF-токена
# ============================================

def get_csrf_token():
    """
    Создает сессию и получает CSRF-токен.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    })
    
    login_page_url = "https://id.skyeng.ru/login"
    response = session.get(login_page_url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = find_csrf_token(soup)
    
    if not csrf_token:
        raise ValueError("CSRF-токен не найден")
    
    logger.info(f"CSRF-токен получен: {csrf_token[:10]}...")
    return session, csrf_token


# ============================================
# ШАГ 2: Логин
# ============================================

def login_to_skyeng(session, csrf_token, username, password):
    """
    Выполняет вход в Skyeng.
    """
    login_submit_url = "https://id.skyeng.ru/frame/login-submit"
    login_data = {
        "username": username,
        "password": password,
        "csrfToken": csrf_token,
    }
    
    headers = {
        'User-Agent': session.headers.get('User-Agent'),
        'origin': 'https://id.skyeng.ru',
        'referer': 'https://id.skyeng.ru/login',
        'X-CSRF-Token': csrf_token,
    }
    
    response = session.post(login_submit_url, data=login_data, headers=headers)
    response.raise_for_status()
    
    login_result = response.json()
    
    if not login_result.get("success"):
        raise AuthenticationError("Неверный логин или пароль")
    
    # Обрабатываем SSO редирект
    redirect_url = login_result.get("redirect")
    if redirect_url:
        session.get(redirect_url, allow_redirects=True)
        logger.info(f"SSO редирект выполнен")
    
    logger.info("Вход выполнен успешно")
    return session


# ============================================
# ШАГ 3: Получение данных по физике
# ============================================

def get_physics_data(session):
    """
    Получает данные по физике через API.
    """
    url = "https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=physics"
    
    response = session.get(url, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    logger.info("Данные по физике получены")
    
    return data


# ============================================
# ШАГ 4: Обработка данных
# ============================================

def parse_physics_data(data):
    """
    Извлекает полезную информацию из ответа API.
    """
    result = {
        "has_active_program": False,
        "stream": None,
        "program": None,
        "teacher": None,
        "lessons": [],
        "raw_data": data
    }
    
    if data.get("stream"):
        result["has_active_program"] = True
        result["stream"] = {
            "id": data["stream"].get("id"),
            "name": data["stream"].get("name"),
            "status": data["stream"].get("status"),
        }
    
    if data.get("program"):
        result["has_active_program"] = True
        result["program"] = {
            "id": data["program"].get("id"),
            "name": data["program"].get("name"),
        }
    
    if data.get("teacher"):
        result["teacher"] = {
            "id": data["teacher"].get("id"),
            "name": data["teacher"].get("name"),
            "avatar": data["teacher"].get("avatarUrl"),
        }
    
    if data.get("lessons"):
        result["lessons"] = [
            {
                "id": lesson.get("id"),
                "title": lesson.get("title"),
                "status": lesson.get("status"),
                "date": lesson.get("date"),
            }
            for lesson in data["lessons"]
        ]
    
    return result


# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def fetch_physics(username, password):
    """
    Полный пайплайн: логин → получение данных по физике → обработка.
    """
    try:
        # Шаг 1: CSRF-токен (получаем и сессию, и токен)
        session, csrf_token = get_csrf_token()
        
        # Шаг 2: Логин
        session = login_to_skyeng(session, csrf_token, username, password)
        
        # Шаг 3: Данные по физике
        raw_data = get_physics_data(session)
        
        # Шаг 4: Обработка
        parsed_data = parse_physics_data(raw_data)
        
        return {
            "success": True,
            "data": parsed_data,
            "error": None
        }
        
    except AuthenticationError as e:
        logger.error(f"Ошибка авторизации: {e}")
        return {"success": False, "data": None, "error": str(e)}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Сетевая ошибка: {e}")
        return {"success": False, "data": None, "error": f"Сетевая ошибка: {str(e)}"}
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return {"success": False, "data": None, "error": f"Ошибка: {str(e)}"}


# ============================================
# ЗАПУСК
# ============================================

if __name__ == "__main__":
    # Пример использования
    result = fetch_physics("penis@yandex.ru", "xyu")
    print(json.dumps(result, indent=2, ensure_ascii=False))