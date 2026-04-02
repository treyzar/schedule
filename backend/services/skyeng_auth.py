"""
Сервис авторизации Skyeng API.
Версия с веб-аутентификацией через id.skyeng.ru (с CSRF-токеном).
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import timedelta
from bs4 import BeautifulSoup

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

from config import get_config
from exceptions import (
    SkyengAuthError,
    SkyengInvalidCredentialsError,
    SkyengNetworkError,
    SkyengTokenExpiredError,
    ServiceRateLimitError,
)
from shared.credentials import SkyengCredentials

logger = logging.getLogger(__name__)


class SkyengAuthService:
    """
    Сервис аутентификации в Skyeng через веб-интерфейс.

    Использует flow:
    1. Получение CSRF-токена с id.skyeng.ru
    2. Логин через /frame/login-submit
    3. SSO редирект для получения токенов API
    
    Пример использования:
        auth_service = SkyengAuthService()
        credentials = auth_service.authenticate(email, password)
    """

    def __init__(self, timeout: Optional[int] = None):
        """
        Инициализация сервиса.

        Args:
            timeout: Таймаут запросов в секундах
        """
        config = get_config()
        self.timeout = timeout or config.skyeng.timeout
        self.retry_attempts = config.skyeng.retry_attempts
        self.user_agent = config.skyeng.user_agent
        
        # URL для веб-аутентификации
        self.id_base_url = config.skyeng.id_base_url
        self.edu_base_url = config.skyeng.edu_base_url
        
        # Сессия для сохранения cookies
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8',
        })

    def _get_csrf_token(self) -> Tuple[requests.Session, str]:
        """
        Получает CSRF-токен со страницы логина.

        Returns:
            Tuple[requests.Session, str]: (сессия, csrf_token)

        Raises:
            SkyengAuthError: Если токен не найден
        """
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8',
        })

        login_page_url = f"{self.id_base_url}/login"
        
        try:
            response = session.get(login_page_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            csrf_input = soup.find("input", {"name": "csrfToken"})
            
            if not csrf_input or not csrf_input.get("value"):
                logger.error("CSRF-токен не найден на странице логина")
                raise SkyengAuthError("Не удалось получить CSRF-токен")

            csrf_token = csrf_input.get("value")
            logger.info(f"CSRF-токен получен: {csrf_token[:10]}...")
            
            return session, csrf_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении CSRF-токена: {e}")
            raise SkyengNetworkError(f"Не удалось загрузить страницу логина: {str(e)}")

    def _login_with_csrf(
        self,
        session: requests.Session,
        csrf_token: str,
        username: str,
        password: str
    ) -> requests.Session:
        """
        Выполняет вход в Skyeng с использованием CSRF-токена.

        Args:
            session: requests сессия
            csrf_token: CSRF-токен
            username: Email пользователя
            password: Пароль пользователя

        Returns:
            requests.Session с авторизованной сессией

        Raises:
            SkyengInvalidCredentialsError: Неверный логин или пароль
            SkyengAuthError: Другие ошибки аутентификации
        """
        login_submit_url = f"{self.id_base_url}/frame/login-submit"
        
        login_data = {
            "username": username,
            "password": password,
            "csrfToken": csrf_token,
        }

        headers = {
            'User-Agent': session.headers.get('User-Agent'),
            'Origin': self.id_base_url,
            'Referer': f"{self.id_base_url}/login",
            'X-CSRF-Token': csrf_token,
            'Accept': 'application/json',
        }

        try:
            response = session.post(
                login_submit_url,
                data=login_data,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            login_result = response.json()

            if not login_result.get("success"):
                logger.warning(f"Login failed: {login_result.get('message', 'Unknown error')}")
                raise SkyengInvalidCredentialsError(
                    login_result.get('message', 'Неверный логин или пароль')
                )

            # Обрабатываем SSO редирект
            redirect_url = login_result.get("redirect")
            if redirect_url:
                logger.info(f"Выполняем SSO редирект: {redirect_url[:50]}...")
                sso_response = session.get(redirect_url, allow_redirects=True, timeout=self.timeout)
                logger.info(f"SSO редирект выполнен, финальный URL: {sso_response.url[:50]}...")
                
                # Логируем все cookies после SSO
                logger.info(f"Cookies после SSO: {session.cookies.get_dict()}")

            logger.info("Вход выполнен успешно")
            return session

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during login: {e}")
            if e.response.status_code == 401:
                raise SkyengInvalidCredentialsError("Неверный логин или пароль")
            raise SkyengAuthError(f"Ошибка сервера: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during login: {e}")
            raise SkyengNetworkError(f"Ошибка сети: {str(e)}")
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise SkyengAuthError("Сервер вернул некорректный ответ")

    def _get_api_tokens_from_session(self, session: requests.Session) -> Dict[str, Any]:
        """
        Получает API токены из авторизованной сессии.

        Args:
            session: Авторизованная requests сессия

        Returns:
            Dict с токенами и данными пользователя

        Raises:
            SkyengAuthError: Если не удалось получить токены
        """
        # Логируем cookies для отладки
        cookies_dict = session.cookies.get_dict()
        logger.info(f"Cookies сессии: {list(cookies_dict.keys())}")
        
        # Пробуем получить данные через API edu-avatar
        url = f"{self.edu_base_url}/api/v2/college-student-cabinet/single-student-account/school-subject?subjectEnum=physics"
        
        try:
            response = session.get(url, timeout=self.timeout)
            
            # Если получили 200 - сессия валидна
            if response.status_code == 200:
                logger.info("Сессия валидна, API доступно")
                
                # Пробуем получить токен через внутренний эндпоинт
                token_url = f"{self.edu_base_url}/api/v2/auth/token"
                token_response = session.get(token_url, timeout=self.timeout)
                
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    logger.info("Токен получен через API")
                    return token_data
                
                # Если не удалось получить токен явно,
                # используем cookies сессии для запросов
                logger.info("Используем cookies сессии для запросов")
                return {
                    "session_cookies": cookies_dict,
                }
            
            logger.warning(f"API вернул статус: {response.status_code}")
            raise SkyengAuthError("Не удалось получить доступ к API")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting API tokens: {e}")
            raise SkyengAuthError(f"Ошибка при получении токенов: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
        reraise=True,
    )
    def _post_with_retry(
        self,
        url: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Выполняет POST запрос с retry логикой.
        """
        return self.session.post(
            url,
            json=json_data,
            headers=headers,
            timeout=self.timeout,
        )

    def authenticate(
        self,
        email: str,
        password: str
    ) -> SkyengCredentials:
        """
        Аутентификация по логину и паролю через веб-интерфейс.

        Args:
            email: Email пользователя
            password: Пароль пользователя

        Returns:
            SkyengCredentials с токенами доступа

        Raises:
            SkyengInvalidCredentialsError: Неверный логин или пароль
            SkyengNetworkError: Ошибка сети
            SkyengAuthError: Другие ошибки аутентификации
        """
        logger.info(f"Attempting Skyeng login for email: {email}")

        try:
            # Шаг 1: Получение CSRF-токена
            session, csrf_token = self._get_csrf_token()

            # Шаг 2: Логин с CSRF
            session = self._login_with_csrf(session, csrf_token, email, password)

            # Шаг 3: Получение API токенов
            token_data = self._get_api_tokens_from_session(session)

            # Создаем credentials
            return self._create_credentials_from_session(session, token_data, email)

        except (SkyengInvalidCredentialsError, SkyengNetworkError, SkyengAuthError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Skyeng auth: {e}", exc_info=True)
            raise SkyengAuthError(f'Неизвестная ошибка: {str(e)}')

    def _create_credentials_from_session(
        self,
        session: requests.Session,
        token_data: Dict[str, Any],
        email: str
    ) -> SkyengCredentials:
        """
        Создает SkyengCredentials из сессии и токенов.

        Args:
            session: Авторизованная сессия
            token_data: Данные токенов
            email: Email пользователя

        Returns:
            SkyengCredentials объект
        """
        from django.utils import timezone
        
        # Если есть явный токен в token_data
        token = token_data.get('accessToken') or token_data.get('access_token')
        refresh_token = token_data.get('refreshToken') or token_data.get('refresh_token')
        expires_in = token_data.get('expiresIn') or token_data.get('expires_in', 3600)
        user_id = token_data.get('userId') or token_data.get('user_id')
        
        # Если нет явного токена, пробуем извлечь из cookies
        # Skyeng может использовать разные имена для cookies
        if not token:
            # Пробуем разные возможные имена cookies
            token = (
                session.cookies.get('JWT') or
                session.cookies.get('jwt') or
                session.cookies.get('access_token') or
                session.cookies.get('accessToken') or
                session.cookies.get('session_id') or
                session.cookies.get('sessionid')
            )
        
        # Если всё ещё нет токена, используем первый доступный cookie
        if not token:
            cookies_dict = session.cookies.get_dict()
            # Ищем cookie, который похож на JWT (содержит точки)
            for key, value in cookies_dict.items():
                if isinstance(value, str) and value.count('.') >= 2:
                    token = value
                    logger.info(f"Используем cookie '{key}' как токен")
                    break
        
        # Если всё ещё нет токена, используем любой cookie
        if not token:
            cookies_dict = session.cookies.get_dict()
            if cookies_dict:
                token = list(cookies_dict.values())[0]
                logger.warning(f"Используем первый доступный cookie как токен")
        
        if not token:
            logger.error("Не удалось извлечь токен из сессии. Cookies: " + str(session.cookies.get_dict()))
            raise SkyengAuthError('Не удалось получить токен доступа')

        # Вычисляем время истечения (по умолчанию 1 час)
        expires_at = timezone.now() + timedelta(seconds=int(expires_in))

        logger.info(
            f"Successfully authenticated Skyeng user: {email}, "
            f"token length: {len(token)}, "
            f"expires at: {expires_at}"
        )

        return SkyengCredentials(
            token=token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            user_id=int(user_id) if user_id else None,
            email=email,
            # Сохраняем cookies сессии для последующих запросов
            _session_cookies=session.cookies.get_dict(),
        )

    def create_session_from_cookies(self, cookies: Dict[str, str]) -> requests.Session:
        """
        Создает сессию из сохраненных cookies.

        Args:
            cookies: Dict с cookies

        Returns:
            requests.Session с установленными cookies
        """
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8',
        })
        
        # Устанавливаем cookies
        for key, value in cookies.items():
            session.cookies.set(key, value, domain='.skyeng.ru', path='/')
        
        return session

    def authenticate_with_session(
        self,
        email: str,
        password: str,
        save_session: bool = True
    ) -> Tuple[SkyengCredentials, Optional[requests.Session]]:
        """
        Аутентификация с сохранением сессии.

        Args:
            email: Email пользователя
            password: Пароль пользователя
            save_session: Сохранить ли сессию

        Returns:
            Tuple[SkyengCredentials, Optional[requests.Session]]: (credentials, session)
        """
        logger.info(f"Attempting Skyeng login with session for email: {email}")

        # Шаг 1: Получение CSRF-токена
        session, csrf_token = self._get_csrf_token()

        # Шаг 2: Логин с CSRF
        session = self._login_with_csrf(session, csrf_token, email, password)

        # Шаг 3: Получение API токенов
        token_data = self._get_api_tokens_from_session(session)

        # Создаем credentials
        credentials = self._create_credentials_from_session(session, token_data, email)

        return credentials, session if save_session else None
