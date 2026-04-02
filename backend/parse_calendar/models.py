from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import Optional, Dict, Any
import json
import logging

from shared.credentials import GoogleCredentials, SkyengCredentials
from shared.encryption import CredentialEncryptor, CredentialEncryptionError

logger = logging.getLogger(__name__)
User = get_user_model()


class UserCredentials(models.Model):
    """
    Модель для хранения учетных данных пользователя для внешних сервисов.
    Хранит токены Google Calendar и Skyeng в зашифрованном виде.
    
    Пример использования:
        # Сохранение Google credentials
        user_creds = get_or_create_user_credentials(user)
        user_creds.set_google_credentials(google_creds_dict, email='user@gmail.com')
        user_creds.save()
        
        # Получение Google credentials
        google_creds = user_creds.get_google_credentials()
        if google_creds:
            service = build('calendar', 'v3', credentials=google_creds.to_google_credentials())
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='external_credentials'
    )

    # Google Calendar credentials (encrypted)
    google_token_encrypted = models.TextField(
        'Google Access Token (Encrypted)',
        blank=True,
        null=True,
        help_text='Зашифрованный access token'
    )
    google_refresh_token_encrypted = models.TextField(
        'Google Refresh Token (Encrypted)',
        blank=True,
        null=True,
        help_text='Зашифрованный refresh token'
    )
    google_client_secret_encrypted = models.TextField(
        'Google Client Secret (Encrypted)',
        blank=True,
        null=True,
        help_text='Зашифрованный client secret'
    )
    
    # Google Calendar credentials (public, not encrypted)
    google_token_uri = models.CharField(
        'Google Token URI',
        max_length=255,
        blank=True,
        null=True
    )
    google_client_id = models.CharField(
        'Google Client ID',
        max_length=255,
        blank=True,
        null=True
    )
    google_scopes = models.TextField(
        'Google Scopes (JSON)',
        blank=True,
        null=True,
        help_text='JSON array scopes'
    )
    google_token_expiry = models.DateTimeField(
        'Google Token Expiry',
        blank=True,
        null=True
    )
    google_email = models.EmailField(
        'Google Email',
        blank=True,
        null=True
    )

    # Skyeng credentials (encrypted)
    skyeng_token_encrypted = models.TextField(
        'Skyeng Access Token (Encrypted)',
        blank=True,
        null=True
    )
    skyeng_refresh_token_encrypted = models.TextField(
        'Skyeng Refresh Token (Encrypted)',
        blank=True,
        null=True
    )
    
    # Skyeng credentials (public, not encrypted)
    skyeng_token_expiry = models.DateTimeField(
        'Skyeng Token Expiry',
        blank=True,
        null=True
    )
    skyeng_email = models.EmailField(
        'Skyeng Email',
        blank=True,
        null=True
    )
    skyeng_user_id = models.IntegerField(
        'Skyeng User ID',
        blank=True,
        null=True
    )

    # Общие метаданные
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)
    last_sync_google = models.DateTimeField(
        'Last Sync Google',
        blank=True,
        null=True
    )
    last_sync_skyeng = models.DateTimeField(
        'Last Sync Skyeng',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'User Credentials'
        verbose_name_plural = 'User Credentials'
        db_table = 'user_credentials'

    def __str__(self) -> str:
        parts = []
        if self.google_email:
            parts.append(f"Google: {self.google_email}")
        if self.skyeng_email:
            parts.append(f"Skyeng: {self.skyeng_email}")
        return f"Credentials for {self.user.username} ({', '.join(parts)})" if parts else f"Credentials for {self.user.username}"

    # =============================================================================
    # Google Credentials Methods
    # =============================================================================
    
    def set_google_credentials(
        self,
        credentials_data: Dict[str, Any],
        email: Optional[str] = None
    ):
        """
        Сохраняет Google credentials с шифрованием чувствительных данных.
        
        Args:
            credentials_data: Dict с данными credentials
            email: Email пользователя (опционально)
            
        Пример:
            creds = {
                'token': 'access_token',
                'refresh_token': 'refresh_token',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': 'client_id',
                'client_secret': 'client_secret',
                'scopes': ['calendar.readonly']
            }
            user_creds.set_google_credentials(creds, email='user@gmail.com')
        """
        encryptor = CredentialEncryptor()
        
        # Шифруем чувствительные данные
        sensitive_data = {
            'token': credentials_data.get('token', ''),
            'refresh_token': credentials_data.get('refresh_token', ''),
            'client_secret': credentials_data.get('client_secret', ''),
        }
        
        try:
            encrypted = encryptor.encrypt(sensitive_data)
            
            # Разделяем на encrypted и public части
            self.google_token_encrypted = encrypted
            self.google_refresh_token_encrypted = encrypted  # Same encryption batch
            self.google_client_secret_encrypted = encrypted  # Same encryption batch
            
            # Сохраняем public данные
            self.google_token_uri = credentials_data.get('token_uri')
            self.google_client_id = credentials_data.get('client_id')
            
            scopes = credentials_data.get('scopes', [])
            if isinstance(scopes, list):
                self.google_scopes = json.dumps(scopes)
            
            self.google_email = email or credentials_data.get('email')
            
            # Устанавливаем expiry
            if credentials_data.get('expiry'):
                self.google_token_expiry = credentials_data['expiry']
            elif credentials_data.get('token_expiry'):
                self.google_token_expiry = credentials_data['token_expiry']
            
            self.updated_at = timezone.now()
            
        except CredentialEncryptionError as e:
            logger.error(f"Failed to encrypt Google credentials: {e}")
            raise
    
    def get_google_credentials(self) -> Optional[GoogleCredentials]:
        """
        Получает и расшифровывает Google credentials.
        
        Returns:
            GoogleCredentials объект или None если credentials не найдены
            
        Raises:
            CredentialEncryptionError: При ошибке дешифрования
        """
        if not self.google_token_encrypted:
            return None
        
        encryptor = CredentialEncryptor()
        
        try:
            # Дешифруем чувствительные данные
            decrypted = encryptor.decrypt(self.google_token_encrypted)
            
            # Собираем public данные
            public_data = {
                'token_uri': self.google_token_uri,
                'client_id': self.google_client_id,
                'scopes': json.loads(self.google_scopes) if self.google_scopes else [],
                'email': self.google_email,
            }
            
            # Создаём credentials объект
            return GoogleCredentials.from_decrypted_dict(decrypted, public_data)
            
        except CredentialEncryptionError:
            raise
        except Exception as e:
            logger.error(f"Failed to decrypt Google credentials: {e}")
            return None
    
    def is_google_token_expired(self) -> bool:
        """Проверяет, истек ли Google токен"""
        if not self.google_token_expiry:
            return False
        return timezone.now() >= self.google_token_expiry
    
    def has_google_credentials(self) -> bool:
        """Проверяет наличие Google credentials"""
        return bool(self.google_token_encrypted)

    def get_google_credentials_dict(self) -> Optional[Dict[str, Any]]:
        """
        Получает Google credentials как dict для использования с Google OAuth.
        
        Returns:
            Dict с credentials или None
        """
        creds = self.get_google_credentials()
        if not creds:
            return None
        
        # Конвертируем в dict, заменяя expires_at на expiry
        from datetime import datetime
        return {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expires_at,
        }

    # =============================================================================
    # Skyeng Credentials Methods
    # =============================================================================
    
    def set_skyeng_credentials(
        self,
        token: str,
        refresh_token: Optional[str] = None,
        expiry: Optional[timezone.datetime] = None,
        email: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        """
        Сохраняет Skyeng credentials с шифрованием.
        
        Args:
            token: Access token
            refresh_token: Refresh token (опционально)
            expiry: Время истечения токена
            email: Email пользователя
            user_id: ID пользователя в Skyeng
        """
        encryptor = CredentialEncryptor()
        
        # Шифруем чувствительные данные
        sensitive_data = {
            'token': token,
            'refresh_token': refresh_token or '',
        }
        
        try:
            encrypted = encryptor.encrypt(sensitive_data)
            
            self.skyeng_token_encrypted = encrypted
            self.skyeng_refresh_token_encrypted = encrypted
            
            # Public данные
            self.skyeng_token_expiry = expiry
            self.skyeng_email = email
            self.skyeng_user_id = user_id
            
            self.updated_at = timezone.now()
            
        except CredentialEncryptionError as e:
            logger.error(f"Failed to encrypt Skyeng credentials: {e}")
            raise
    
    def get_skyeng_credentials(self) -> Optional[SkyengCredentials]:
        """
        Получает и расшифровывает Skyeng credentials.
        
        Returns:
            SkyengCredentials объект или None
        """
        if not self.skyeng_token_encrypted:
            return None
        
        encryptor = CredentialEncryptor()
        
        try:
            decrypted = encryptor.decrypt(self.skyeng_token_encrypted)
            
            public_data = {
                'user_id': self.skyeng_user_id,
                'email': self.skyeng_email,
            }
            
            # Добавляем expires_at если есть
            if self.skyeng_token_expiry:
                public_data['expires_at'] = self.skyeng_token_expiry
            
            return SkyengCredentials.from_decrypted_dict(decrypted, public_data)
            
        except CredentialEncryptionError:
            raise
        except Exception as e:
            logger.error(f"Failed to decrypt Skyeng credentials: {e}")
            return None
    
    def is_skyeng_token_expired(self) -> bool:
        """Проверяет, истек ли Skyeng токен"""
        if not self.skyeng_token_expiry:
            return False
        return timezone.now() >= self.skyeng_token_expiry
    
    def has_skyeng_credentials(self) -> bool:
        """Проверяет наличие Skyeng credentials"""
        return bool(self.skyeng_token_encrypted)

    # =============================================================================
    # General Methods
    # =============================================================================
    
    def is_fully_authenticated(self) -> bool:
        """Проверяет, авторизован ли пользователь во всех сервисах"""
        return self.has_google_credentials() and self.has_skyeng_credentials()
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Возвращает статус авторизации пользователя.
        
        Returns:
            Dict со статусами авторизации
        """
        return {
            'google': {
                'authenticated': self.has_google_credentials(),
                'email': self.google_email,
                'token_expired': self.is_google_token_expired(),
            },
            'skyeng': {
                'authenticated': self.has_skyeng_credentials(),
                'email': self.skyeng_email,
                'token_expired': self.is_skyeng_token_expired(),
            },
            'fully_authenticated': self.is_fully_authenticated(),
        }
