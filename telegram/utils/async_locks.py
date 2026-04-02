"""
Утилиты для асинхронной работы.
Включая блокировки для предотвращения race conditions.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AsyncLockManager:
    """
    Менеджер асинхронных блокировок.
    
    Предотвращает race conditions при одновременном обновлении
    credentials или других общих ресурсов.
    
    Пример использования:
        lock_manager = AsyncLockManager()
        
        async with lock_manager.acquire_lock(f"user_{user_id}"):
            # Критическая секция - только один поток одновременно
            await update_credentials(user_id, new_creds)
    """
    
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_creation = asyncio.Lock()
    
    async def get_lock(self, key: str) -> asyncio.Lock:
        """
        Получает или создаёт блокировку для ключа.
        
        Args:
            key: Уникальный ключ для блокировки (например, user_id)
            
        Returns:
            asyncio.Lock объект
        """
        # Быстрая проверка без блокировки
        if key in self._locks:
            return self._locks[key]
        
        # Создаём новую блокировку с защитой от race condition
        async with self._lock_creation:
            # Проверяем ещё раз после получения блокировки
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]
    
    @asynccontextmanager
    async def acquire_lock(self, key: str):
        """
        Контекстный менеджер для приобретения блокировки.
        
        Args:
            key: Уникальный ключ для блокировки
            
        Yields:
            None
            
        Пример:
            async with lock_manager.acquire_lock(f"user_{user_id}"):
                await critical_section()
        """
        lock = await self.get_lock(key)
        await lock.acquire()
        try:
            yield
        finally:
            lock.release()
    
    def remove_lock(self, key: str):
        """
        Удаляет блокировку (для очистки памяти).
        
        Args:
            key: Ключ блокировки для удаления
        """
        if key in self._locks:
            del self._locks[key]
    
    def clear(self):
        """Очищает все блокировки"""
        self._locks.clear()


# Глобальный экземпляр для использования в приложении
lock_manager = AsyncLockManager()


@asynccontextmanager
async def user_credentials_lock(user_id: str):
    """
    Блокировка для обновления credentials пользователя.
    
    Предотвращает race condition при одновременном обновлении
    токенов.
    
    Пример:
        async with user_credentials_lock(user_id):
            await update_google_token(user_id, new_token)
    """
    async with lock_manager.acquire_lock(f"creds_{user_id}"):
        yield


@asynccontextmanager
async def token_refresh_lock(user_id: str, service: str):
    """
    Блокировка для обновления токена сервиса.
    
    Args:
        user_id: ID пользователя
        service: Название сервиса (google, skyeng)
        
    Пример:
        async with token_refresh_lock(user_id, 'google'):
            await refresh_google_token(user_id)
    """
    async with lock_manager.acquire_lock(f"refresh_{service}_{user_id}"):
        yield
