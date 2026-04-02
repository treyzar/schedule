"""
Централизованная конфигурация приложения.
Все настройки приложения должны быть здесь, а не разбросаны по коду.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from functools import lru_cache


@dataclass(frozen=True)
class OllamaConfig:
    """Конфигурация Ollama AI"""
    base_url: str = field(
        default_factory=lambda: os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
    )
    model_name: str = field(
        default_factory=lambda: os.getenv('OLLAMA_MODEL_NAME', 'qwen3.5:9b')
    )
    timeout: int = field(
        default_factory=lambda: int(os.getenv('OLLAMA_TIMEOUT', '60'))
    )
    chat_endpoint: str = '/api/chat'
    generate_endpoint: str = '/api/generate'
    
    @property
    def chat_url(self) -> str:
        """URL для chat API"""
        return f"{self.base_url.rstrip('/')}{self.chat_endpoint}"
    
    @property
    def generate_url(self) -> str:
        """URL для generate API"""
        return f"{self.base_url.rstrip('/')}{self.generate_endpoint}"


@dataclass(frozen=True)
class GoogleConfig:
    """Конфигурация Google OAuth и Calendar API"""
    client_secrets_file: str = field(
        default_factory=lambda: os.getenv('GOOGLE_CLIENT_SECRETS_FILE', 'client_secrets.json')
    )
    scopes: List[str] = field(
        default_factory=lambda: [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/userinfo.email',
        ]
    )
    redirect_uri: str = field(
        default_factory=lambda: os.getenv(
            'GOOGLE_REDIRECT_URI',
            'http://localhost:8000/parse_calendar/oauth2callback/'
        )
    )
    credentials_encryption_key: Optional[str] = field(
        default_factory=lambda: os.getenv('CREDENTIALS_ENCRYPTION_KEY')
    )
    
    @property
    def calendar_readonly_scopes(self) -> List[str]:
        """Scopes только для чтения календаря"""
        return ['https://www.googleapis.com/auth/calendar.readonly']
    
    @property
    def calendar_full_scopes(self) -> List[str]:
        """Полные права на календарь"""
        return self.scopes


@dataclass(frozen=True)
class SkyengConfig:
    """Конфигурация Skyeng API"""
    base_url: str = field(
        default_factory=lambda: os.getenv('SKYENG_API_BASE_URL', 'https://api.skyeng.ru')
    )
    edu_base_url: str = 'https://edu-avatar.skyeng.ru'
    id_base_url: str = 'https://id.skyeng.ru'
    avatar_base_url: str = 'https://avatar.skyeng.ru'
    timeout: int = field(
        default_factory=lambda: int(os.getenv('SKYENG_TIMEOUT', '30'))
    )
    timeout_long: int = field(
        default_factory=lambda: int(os.getenv('SKYENG_TIMEOUT_LONG', '60'))
    )
    retry_attempts: int = field(
        default_factory=lambda: int(os.getenv('SKYENG_RETRY_ATTEMPTS', '3'))
    )
    user_agent: str = 'SmartScheduler/1.0'
    
    @property
    def login_endpoint(self) -> str:
        """Endpoint для логина"""
        return '/auth/public/login'
    
    @property
    def refresh_endpoint(self) -> str:
        """Endpoint для refresh токена"""
        return '/auth/public/refresh'
    
    @property
    def validate_endpoint(self) -> str:
        """Endpoint для валидации токена"""
        return '/auth/public/validate'


@dataclass(frozen=True)
class TelegramBotConfig:
    """Конфигурация Telegram бота"""
    token: Optional[str] = field(
        default_factory=lambda: os.getenv('TELEGRAM_BOT_TOKEN')
    )
    webhook_url: Optional[str] = field(
        default_factory=lambda: os.getenv('TELEGRAM_WEBHOOK_URL')
    )
    use_webhook: bool = field(
        default_factory=lambda: os.getenv('TELEGRAM_USE_WEBHOOK', 'False') == 'True'
    )
    fsm_storage: str = field(
        default_factory=lambda: os.getenv('TELEGRAM_FSM_STORAGE', 'memory')
    )


@dataclass(frozen=True)
class DatabaseConfig:
    """Конфигурация базы данных"""
    engine: str = 'django.db.backends.sqlite3'
    name: str = 'db.sqlite3'
    
    @property
    def is_sqlite(self) -> bool:
        """Проверяет, используется ли SQLite"""
        return 'sqlite' in self.engine


@dataclass(frozen=True)
class AppConfig:
    """
    Основная конфигурация приложения.
    
    Пример использования:
        from config import get_config
        
        config = get_config()
        response = requests.post(config.ollama.chat_url, timeout=config.ollama.timeout)
    """
    # Basic settings
    debug: bool = field(
        default_factory=lambda: os.getenv('DEBUG', 'False') == 'True'
    )
    secret_key: str = field(
        default_factory=lambda: os.getenv('DJANGO_SECRET_KEY', '')
    )
    frontend_url: str = field(
        default_factory=lambda: os.getenv('FRONTEND_URL', 'http://localhost:4028')
    )
    backend_url: str = field(
        default_factory=lambda: os.getenv('BACKEND_URL', 'http://localhost:8000')
    )
    allowed_hosts: List[str] = field(
        default_factory=lambda: os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    )
    
    # Timezone
    timezone: str = field(
        default_factory=lambda: os.getenv('TIMEZONE', 'Europe/Moscow')
    )
    
    # Sub-configs
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    google: GoogleConfig = field(default_factory=GoogleConfig)
    skyeng: SkyengConfig = field(default_factory=SkyengConfig)
    telegram: TelegramBotConfig = field(default_factory=TelegramBotConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # Timeouts
    request_timeout_short: int = 5
    request_timeout_medium: int = 30
    request_timeout_long: int = 60
    
    # Feature flags
    enable_credentials_encryption: bool = field(
        default_factory=lambda: os.getenv('ENABLE_CREDENTIALS_ENCRYPTION', 'True') == 'True'
    )


@lru_cache()
def get_config() -> AppConfig:
    """
    Возвращает кэшированную конфигурацию приложения.
    
    Использование:
        from config import get_config
        
        config = get_config()
        ollama_url = config.ollama.chat_url
    
    Returns:
        AppConfig объект с настройками
    """
    return AppConfig()


def reload_config() -> AppConfig:
    """
    Перезагружает конфигурацию (сбрасывает кэш).
    Полезно для тестов.
    """
    get_config.cache_clear()
    return get_config()
