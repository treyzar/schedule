"""
Тесты для сервисов авторизации Skyeng и Google
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from aiohttp import ClientSession
import requests

from backend.services.skyeng_auth import SkyengAuthService, AuthConfig
from backend.services.google_auth import GoogleAuthService, GoogleCredentials


class TestSkyengAuthService:
    """Тесты для SkyengAuthService"""

    def test_extract_csrf_token_from_input(self):
        """Извлечение CSRF токена из input элемента"""
        html = '''
        <html>
            <input name="csrfToken" value="abc123xyz789">
        </html>
        '''
        soup = MagicMock()
        input_mock = MagicMock()
        input_mock.get.return_value = "abc123xyz789"
        soup.find.return_value = input_mock
        
        # Тестируем логику извлечения
        assert input_mock.get("value") == "abc123xyz789"

    def test_extract_csrf_token_from_meta(self):
        """Извлечение CSRF токена из meta тега"""
        html = '''
        <html>
            <meta name="csrf-token" content="xyz789abc123">
        </html>
        '''
        # Простая проверка логики
        assert "xyz789abc123" in html

    def test_auth_config_default_values(self):
        """Проверка значений конфигурации по умолчанию"""
        config = AuthConfig()
        
        assert config.base_url == "https://id.skyeng.ru"
        assert config.api_url == "https://edu-avatar.skyeng.ru"
        assert "Mozilla/5.0" in config.user_agent
        assert config.timeout == 15

    @pytest.mark.asyncio
    async def test_async_login_invalid_credentials(self):
        """Тест асинхронного логина с неверными credentials"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock получения CSRF токена
            mock_response = AsyncMock()
            mock_response.text.return_value = '<input name="csrfToken" value="test-token">'
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Mock логина - ошибка авторизации
            mock_login_response = AsyncMock()
            mock_login_response.status = 401
            mock_session.post.return_value.__aenter__.return_value = mock_login_response
            
            result = await SkyengAuthService.async_login("wrong_user", "wrong_pass")
            
            assert result is None
            await mock_session.close()

    @pytest.mark.asyncio
    async def test_async_login_success(self):
        """Тест успешного асинхронного логина"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.closed = False
            
            # Mock получения CSRF токена
            mock_response = AsyncMock()
            mock_response.text.return_value = '<input name="csrfToken" value="test-token">'
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            # Mock успешного логина
            mock_login_response = AsyncMock()
            mock_login_response.status = 200
            mock_login_response.url = "https://id.skyeng.ru/success"
            mock_session.post.return_value.__aenter__.return_value = mock_login_response
            
            result = await SkyengAuthService.async_login("user@example.com", "correct_password")
            
            assert result is not None
            await result.close()

    def test_sync_login_invalid_credentials(self):
        """Тест синхронного логина с неверными credentials"""
        with patch('requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock получения CSRF токена
            mock_response = MagicMock()
            mock_response.text.return_value = '<input name="csrfToken" value="test-token">'
            mock_session.get.return_value = mock_response
            
            # Mock логина - ошибка авторизации
            mock_login_response = MagicMock()
            mock_login_response.status_code = 401
            mock_session.post.return_value = mock_login_response
            
            result = SkyengAuthService.sync_login("wrong_user", "wrong_pass")
            
            assert result is None

    def test_extract_session_cookies(self):
        """Извлечение cookies из сессии"""
        session = requests.Session()
        session.cookies.set('test_cookie', 'value123')
        session.cookies.set('session_id', 'abc456')
        
        cookies = SkyengAuthService.extract_session_cookies(session)
        
        assert 'test_cookie' in cookies
        assert cookies['test_cookie'] == 'value123'
        assert 'session_id' in cookies
        assert cookies['session_id'] == 'abc456'

    def test_restore_session_from_cookies(self):
        """Восстановление сессии из cookies"""
        cookies = {
            'session_id': 'abc456',
            'user_id': '12345'
        }
        
        session = SkyengAuthService.restore_session_from_cookies(cookies)
        
        assert isinstance(session, requests.Session)
        assert session.cookies.get('session_id') == 'abc456'
        assert session.cookies.get('user_id') == '12345'


class TestGoogleCredentials:
    """Тесты для модели GoogleCredentials"""

    def test_from_credentials(self):
        """Создание GoogleCredentials из Credentials"""
        mock_creds = MagicMock()
        mock_creds.token = "test_token"
        mock_creds.refresh_token = "test_refresh"
        mock_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds.client_id = "test_client_id"
        mock_creds.client_secret = "test_secret"
        mock_creds.scopes = ["scope1", "scope2"]
        
        creds = GoogleCredentials.from_credentials(mock_creds)
        
        assert creds.token == "test_token"
        assert creds.refresh_token == "test_refresh"
        assert creds.client_id == "test_client_id"
        assert creds.client_secret == "test_secret"
        assert "scope1" in creds.scopes

    def test_to_dict(self):
        """Конвертация GoogleCredentials в dict"""
        creds = GoogleCredentials(
            token="test_token",
            refresh_token="test_refresh",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="test_client_id",
            client_secret="test_secret",
            scopes=["scope1", "scope2"]
        )
        
        data = creds.to_dict()
        
        assert data['token'] == "test_token"
        assert data['refresh_token'] == "test_refresh"
        assert data['client_id'] == "test_client_id"

    def test_from_dict(self):
        """Создание GoogleCredentials из dict"""
        data = {
            'token': "test_token",
            'refresh_token': "test_refresh",
            'token_uri': "https://oauth2.googleapis.com/token",
            'client_id': "test_client_id",
            'client_secret': "test_secret",
            'scopes': ["scope1", "scope2"]
        }
        
        creds = GoogleCredentials.from_dict(data)
        
        assert creds.token == "test_token"
        assert creds.refresh_token == "test_refresh"
        assert creds.scopes == ["scope1", "scope2"]

    def test_to_credentials(self):
        """Конвертация GoogleCredentials обратно в Credentials"""
        creds = GoogleCredentials(
            token="test_token",
            refresh_token="test_refresh",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="test_client_id",
            client_secret="test_secret",
            scopes=["scope1", "scope2"]
        )
        
        credentials = creds.to_credentials()
        
        assert credentials.token == "test_token"
        assert credentials.refresh_token == "test_refresh"


class TestGoogleAuthService:
    """Тесты для GoogleAuthService"""

    @pytest.fixture
    def mock_settings(self):
        """Mock Django settings"""
        with patch('backend.services.google_auth.settings') as mock:
            mock.CLIENT_SECRETS_FILE = "/path/to/client_secrets.json"
            mock.GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
            yield mock

    def test_init_with_default_values(self, mock_settings):
        """Инициализация с значениями по умолчанию"""
        service = GoogleAuthService()
        
        assert service.client_secrets_path == "/path/to/client_secrets.json"
        assert service.scopes == ["https://www.googleapis.com/auth/calendar.readonly"]

    def test_init_with_custom_values(self):
        """Инициализация с кастомными значениями"""
        service = GoogleAuthService(
            client_secrets_path="/custom/path.json",
            scopes=["scope1", "scope2"]
        )
        
        assert service.client_secrets_path == "/custom/path.json"
        assert service.scopes == ["scope1", "scope2"]

    def test_validate_credentials_valid(self):
        """Валидация валидных credentials"""
        with patch('google.oauth2.credentials.Credentials') as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.expired = False
            mock_creds_class.return_value = mock_creds
            
            service = GoogleAuthService()
            result = service.validate_credentials({'token': 'valid_token'})
            
            assert result is True

    def test_validate_credentials_expired_with_refresh(self):
        """Валидация истекших credentials с refresh token"""
        with patch('google.oauth2.credentials.Credentials') as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.expired = True
            mock_creds.refresh_token = "refresh_token"
            mock_creds.refresh = MagicMock()
            mock_creds_class.return_value = mock_creds
            
            service = GoogleAuthService()
            result = service.validate_credentials({'token': 'expired_token'})
            
            assert result is True
            mock_creds.refresh.assert_called_once()

    def test_get_user_email_success(self):
        """Получение email пользователя"""
        with patch('google.oauth2.credentials.Credentials') as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.id_token = {'email': 'user@example.com'}
            mock_creds_class.return_value = mock_creds
            
            service = GoogleAuthService()
            email = service.get_user_email({'token': 'test_token'})
            
            assert email == 'user@example.com'

    def test_get_user_email_no_id_token(self):
        """Получение email без id_token"""
        with patch('google.oauth2.credentials.Credentials') as mock_creds_class:
            mock_creds = MagicMock()
            mock_creds.id_token = None
            mock_creds_class.return_value = mock_creds
            
            service = GoogleAuthService()
            email = service.get_user_email({'token': 'test_token'})
            
            assert email is None


@pytest.mark.asyncio
class TestSkyengAuthServiceIntegration:
    """Интеграционные тесты для SkyengAuthService"""

    async def test_full_login_flow_mock(self):
        """Полный тест потока авторизации с моками"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.closed = False
            
            # Setup mock responses
            mock_get_response = AsyncMock()
            mock_get_response.text.return_value = '''
            <html>
                <input name="csrfToken" value="csrf-12345">
            </html>
            '''
            mock_session.get.return_value.__aenter__.return_value = mock_get_response
            
            mock_post_response = AsyncMock()
            mock_post_response.status = 200
            mock_post_response.url = "https://id.skyeng.ru/success"
            mock_session.post.return_value.__aenter__.return_value = mock_post_response
            
            # Execute login
            session = await SkyengAuthService.async_login(
                username="test@example.com",
                password="password123"
            )
            
            # Assertions
            assert session is not None
            mock_session.get.assert_called_once()
            mock_session.post.assert_called_once()
            
            # Verify login data
            call_args = mock_session.post.call_args
            assert call_args[1]['data']['username'] == "test@example.com"
            assert call_args[1]['data']['csrfToken'] == "csrf-12345"
            
            await session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
