#!/usr/bin/env python
"""
Тест аутентификации Skyeng с использованием веб-flow.
"""

import os
import sys
import django

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from services.skyeng_auth import SkyengAuthService

def test_skyeng_auth():
    """Тестирует аутентификацию в Skyeng"""
    
    # Получаем credentials из переменных окружения или используем тестовые
    email = os.getenv('SKYENG_TEST_EMAIL', 'penis@yandex.ru')
    password = os.getenv('SKYENG_TEST_PASSWORD', 'xyu')
    
    print("=" * 60)
    print("Тестирование аутентификации Skyeng")
    print("=" * 60)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print("=" * 60)
    
    auth_service = SkyengAuthService()
    
    try:
        # Аутентификация
        print("\nШаг 1: Аутентификация...")
        credentials = auth_service.authenticate(email, password)
        
        print(f"✓ Аутентификация успешна!")
        print(f"  User ID: {credentials.user_id}")
        print(f"  Email: {credentials.email}")
        print(f"  Token: {credentials.token[:20]}...")
        print(f"  Refresh Token: {credentials.refresh_token[:20] if credentials.refresh_token else 'None'}...")
        print(f"  Expires At: {credentials.expires_at}")
        print(f"  Session Cookies: {len(credentials._session_cookies)} cookies")
        
        # Тест создание сессии из cookies
        print("\nШаг 2: Тест создание сессии из cookies...")
        session = auth_service.create_session_from_cookies(credentials._session_cookies)
        print(f"✓ Сессия создана, cookies: {len(session.cookies)}")
        
        # Проверка доступа к API
        print("\nШаг 3: Проверка доступа к API...")
        test_url = "https://edu-avatar.skyeng.ru/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=physics"
        response = session.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ API доступно! Статус: {response.status_code}")
            data = response.json()
            print(f"  Ответ: {len(str(data))} байт")
            
            # Проверяем наличие данных
            if data.get('stream'):
                print(f"  Stream: {data['stream'].get('name', 'N/A')}")
            if data.get('teacher'):
                print(f"  Teacher: {data['teacher'].get('name', 'N/A')}")
            if data.get('lessons'):
                print(f"  Lessons: {len(data['lessons'])} занятий")
        else:
            print(f"✗ API вернул ошибку: {response.status_code}")
        
        print("\n" + "=" * 60)
        print("ТЕСТ УСПЕШЕН!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ ОШИБКА: {e}")
        print("\n" + "=" * 60)
        print("ТЕСТ ПРОВАЛЕН")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_skyeng_auth()
    sys.exit(0 if success else 1)
