"""
Сервисы для работы с внешними API
"""

from .skyeng_auth import SkyengAuthService
from .google_auth import GoogleAuthService

__all__ = ['SkyengAuthService', 'GoogleAuthService']
