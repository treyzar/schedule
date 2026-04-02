"""
Модуль для работы с credentials различных сервисов.
Предоставляет единый интерфейс для хранения и управления учетными данными.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json


class CredentialType(Enum):
    """Типы credentials"""
    GOOGLE = "google"
    SKYENG = "skyeng"


class CredentialStatus(Enum):
    """Статус credentials"""
    VALID = "valid"
    EXPIRED_CAN_REFRESH = "expired_can_refresh"
    EXPIRED_NEEDS_REAUTH = "expired_needs_reauth"
    INVALID = "invalid"


@dataclass
class BaseCredentials:
    """Базовый класс для всех credentials"""
    token: str
    expires_at: Optional[datetime] = None
    
    @property
    def is_expired(self) -> bool:
        """Проверяет, истекли ли credentials"""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в dict для сериализации"""
        data = asdict(self)
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseCredentials':
        """Создаёт из dict"""
        if 'expires_at' in data and data['expires_at']:
            try:
                data['expires_at'] = datetime.fromisoformat(data['expires_at'])
            except (ValueError, TypeError):
                data['expires_at'] = None
        return cls(**data)


@dataclass
class GoogleCredentials(BaseCredentials):
    """
    Google OAuth credentials.
    
    Пример использования:
        creds = GoogleCredentials(
            token='access_token',
            refresh_token='refresh_token',
            client_id='...',
            client_secret='...',
        )
        
        # Конвертация в Google Credentials объект
        google_creds = creds.to_google_credentials()
        
        # Создание из Google Credentials объекта
        creds = GoogleCredentials.from_google_credentials(google_creds)
    """
    refresh_token: Optional[str] = None
    token_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    email: Optional[str] = None
    
    def to_google_credentials(self) -> 'google.oauth2.credentials.Credentials':
        """
        Конвертирует в Google Credentials объект для использования с Google API.
        
        Returns:
            google.oauth2.credentials.Credentials объект
        """
        import google.oauth2.credentials
        return google.oauth2.credentials.Credentials(
            token=self.token,
            refresh_token=self.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes,
        )
    
    @classmethod
    def from_google_credentials(
        cls, 
        creds: 'google.oauth2.credentials.Credentials'
    ) -> 'GoogleCredentials':
        """
        Создаёт GoogleCredentials из Google Credentials объекта.
        
        Args:
            creds: Google Credentials объект
            
        Returns:
            GoogleCredentials объект
        """
        email = None
        if hasattr(creds, 'id_token') and creds.id_token:
            email = creds.id_token.get('email')
        
        return cls(
            token=creds.token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=list(creds.scopes) if creds.scopes else [],
            email=email,
        )
    
    def to_encrypted_dict(self) -> Dict[str, str]:
        """
        Конвертирует в dict для шифрования.
        Возвращает только чувствительные данные.
        """
        return {
            'token': self.token,
            'refresh_token': self.refresh_token or '',
            'client_secret': self.client_secret or '',
        }
    
    @classmethod
    def from_decrypted_dict(
        cls, 
        decrypted: Dict[str, str],
        public_data: Dict[str, Any]
    ) -> 'GoogleCredentials':
        """
        Создаёт из расшифрованных данных.
        
        Args:
            decrypted: Расшифрованные чувствительные данные
            public_data: Открытые данные (token_uri, scopes, email, etc.)
        """
        return cls(
            token=decrypted.get('token', ''),
            refresh_token=decrypted.get('refresh_token') or None,
            token_uri=public_data.get('token_uri'),
            client_id=public_data.get('client_id'),
            client_secret=decrypted.get('client_secret') or None,
            scopes=public_data.get('scopes', []),
            email=public_data.get('email'),
        )


@dataclass
class SkyengCredentials(BaseCredentials):
    """
    Skyeng API credentials.

    Пример использования:
        creds = SkyengCredentials(
            token='jwt_token',
            refresh_token='refresh_jwt',
            user_id=12345,
            email='user@example.com'
        )
    """
    refresh_token: Optional[str] = None
    user_id: Optional[int] = None
    email: Optional[str] = None
    # Cookies сессии для веб-аутентификации (не сохраняется в БД)
    _session_cookies: Dict[str, str] = field(default_factory=dict, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в dict для сериализации"""
        data = super().to_dict()
        data.update({
            'refresh_token': self.refresh_token,
            'user_id': self.user_id,
            'email': self.email,
        })
        return data

    def to_encrypted_dict(self) -> Dict[str, str]:
        """Конвертирует в dict для шифрования"""
        return {
            'token': self.token,
            'refresh_token': self.refresh_token or '',
        }

    @classmethod
    def from_decrypted_dict(
        cls,
        decrypted: Dict[str, str],
        public_data: Dict[str, Any]
    ) -> 'SkyengCredentials':
        """Создаёт из расшифрованных данных"""
        return cls(
            token=decrypted.get('token', ''),
            refresh_token=decrypted.get('refresh_token') or None,
            user_id=public_data.get('user_id'),
            email=public_data.get('email'),
        )
