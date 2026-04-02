"""
Tests for shared credentials module
"""

import pytest
from datetime import datetime, timedelta
from shared.credentials import (
    GoogleCredentials,
    SkyengCredentials,
    CredentialType,
    CredentialStatus,
    BaseCredentials,
)


class TestBaseCredentials:
    """Тесты для базового класса credentials"""
    
    def test_is_expired_false(self):
        """Тест: credentials не истекли"""
        future = datetime.now() + timedelta(hours=1)
        creds = BaseCredentials(token='test', expires_at=future)
        
        assert creds.is_expired is False
    
    def test_is_expired_true(self):
        """Тест: credentials истекли"""
        past = datetime.now() - timedelta(hours=1)
        creds = BaseCredentials(token='test', expires_at=past)
        
        assert creds.is_expired is True
    
    def test_is_expired_no_expiry(self):
        """Тест: credentials без срока действия не истекли"""
        creds = BaseCredentials(token='test', expires_at=None)
        
        assert creds.is_expired is False
    
    def test_to_dict(self):
        """Тест: конвертация в dict"""
        future = datetime.now() + timedelta(hours=1)
        creds = BaseCredentials(token='test', expires_at=future)
        
        data = creds.to_dict()
        
        assert data['token'] == 'test'
        assert 'expires_at' in data
    
    def test_from_dict(self):
        """Тест: создание из dict"""
        data = {
            'token': 'test',
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat(),
        }
        
        creds = BaseCredentials.from_dict(data)
        
        assert creds.token == 'test'
        assert isinstance(creds.expires_at, datetime)


class TestGoogleCredentials:
    """Тесты для Google credentials"""
    
    @pytest.fixture
    def sample_google_creds(self):
        return GoogleCredentials(
            token='access_token',
            refresh_token='refresh_token',
            token_uri='https://oauth2.googleapis.com/token',
            client_id='client_id',
            client_secret='client_secret',
            scopes=['calendar.readonly'],
            email='user@gmail.com',
        )
    
    def test_creation(self, sample_google_creds):
        """Тест: создание GoogleCredentials"""
        assert sample_google_creds.token == 'access_token'
        assert sample_google_creds.refresh_token == 'refresh_token'
        assert sample_google_creds.email == 'user@gmail.com'
        assert len(sample_google_creds.scopes) == 1
    
    def test_to_dict(self, sample_google_creds):
        """Тест: конвертация в dict"""
        data = sample_google_creds.to_dict()
        
        assert data['token'] == 'access_token'
        assert data['refresh_token'] == 'refresh_token'
        assert data['email'] == 'user@gmail.com'
        assert data['scopes'] == ['calendar.readonly']
    
    def test_from_dict(self):
        """Тест: создание из dict"""
        data = {
            'token': 'access_token',
            'refresh_token': 'refresh_token',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'client_id',
            'client_secret': 'client_secret',
            'scopes': ['calendar.readonly'],
            'email': 'user@gmail.com',
        }
        
        creds = GoogleCredentials.from_dict(data)
        
        assert creds.token == 'access_token'
        assert creds.email == 'user@gmail.com'
    
    def test_to_encrypted_dict(self, sample_google_creds):
        """Тест: конвертация в dict для шифрования"""
        encrypted = sample_google_creds.to_encrypted_dict()
        
        assert 'token' in encrypted
        assert 'refresh_token' in encrypted
        assert 'client_secret' in encrypted
        assert 'scopes' not in encrypted  # Не шифруется
    
    def test_from_decrypted_dict(self):
        """Тест: создание из расшифрованных данных"""
        decrypted = {
            'token': 'access_token',
            'refresh_token': 'refresh_token',
            'client_secret': 'client_secret',
        }
        public = {
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': 'client_id',
            'scopes': ['calendar.readonly'],
            'email': 'user@gmail.com',
        }
        
        creds = GoogleCredentials.from_decrypted_dict(decrypted, public)
        
        assert creds.token == 'access_token'
        assert creds.client_id == 'client_id'
        assert creds.email == 'user@gmail.com'
    
    def test_is_expired(self):
        """Тест: проверка истечения"""
        past = datetime.now() - timedelta(hours=1)
        creds = GoogleCredentials(token='test', expires_at=past)
        
        assert creds.is_expired is True


class TestSkyengCredentials:
    """Тесты для Skyeng credentials"""
    
    @pytest.fixture
    def sample_skyeng_creds(self):
        return SkyengCredentials(
            token='jwt_token',
            refresh_token='refresh_jwt',
            user_id=12345,
            email='user@example.com',
            expires_at=datetime.now() + timedelta(hours=1),
        )
    
    def test_creation(self, sample_skyeng_creds):
        """Тест: создание SkyengCredentials"""
        assert sample_skyeng_creds.token == 'jwt_token'
        assert sample_skyeng_creds.user_id == 12345
        assert sample_skyeng_creds.email == 'user@example.com'
    
    def test_to_dict(self, sample_skyeng_creds):
        """Тест: конвертация в dict"""
        data = sample_skyeng_creds.to_dict()
        
        assert data['token'] == 'jwt_token'
        assert data['user_id'] == 12345
        assert data['email'] == 'user@example.com'
        assert 'expires_at' in data
    
    def test_from_decrypted_dict(self):
        """Тест: создание из расшифрованных данных"""
        decrypted = {
            'token': 'jwt_token',
            'refresh_token': 'refresh_jwt',
        }
        public = {
            'user_id': 12345,
            'email': 'user@example.com',
        }
        
        creds = SkyengCredentials.from_decrypted_dict(decrypted, public)
        
        assert creds.token == 'jwt_token'
        assert creds.user_id == 12345


class TestCredentialStatus:
    """Тесты для enum статусов credentials"""
    
    def test_status_values(self):
        """Тест: значения статусов"""
        assert CredentialStatus.VALID.value == 'valid'
        assert CredentialStatus.EXPIRED_CAN_REFRESH.value == 'expired_can_refresh'
        assert CredentialStatus.EXPIRED_NEEDS_REAUTH.value == 'expired_needs_reauth'
        assert CredentialStatus.INVALID.value == 'invalid'


class TestCredentialType:
    """Тесты для enum типов credentials"""
    
    def test_type_values(self):
        """Тест: значения типов"""
        assert CredentialType.GOOGLE.value == 'google'
        assert CredentialType.SKYENG.value == 'skyeng'
