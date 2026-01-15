import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# Создание папки для сохранения данных
DATA_FOLDER = "skyeng_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

def save_json(data, filename):
    """
    Сохраняет данные в JSON файл с отступами для читаемости
    """
    filepath = os.path.join(DATA_FOLDER, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ Данные сохранены в {filepath}")

def save_html(content, filename):
    """
    Сохраняет HTML для отладки
    """
    filepath = os.path.join(DATA_FOLDER, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📄 HTML сохранён в {filepath}")

def try_parse_json(response):
    """
    Пытается распарсить ответ как JSON, если не получается — возвращает None
    """
    try:
        if response.headers.get('content-type', '').startswith('application/json'):
            return response.json()
        else:
            # Пробуем всё равно распарсить (вдруг сервер ошибся в Content-Type)
            return response.json()
    except:
        print(f"⚠️ Ответ не является JSON, сохраняю как HTML")
        return None

def extract_subject_name(url):
    """
    Извлекает имя предмета из URL для использования в имени файла
    Например: https://avatar.skyeng.ru/student/subject/math -> math
    """
    # Убираем trailing slash
    url = url.rstrip('/')
    # Извлекаем последнюю часть пути
    match = re.search(r'/([^/]+)$', url)
    if match:
        return match.group(1)
    return "unknown_subject"

# Основная сессия
session = requests.Session()

# Настройки
USERNAME = "ivan.khristoforov@sinhub.ru"
PASSWORD = "jA6vW0eA3ydE1dK9"

try:
    # 1. Получение страницы логина и CSRF-токена
    print("🔑 Получаю страницу логина...")
    login_page_url = "https://id.skyeng.ru/login"
    login_page_response = session.get(login_page_url, timeout=10)
    login_page_response.raise_for_status()
    
    # Сохраняем HTML страницы логина для отладки
    save_html(login_page_response.text, "login_page.html")
    
    soup = BeautifulSoup(login_page_response.text, 'html.parser')
    
    # Извлечение CSRF-токена (все варианты)
    csrf_token = None
    csrf_input = soup.find("input", {"name": "csrfToken"})
    if csrf_input:
        csrf_token = csrf_input.get("value")
    
    if not csrf_token:
        meta_tag = (
            soup.find("meta", {"name": "csrf-token"})
            or soup.find("meta", {"name": "csrf_token"})
            or soup.find("meta", {"name": "_csrf"})
        )
        if meta_tag:
            csrf_token = meta_tag.get("content")
    
    if not csrf_token:
        csrf_token = session.cookies.get("csrftoken") or session.cookies.get("XSRF-TOKEN")
    
    if not csrf_token:
        raise ValueError("❌ Не удалось найти CSRF-токен")
    
    print(f"✅ CSRF-токен получен: {csrf_token[:10]}...")

    # 2. Выполнение входа
    print("🔐 Выполняю вход...")
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfToken": csrf_token,
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": login_page_url,
        "X-CSRF-Token": csrf_token,
    }
    
    login_response = session.post(
        "https://id.skyeng.ru/frame/login-submit",
        data=login_data,
        headers=headers,
        timeout=10,
        allow_redirects=True
    )
    
    # Сохраняем ответ от login-submit
    login_json = try_parse_json(login_response)
    if login_json:
        save_json(login_json, "login_response.json")
    else:
        save_html(login_response.text, "login_response.html")
    
    if login_response.status_code not in [200, 302]:
        raise Exception(f"❌ Ошибка авторизации. Статус: {login_response.status_code}")
    
    print("✅ Вход выполнен успешно")

    # 3. Получение списка URL от пользователя
    print("\n📥 Введите ссылки на предметы (каждая с новой строки).")
    print("Для завершения ввода оставьте строку пустой и нажмите Enter.")
    
    subject_urls = []
    while True:
        url = input("URL: ").strip()
        if not url:
            break
        # Валидация URL
        if "avatar.skyeng.ru/student/subject/" in url:
            subject_urls.append(url)
            print(f"✅ Добавлено: {url}")
        else:
            print(f"❌ Неверный формат URL: {url}")
    
    if not subject_urls:
        raise ValueError("❌ Не указано ни одного URL")
    
    print(f"\n✨ Будет обработано {len(subject_urls)} предметов")

    # 4. Обработка каждого предмета
    for url in subject_urls:
        subject_name = extract_subject_name(url)
        display_name = " ".join(word.capitalize() for word in subject_name.split('_'))
        
        print(f"\n📚 Получаю данные по предмету: {display_name}")
        
        response = session.get(
            url,
            headers=headers,
            timeout=10
        )
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{subject_name}_{timestamp}"
        
        # Пробуем сохранить как JSON
        subject_data = try_parse_json(response)
        if subject_data:
            save_json(subject_data, f"{base_filename}.json")
        else:
            # Сохраняем HTML
            save_html(response.text, f"{base_filename}.html")
            
            # Попытка найти JSON в script тегах
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tags = soup.find_all('script')
            
            for i, script in enumerate(script_tags):
                script_content = script.string
                if script_content and ('window.__INITIAL_STATE__' in script_content or 'window.__DATA__' in script_content):
                    json_match = re.search(r'\{.*\}', script_content, re.DOTALL)
                    if json_match:
                        try:
                            initial_data = json.loads(json_match.group())
                            save_json(initial_data, f"{base_filename}_script_data.json")
                            print(f"💾 Найдены данные в script теге #{i}")
                        except:
                            pass
    
    # 5. Сохранение cookies и общих данных
    print("\n💾 Сохраняю cookies...")
    cookies_dict = session.cookies.get_dict()
    save_json(cookies_dict, "session_cookies.json")

    print(f"\n✨ Все данные сохранены в папку: {os.path.abspath(DATA_FOLDER)}")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    # Сохраняем ошибку
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "error": str(e),
        "response_status": login_response.status_code if 'login_response' in locals() else None,
        "response_text": login_response.text[:500] if 'login_response' in locals() else None
    }
    save_json(error_data, "error.json")
    if 'login_response' in locals():
        save_html(login_response.text, "error_login_response.html")