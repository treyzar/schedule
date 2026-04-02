"""
Модуль шифрования для защиты чувствительных данных.
Использует Fernet (symmetric encryption) для шифрования credentials.
"""

import base64
import hashlib
import logging
from typing import Dict, Optional
from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)


class CredentialEncryptionError(Exception):
    """Ошибка шифрования/дешифрования credentials"""
    pass


class CredentialEncryptor:
    """
    Шифрует и дешифрует credentials.
    
    Пример использования:
        encryptor = CredentialEncryptor()
        
        # Шифрование
        encrypted = encryptor.encrypt({'token': 'secret_token'})
        
        # Дешифрование
        decrypted = encryptor.decrypt(encrypted)
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Инициализация шифровальщика.
        
        Args:
            encryption_key: Ключ шифрования. Если не указан, 
                           используется CREDENTIALS_ENCRYPTION_KEY из settings.
        """
        key = encryption_key or getattr(settings, 'CREDENTIALS_ENCRYPTION_KEY', None)
        
        if not key:
            # Fallback: генерируем ключ из SECRET_KEY
            key = self._derive_key_from_secret_key(settings.SECRET_KEY)
            logger.warning(
                "CREDENTIALS_ENCRYPTION_KEY не настроен. "
                "Используется ключ, полученный из SECRET_KEY."
            )
        
        self._fernet = Fernet(key)
    
    def _derive_key_from_secret_key(self, secret_key: str) -> bytes:
        """
        Создаёт 32-байтный ключ из SECRET_KEY Django.
        
        Args:
            secret_key: SECRET_KEY из Django settings
            
        Returns:
            Base64-encoded 32-byte key для Fernet
        """
        # Хэшируем SECRET_KEY для получения 32 байт
        key_hash = hashlib.sha256(secret_key.encode()).digest()
        # Кодируем в base64 для Fernet
        return base64.urlsafe_b64encode(key_hash)
    
    def encrypt(self, data: Dict[str, str]) -> str:
        """
        Шифрует dict с чувствительными данными.
        
        Args:
            data: Dict с данными для шифрования
            
        Returns:
            Зашифрованная строка (base64)
            
        Raises:
            CredentialEncryptionError: При ошибке шифрования
        """
        try:
            import json
            data_bytes = json.dumps(data).encode('utf-8')
            encrypted_bytes = self._fernet.encrypt(data_bytes)
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}", exc_info=True)
            raise CredentialEncryptionError(f"Failed to encrypt data: {e}")
    
    def decrypt(self, encrypted_data: str) -> Dict[str, str]:
        """
        Дешифрует строку обратно в dict.
        
        Args:
            encrypted_data: Зашифрованная строка
            
        Returns:
            Dict с расшифрованными данными
            
        Raises:
            CredentialEncryptionError: При ошибке дешифрования
        """
        try:
            import json
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return json.loads(decrypted_bytes.decode('utf-8'))
        except Exception as e:
            logger.error(f"Decryption failed: {e}", exc_info=True)
            raise CredentialEncryptionError(f"Failed to decrypt data: {e}")
