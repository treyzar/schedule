"""
Middleware для проверки обязательной авторизации в Skyeng.
Перенаправляет неавторизованных пользователей на страницу /skyeng-login.
"""

import logging
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

logger = logging.getLogger(__name__)


class SkyengAuthRequiredMiddleware:
    """
    Middleware, который проверяет авторизацию в Skyeng.
    
    Если пользователь авторизован в Google, но не в Skyeng,
    он будет перенаправлен на /skyeng-login.
    
    Исключения:
    - API endpoints (возвращают 401 вместо редиректа)
    - Статус авторизации (/parse_calendar/status/, /skyeng-status/)
    - Сам /skyeng-login
    - Logout endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Пути, которые не требуют авторизации в Skyeng
        self.exempt_paths = [
            '/parse_calendar/skyeng-login/',
            '/parse_calendar/status/',
            '/parse_calendar/skyeng-status/',
            '/parse_calendar/oauth2callback/',
            '/parse_calendar/logout/',
            '/parse_calendar/skyeng-logout/',
            '/parse_calendar/authorize/',
            '/static/',
            '/favicon.ico',
        ]
        
        # API пути, которые возвращают 401 вместо редиректа
        self.api_paths = [
            '/parse_calendar/',
            '/api/',
        ]
    
    def __call__(self, request):
        # Проверяем, является ли путь исключением
        if self._is_exempt(request.path):
            return self.get_response(request)
        
        # Проверяем авторизацию в Skyeng
        requires_skyeng_auth = self._requires_skyeng_auth(request)
        
        if requires_skyeng_auth:
            # Для API возвращаем 401
            if self._is_api_path(request.path):
                return JsonResponse(
                    {
                        'error': 'Skyeng authorization required',
                        'redirect': '/skyeng-login',
                    },
                    status=401
                )
            
            # Для обычных запросов - редирект
            # Сохраняем текущий URL для возврата после авторизации
            next_url = request.get_full_path()
            redirect_url = f'{settings.FRONTEND_URL}/skyeng-login'
            if next_url and next_url != '/':
                redirect_url += f'?next={next_url}'
            
            return redirect(redirect_url)
        
        return self.get_response(request)
    
    def _is_exempt(self, path: str) -> bool:
        """Проверяет, является ли путь исключением"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def _is_api_path(self, path: str) -> bool:
        """Проверяет, является ли путь API"""
        return any(path.startswith(api) for api in self.api_paths)
    
    def _requires_skyeng_auth(self, request) -> bool:
        """
        Проверяет, требуется ли авторизация в Skyeng.
        
        Возвращает True, если:
        - Пользователь авторизован в Google (есть credentials в сессии)
        - НО не авторизован в Skyeng (нет токена в БД)
        """
        # Проверяем авторизацию в Google (сессия)
        google_authenticated = 'google_credentials' in request.session
        
        if not google_authenticated:
            # Если нет Google авторизации, не требуем Skyeng
            # (пользователь должен сначала авторизоваться в Google)
            return False
        
        # Проверяем авторизацию в Skyeng (БД)
        if request.user.is_authenticated:
            try:
                user_creds = request.user.external_credentials
                if user_creds and user_creds.has_skyeng_credentials():
                    # Проверяем, не истёк ли токен
                    if not user_creds.is_skyeng_token_expired():
                        return False
            except Exception:
                # Если ошибка при проверке, требуем авторизацию
                pass
        
        # Проверяем временные credentials (пользователь в процессе авторизации)
        if request.session.get('google_credentials_temp'):
            # Пользователь только что прошёл Google OAuth,
            # но ещё не завершил Skyeng авторизацию
            # Не требуем авторизацию на странице skyeng-login
            if request.path.startswith('/skyeng-login'):
                return False
            # На другие страницы - требуем
            return True
        
        return True
