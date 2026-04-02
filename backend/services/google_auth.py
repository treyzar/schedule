"""
Сервис авторизации Google OAuth.
Обновлённая версия с явной обработкой истечения токенов и retry логикой.
"""

import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

from config import get_config
from exceptions import GoogleAuthError, GoogleTokenExpiredError, GoogleCalendarError
from shared.credentials import GoogleCredentials, CredentialStatus

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """
    Сервис авторизации Google OAuth.
    
    Управляет потоком авторизации Google Calendar API.
    
    Пример использования:
        # В Django view
        auth_service = GoogleAuthService()
        auth_url, state, code_verifier = auth_service.create_authorization_url(request)
        
        # В callback
        credentials = auth_service.exchange_code_for_credentials(code, redirect_uri, code_verifier)
    """
    
    def __init__(
        self,
        client_secrets_path: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ):
        """
        Инициализация сервиса.
        
        Args:
            client_secrets_path: Путь к client_secrets.json
            scopes: Список необходимых прав доступа
        """
        config = get_config()
        self.client_secrets_path = client_secrets_path or config.google.client_secrets_file
        self.scopes = scopes or config.google.scopes
    
    def create_authorization_url(
        self,
        request: HttpRequest,
        callback_route: str = 'google_callback'
    ) -> Tuple[str, str, str]:
        """
        Создает URL для авторизации Google.
        
        Returns:
            Tuple[str, str, str]: (authorization_url, state, code_verifier)
        """
        import os
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        from google_auth_oauthlib.flow import Flow
        
        flow = Flow.from_client_secrets_file(
            self.client_secrets_path,
            scopes=self.scopes
        )
        
        redirect_uri = request.build_absolute_uri(reverse(callback_route))
        flow.redirect_uri = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Извлекаем автоматически сгенерированный code_verifier
        code_verifier = flow.code_verifier
        
        logger.info(f"Создан URL авторизации. State={state[:10]}, PKCE verifier сохранен.")
        return authorization_url, state, code_verifier
    
    def exchange_code_for_credentials(
        self,
        code: str,
        redirect_uri: str,
        state: Optional[str] = None,
        code_verifier: Optional[str] = None
    ) -> GoogleCredentials:
        """
        Обменивает authorization code на credentials с поддержкой PKCE.
        
        Args:
            code: Authorization code от Google
            redirect_uri: Redirect URI
            state: State из сессии
            code_verifier: PKCE verifier из сессии
            
        Returns:
            GoogleCredentials объект
            
        Raises:
            GoogleAuthError: При ошибке обмена кода
        """
        import os
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        from google_auth_oauthlib.flow import Flow
        
        try:
            flow = Flow.from_client_secrets_file(
                self.client_secrets_path,
                scopes=self.scopes,
                state=state
            )
            
            flow.redirect_uri = redirect_uri
            
            # Восстанавливаем verifier для PKCE
            if code_verifier:
                flow.code_verifier = code_verifier
            
            auth_response = f"{redirect_uri}?code={code}"
            if state:
                auth_response += f"&state={state}"
            
            # Игнорируем warning о scope mismatch — Google просто добавляет openid и calendar.readonly
            # Токен всё равно приходит в response
            token_data = None
            try:
                flow.fetch_token(authorization_response=auth_response)
                token_data = flow.oauth2session.token
            except Exception as e:
                # Если это warning о scope — токен всё равно получен, просто oauthlib не распарсил
                if "Scope has changed" in str(e):
                    logger.warning(f"Ignoring scope change warning: {e}")
                    # Парсим токен вручную из OAuth2Session
                    token_data = getattr(flow.oauth2session, 'token', None)
                    
                    # Если токена нет, пробуем получить из последнего response
                    if not token_data and hasattr(flow.oauth2session, '_client'):
                        # Токен должен быть в _client.access_token
                        client = flow.oauth2session._client
                        token_data = {
                            'access_token': getattr(client, 'access_token', None),
                            'refresh_token': getattr(client, 'refresh_token', None),
                            'scope': getattr(client, 'scope', []),
                        }
                else:
                    raise
            
            # Если токена нет — ошибка
            if not token_data or not token_data.get('access_token'):
                raise GoogleAuthError(
                    message="Не удалось получить access token",
                    needs_reauth=True
                )
            
            return GoogleCredentials(
                token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=flow.client_config['client_id'],
                client_secret=flow.client_config['client_secret'],
                scopes=token_data.get('scope', '').split() if isinstance(token_data.get('scope'), str) else token_data.get('scope', []),
            )
            
        except Exception as e:
            logger.error(f"Error exchanging code for credentials: {e}", exc_info=True)
            raise GoogleAuthError(
                message=f"Ошибка обмена authorization code: {str(e)}",
                needs_reauth=True
            )
    
    def check_credential_status(
        self,
        credentials_data: Dict[str, Any]
    ) -> Tuple[str, Optional[GoogleCredentials]]:
        """
        Проверяет статус credentials и возвращает статус + обновлённые credentials.
        
        Args:
            credentials_data: Dict с данными credentials
            
        Returns:
            Tuple[str, Optional[GoogleCredentials]]: (статус, credentials или None)
            
        Пример использования:
            status, creds = auth_service.check_credential_status(credentials_data)
            
            if status == CredentialStatus.VALID:
                # Используем credentials
                pass
            elif status == CredentialStatus.EXPIRED_CAN_REFRESH:
                # credentials уже обновлены
                pass
            else:
                # Требуется повторная авторизация
                redirect_to_auth()
        """
        import google.auth.transport.requests
        from google.oauth2.credentials import Credentials
        from google.auth.exceptions import RefreshError

        try:
            # Удаляем лишние ключи, которые не ожидает Credentials
            credentials_data_clean = {
                k: v for k, v in credentials_data.items()
                if k not in ('expires_at', 'email')
            }
            credentials = Credentials(**credentials_data_clean)
            
            # Если токен не истек, возвращаем как валидный
            if not credentials.expired:
                return (
                    CredentialStatus.VALID.value,
                    GoogleCredentials.from_google_credentials(credentials)
                )
            
            # Если истек, пробуем обновить
            if credentials.refresh_token:
                try:
                    credentials.refresh(google.auth.transport.requests.Request())
                    logger.info("Google credentials успешно обновлены")
                    return (
                        CredentialStatus.VALID.value,
                        GoogleCredentials.from_google_credentials(credentials)
                    )
                except RefreshError as e:
                    logger.warning(f"Token refresh failed: {e}")
                    return (CredentialStatus.EXPIRED_NEEDS_REAUTH.value, None)
            
            # Нет refresh token - требуется re-auth
            return (CredentialStatus.EXPIRED_NEEDS_REAUTH.value, None)
            
        except Exception as e:
            logger.error(f"Credential status check failed: {e}", exc_info=True)
            return (CredentialStatus.INVALID.value, None)
    
    def refresh_credentials(
        self,
        credentials_data: Dict[str, Any]
    ) -> Optional[GoogleCredentials]:
        """
        Обновляет истекшие credentials используя refresh token.
        
        Args:
            credentials_data: Dict с данными credentials
            
        Returns:
            GoogleCredentials с валидным токеном или None при ошибке
        """
        status, credentials = self.check_credential_status(credentials_data)
        
        if status == CredentialStatus.VALID.value:
            return credentials
        
        logger.warning(f"Cannot refresh credentials: status={status}")
        return None
    
    def get_calendar_service(
        self,
        credentials_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Создает сервис Google Calendar API.
        
        Args:
            credentials_data: Dict с данными credentials
            
        Returns:
            Сервис Calendar API или None при ошибке
        """
        try:
            status, credentials = self.check_credential_status(credentials_data)
            
            if status != CredentialStatus.VALID.value or not credentials:
                logger.warning(f"Cannot create calendar service: status={status}")
                return None
            
            from googleapiclient.discovery import build
            
            google_creds = credentials.to_google_credentials()
            return build('calendar', 'v3', credentials=google_creds)
            
        except Exception as e:
            logger.error(f"Error creating Calendar service: {e}", exc_info=True)
            return None
    
    def validate_credentials(self, credentials_data: Dict[str, Any]) -> bool:
        """
        Проверяет валидность credentials.
        
        Args:
            credentials_data: Dict с данными credentials
            
        Returns:
            True если credentials валидны
        """
        status, _ = self.check_credential_status(credentials_data)
        return status == CredentialStatus.VALID.value
    
    def get_user_email(self, credentials_data: Dict[str, Any]) -> Optional[str]:
        """
        Получает email пользователя из credentials.
        
        Args:
            credentials_data: Dict с данными credentials
            
        Returns:
            Email пользователя или None
        """
        try:
            from google.oauth2.credentials import Credentials
            credentials = Credentials(**credentials_data)
            
            if hasattr(credentials, 'id_token') and credentials.id_token:
                return credentials.id_token.get('email')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user email: {e}")
            return None
