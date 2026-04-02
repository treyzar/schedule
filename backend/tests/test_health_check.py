"""
Tests for health check endpoints
"""

import pytest
from django.test import Client
from django.core.cache import cache
from django.db import connection


@pytest.mark.django_db
class TestHealthCheckView:
    """Тесты для health check endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.url = '/health/'
    
    def test_health_check_success(self):
        """Тест: успешная проверка health"""
        response = self.client.get(self.url)
        
        assert response.status_code in [200, 503]  # Может быть 503 если сервисы недоступны
        assert 'status' in response.json()
        assert 'timestamp' in response.json()
        assert 'checks' in response.json()
    
    def test_health_check_structure(self):
        """Тест: структура ответа health check"""
        response = self.client.get(self.url)
        data = response.json()
        
        assert 'status' in data
        assert 'timestamp' in data
        assert 'checks' in data
        assert 'summary' in data
        
        # Проверяем структуру summary
        assert 'total' in data['summary']
        assert 'healthy' in data['summary']
        assert 'unhealthy' in data['summary']
    
    def test_health_check_database_check(self):
        """Тест: проверка health check базы данных"""
        response = self.client.get(self.url)
        data = response.json()
        
        assert 'database' in data['checks']
        db_check = data['checks']['database']
        
        assert 'status' in db_check
        # Если БД работает, статус должен быть healthy
        if db_check['status'] == 'healthy':
            assert 'latency_ms' in db_check
    
    def test_health_check_cache_check(self):
        """Тест: проверка health check cache"""
        response = self.client.get(self.url)
        data = response.json()
        
        assert 'cache' in data['checks']
        cache_check = data['checks']['cache']
        
        assert 'status' in cache_check
    
    def test_health_check_allowing_anonymous(self):
        """Тест: health check доступен без авторизации"""
        response = self.client.get(self.url)
        
        # Должен быть доступен без авторизации
        assert response.status_code in [200, 503]


@pytest.mark.django_db
class TestDetailedHealthCheckView:
    """Тесты для детального health check endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.url = '/health/detailed/'
    
    def test_detailed_health_check_success(self):
        """Тест: успешная детальная проверка"""
        response = self.client.get(self.url)
        
        assert response.status_code == 200
        assert 'status' in response.json()
        assert 'version' in response.json()
        assert 'configuration' in response.json()
    
    def test_detailed_health_check_version_info(self):
        """Тест: информация о версиях в детальном health check"""
        response = self.client.get(self.url)
        data = response.json()
        
        assert 'version' in data
        assert 'python' in data['version']
        assert 'django' in data['version']
    
    def test_detailed_health_check_configuration(self):
        """Тест: информация о конфигурации"""
        response = self.client.get(self.url)
        data = response.json()
        
        assert 'configuration' in data
        assert 'debug' in data['configuration']
        assert 'timezone' in data['configuration']
    
    def test_detailed_health_check_services(self):
        """Тест: информация о сервисах"""
        response = self.client.get(self.url)
        data = response.json()
        
        assert 'services' in data
        assert 'ollama' in data['services']
        assert 'google' in data['services']


class TestHealthCheckComponents:
    """Тесты для компонентов health check"""
    
    def test_database_connection(self):
        """Тест: подключение к базе данных"""
        # Проверяем что можем подключиться
        connection.ensure_connection()
        
        # Проверяем что можем выполнить запрос
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
        
        assert result[0] == 1
    
    def test_cache_set_get(self):
        """Тест: работа cache"""
        test_key = 'test_health_check'
        test_value = 'ok'
        
        # Устанавливаем значение
        cache.set(test_key, test_value, timeout=10)
        
        # Получаем значение
        result = cache.get(test_key)
        
        assert result == test_value
        
        # Очищаем
        cache.delete(test_key)
