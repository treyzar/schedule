"""
Health check endpoints для мониторинга состояния приложения.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from django.db import connection
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint для мониторинга.
    
    GET /health/
    
    Response (healthy):
    {
        "status": "healthy",
        "timestamp": "2024-04-02T15:00:00Z",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 5},
            "cache": {"status": "healthy"},
            "ollama": {"status": "healthy"},
            "google_api": {"status": "healthy"},
            "skyeng_api": {"status": "healthy"}
        }
    }
    
    Response (degraded):
    {
        "status": "degraded",
        "timestamp": "...",
        "checks": {
            "database": {"status": "healthy"},
            "cache": {"status": "unhealthy", "error": "..."}
        }
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        checks = {
            'database': self._check_database(),
            'cache': self._check_cache(),
            'ollama': self._check_ollama(),
        }
        
        # Определяем общий статус
        all_healthy = all(
            check.get('status') == 'healthy' 
            for check in checks.values()
        )
        
        healthy_count = sum(
            1 for check in checks.values() 
            if check.get('status') == 'healthy'
        )
        
        overall_status = 'healthy' if all_healthy else 'degraded'
        if healthy_count == 0:
            overall_status = 'unhealthy'
        
        return Response({
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'summary': {
                'total': len(checks),
                'healthy': healthy_count,
                'unhealthy': len(checks) - healthy_count,
            }
        }, status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE)
    
    def _check_database(self) -> Dict[str, Any]:
        """Проверяет подключение к базе данных"""
        try:
            start = datetime.now()
            connection.ensure_connection()
            latency = (datetime.now() - start).total_seconds() * 1000
            
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            
            return {
                'status': 'healthy',
                'latency_ms': round(latency, 2),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
            }
    
    def _check_cache(self) -> Dict[str, Any]:
        """Проверяет работу cache"""
        try:
            test_key = 'health_check_test'
            test_value = 'ok'
            
            cache.set(test_key, test_value, timeout=10)
            result = cache.get(test_key)
            
            if result == test_value:
                return {'status': 'healthy'}
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Cache read mismatch',
                }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
            }
    
    def _check_ollama(self) -> Dict[str, Any]:
        """Проверяет доступность Ollama API"""
        import aiohttp
        from config import get_config
        
        config = get_config()
        
        async def check():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{config.ollama.base_url}/api/tags",
                        timeout=5
                    ) as response:
                        if response.status == 200:
                            return {'status': 'healthy'}
                        else:
                            return {
                                'status': 'degraded',
                                'error': f'Ollama returned {response.status}',
                            }
            except Exception as e:
                return {
                    'status': 'unhealthy',
                    'error': str(e),
                }
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(check())
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
            }


class DetailedHealthCheckView(APIView):
    """
    Детальный health check с информацией о версиях и конфигурации.
    
    GET /health/detailed/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.conf import settings
        
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': {
                'python': self._get_python_version(),
                'django': self._get_django_version(),
            },
            'configuration': {
                'debug': settings.DEBUG,
                'timezone': settings.TIME_ZONE,
                'allowed_hosts': settings.ALLOWED_HOSTS,
            },
            'services': {
                'ollama': {
                    'url': settings.OLLAMA_BASE_URL,
                    'model': settings.OLLAMA_MODEL_NAME,
                },
                'google': {
                    'scopes': settings.GOOGLE_SCOPES,
                },
            }
        })
    
    def _get_python_version(self) -> str:
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _get_django_version(self) -> str:
        import django
        return f"{django.VERSION[0]}.{django.VERSION[1]}.{django.VERSION[2]}"
