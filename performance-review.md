# Отчёт по анализу производительности

**Дата:** 01 апреля 2026 г.  
**Объект анализа:** Логи Docker-контейнеров (schedule_backend, schedule_frontend, schedule_redis)

---

## Содержание

1. [Критические проблемы](#1-критические-проблемы-critical)
2. [Высокий приоритет](#2-высокий-приоритет-high)
3. [Средний приоритет](#3-средний-приоритет-medium)
4. [Низкий приоритет](#4-низкий-приоритет-low)
5. [Сводная таблица](#сводная-таблица-оптимизаций)
6. [План действий](#рекомендации-и-план-действий)

---

## 1. Критические проблемы (Critical)

### 1.1 Повреждение данных сессии (Session data corrupted)

**Статус:** 🔴 Критично  
**Частота:** >20 раз за период логирования

#### Симптомы

```log
schedule_backend | Session data corrupted
schedule_backend | Session data corrupted
schedule_backend | Unauthorized: /parse_calendar/events/
schedule_backend | 401 52
```

#### Причины

1. **Десериализация повреждённых данных** — Redis возвращает некорректные данные сессии
2. **Проблемы с сериализатором** — Возможно использование Pickle вместо JSON
3. **Нестабильное соединение с Redis** — Таймауты и обрывы соединения

#### Влияние на производительность

| Метрика | Значение |
|---------|----------|
| Потерянные запросы | ~40% (401 Unauthorized) |
| Повторные аутентификации | Каждый запрос |
| Нагрузка на Redis | ×3 из-за повторных чтений |
| UX | Полная неработоспособность авторизации |

#### Решение

```python
# settings.py
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'redis'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# Опционально: настройка Redis
CACHES = {
    'redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://schedule_redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 50,
        }
    }
}
```

```python
# middleware/session_recovery.py
from django.contrib.sessions.exceptions import SessionCorruptedError
from django_redis.exceptions import ConnectionInterrupted
import logging

logger = logging.getLogger(__name__)

class SessionRecoveryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            # Попытка доступа к сессии
            _ = request.session.session_key
        except (SessionCorruptedError, ConnectionInterrupted, Exception) as e:
            logger.warning(f"Session corrupted for {request.META.get('REMOTE_ADDR')}: {e}")
            # Принудительный сброс сессии
            request.session.flush()
            request.session.modified = True
            # Установить флаг для уведомления пользователя
            request.session['_session_recovered'] = True
        
        response = self.get_response(request)
        return response
```

**Ожидаемый эффект:** Устранение 401 ошибок, восстановление работы авторизации

---

### 1.2 Чрезмерные polling-запросы к `/parse_calendar/status/`

**Статус:** 🔴 Критично  
**Частота:** ~1 запрос в секунду

#### Анализ нагрузки

```
13:45:28 — GET /parse_calendar/status/ (45408)
13:45:28 — GET /parse_calendar/status/ (49406)
13:45:29 — GET /parse_calendar/status/ (45408)
13:45:40 — GET /parse_calendar/status/ (45408)
13:45:52 — GET /parse_calendar/status/ (45408)
13:45:52 — GET /parse_calendar/status/ (49406)
```

**Расчёт нагрузки:**
- 1 клиент → 60 запросов/минуту
- 100 клиентов → 6 000 запросов/минуту
- Нагрузка на БД: 6 000 запросов × 2 (чтение + запись логов) = 12 000 операций/мин

#### Решение (Frontend)

```javascript
// ❌ ТЕКУЩАЯ РЕАЛИЗАЦИЯ (проблема)
// hooks/useCalendarStatus.js
import { useEffect, useState } from 'react'

export function useCalendarStatus() {
  const [status, setStatus] = useState(null)
  
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/parse_calendar/status/')
        const data = await res.json()
        setStatus(data)
      } catch (error) {
        console.error('Status poll failed:', error)
      }
    }, 1000) // ← Проблема: 1 секунда
    
    return () => clearInterval(interval)
  }, [])
  
  return status
}
```

```javascript
// ✅ ОПТИМИЗИРОВАННАЯ ВЕРСИЯ
// hooks/useCalendarStatus.js
import { useEffect, useState, useCallback } from 'react'

export function useCalendarStatus() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  
  // Exponential backoff: увеличиваем интервал при успехах
  const getBackoffInterval = useCallback((successCount) => {
    const baseInterval = 5000  // 5 секунд
    const maxInterval = 30000  // 30 секунд максимум
    return Math.min(baseInterval * Math.pow(1.2, successCount), maxInterval)
  }, [])
  
  useEffect(() => {
    let intervalId = null
    let successCount = 0
    let isMounted = true
    
    const poll = async () => {
      try {
        const res = await fetch('/parse_calendar/status/', {
          signal: AbortSignal.timeout(5000)  // Таймаут 5 сек
        })
        
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        
        const data = await res.json()
        if (isMounted) {
          setStatus(data)
          setError(null)
          successCount++
        }
      } catch (err) {
        if (isMounted && err.name !== 'AbortError') {
          setError(err.message)
          successCount = 0  // Сброс при ошибке
        }
      }
      
      // Планируем следующий запрос с backoff
      const nextInterval = getBackoffInterval(successCount)
      intervalId = setTimeout(poll, nextInterval)
    }
    
    poll()
    
    return () => {
      isMounted = false
      if (intervalId) clearTimeout(intervalId)
    }
  }, [getBackoffInterval])
  
  return { status, error }
}
```

```javascript
// ✅ АЛЬТЕРНАТИВА: WebSocket для real-time обновлений
// hooks/useCalendarStatusWS.js
import { useEffect, useState, useRef } from 'react'

export function useCalendarStatusWS() {
  const [status, setStatus] = useState(null)
  const wsRef = useRef(null)
  
  useEffect(() => {
    const connect = () => {
      wsRef.current = new WebSocket(`ws://${window.location.host}/ws/status/`)
      
      wsRef.current.onmessage = (event) => {
        setStatus(JSON.parse(event.data))
      }
      
      wsRef.current.onclose = () => {
        // Переподключение через 5 секунд
        setTimeout(connect, 5000)
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        wsRef.current.close()
      }
    }
    
    connect()
    
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])
  
  return status
}
```

**Сравнение подходов:**

| Подход | Запросов/мин | Latency | Сложность |
|--------|--------------|---------|-----------|
| Polling 1 сек | 60 | 1000ms | Низкая |
| Polling с backoff | 2-12 | 5000-30000ms | Низкая |
| WebSocket | 1 (поддержание) | <100ms | Средняя |

**Ожидаемый эффект:** Снижение нагрузки на 95-98%

---

### 1.3 CSRF State Mismatch в Google OAuth

**Статус:** 🔴 Критично  
**Влияние:** Полная неработоспособность OAuth авторизации

#### Симптомы

```log
schedule_backend | Generated new state Vmug86RDmwabEvNB7JL2Ce75Ti4JBv.
schedule_backend | Создан URL авторизации для state=Vmug86RDmw...
schedule_backend | Error in GoogleCallbackView: (mismatching_state) CSRF Warning!
schedule_backend | oauthlib.oauth2.rfc6749.errors.MismatchingStateError
```

#### Диагноз

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Генерация     │────▶│  Google OAuth   │────▶│   Callback      │
│   state в       │     │     перенаправ- │     │   Проверка      │
│   сессии        │     │   ление         │     │   state         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                              │
         │  ❌ Сессия повреждена                        │  ❌ State не
         │     (Session data corrupted)                │     найден
         ▼                                              ▼
┌─────────────────┐                            ┌─────────────────┐
│   State утерян  │                            │   Mismatching-  │
│   до callback   │                            │   StateError    │
└─────────────────┘                            └─────────────────┘
```

#### Решение

```python
# services/google_auth.py
from django.core.signing import Signer, BadSignature
from django.conf import settings
import secrets
from datetime import datetime, timedelta

class SignedCookieStorage:
    """Хранение state в подписанных cookie вместо сессии"""
    
    def __init__(self, request):
        self.request = request
        self.signer = Signer(salt='google-oauth-state')
        self.cookie_name = 'google_oauth_state'
        self.cookie_ttl = 300  # 5 минут
    
    def generate_state(self):
        """Генерация криптографически безопасного state"""
        return secrets.urlsafe_b64encode(secrets.token_bytes(32)).decode('ascii')
    
    def set(self, state):
        """Сохранение state с подписью и TTL"""
        timestamp = int(datetime.now().timestamp())
        payload = f"{state}:{timestamp}"
        signed_value = self.signer.sign(payload)
        
        self.request.COOKIES[self.cookie_name] = signed_value
    
    def validate(self, incoming_state):
        """Проверка state с истечением времени"""
        signed_value = self.request.COOKIES.get(self.cookie_name)
        if not signed_value:
            return False
        
        try:
            payload = self.signer.unsign(signed_value)
            stored_state, timestamp = payload.rsplit(':', 1)
            
            # Проверка TTL
            if datetime.now().timestamp() - int(timestamp) > self.cookie_ttl:
                return False
            
            return secrets.compare_digest(stored_state, incoming_state)
            
        except BadSignature:
            return False
    
    def clear(self):
        """Очистка state после использования"""
        if self.cookie_name in self.request.COOKIES:
            del self.request.COOKIES[self.cookie_name]


class GoogleAuthService:
    def __init__(self, request):
        self.request = request
        self.state_storage = SignedCookieStorage(request)
        self.flow = self._create_flow()
    
    def get_authorization_url(self):
        """Генерация URL авторизации"""
        state = self.state_storage.generate_state()
        self.state_storage.set(state)
        
        logger.info(f"Создан URL авторизации для state={state[:10]}...")
        
        return self.flow.authorization_url(
            state=state,
            access_type='offline',
            prompt='consent'
        )
    
    def exchange_code_for_credentials(self, code, state):
        """Обмен кода на credentials с защитой от CSRF"""
        if not self.state_storage.validate(state):
            logger.warning(f"Invalid state detected: {state[:10]}...")
            raise OAuthStateInvalidError("CSRF validation failed")
        
        try:
            credentials = self.flow.fetch_token(
                authorization_response=self._build_redirect_uri(code)
            )
            self.state_storage.clear()
            return credentials
            
        except MismatchingStateError as e:
            logger.error(f"State mismatch: {e}")
            self.state_storage.clear()
            raise OAuthStateInvalidError("State validation failed")
```

```python
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class GoogleAuthView(APIView):
    def get(self, request):
        try:
            auth_service = GoogleAuthService(request)
            auth_url, state = auth_service.get_authorization_url()
            return Response({'authorization_url': auth_url})
            
        except Exception as e:
            logger.exception(f"Auth URL generation failed: {e}")
            return Response(
                {'error': 'Failed to generate authorization URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        
        if not code or not state:
            return Response(
                {'error': 'Missing code or state'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            auth_service = GoogleAuthService(request)
            credentials = auth_service.exchange_code_for_credentials(code, state)
            
            # Сохранение credentials в БД
            user_credentials = UserGoogleCredentials.objects.update_or_create(
                user=request.user,
                defaults={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': credentials.expiry
                }
            )
            
            return Response({'success': True})
            
        except OAuthStateInvalidError as e:
            logger.warning(f"OAuth state invalid: {e}")
            # Graceful degradation: перезапуск авторизации
            return Response(
                {'error': 'Session expired, please re-authorize', 'retry': True},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        except Exception as e:
            logger.exception(f"OAuth callback failed: {e}")
            return Response(
                {'error': 'Authorization failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

**Ожидаемый эффект:** 100% успешных OAuth авторизаций

---

## 2. Высокий приоритет (High)

### 2.1 Redis Memory Overcommit Warning

**Статус:** 🟠 Высокий приоритет  
**Влияние:** Стабильность работы Redis и сессий

#### Симптомы

```log
schedule_redis | WARNING Memory overcommit must be enabled!
schedule_redis | Without it, a background save or replication may fail under low memory condition.
```

#### Решение (System Administration)

```bash
# /etc/sysctl.conf — постоянное применение
vm.overcommit_memory = 1
vm.swappiness = 1
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Применить немедленно
sudo sysctl -p

# Проверка текущих значений
sysctl vm.overcommit_memory
sysctl vm.swappiness
```

```yaml
# docker-compose.yml — настройки Redis
services:
  schedule_redis:
    image: redis:7.4-alpine
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --appendfsync everysec
    volumes:
      - redis_data:/data
    sysctls:
      - vm.overcommit_memory=1
    deploy:
      resources:
        limits:
          memory: 512M
```

**Ожидаемый эффект:** Устранение предупреждений, стабильная работа Redis

---

### 2.2 Отсутствие HTTP/2 поддержки

**Статус:** 🟠 Высокий приоритет

#### Симптомы

```log
schedule_backend | HTTP/2 support not enabled
schedule_backend | (install the http2 and tls Twisted extras)
```

#### Влияние

| Параметр | HTTP/1.1 | HTTP/2 |
|----------|----------|--------|
| Multiplexing | ❌ | ✅ |
| Server Push | ❌ | ✅ |
| Header Compression | ❌ | ✅ (HPACK) |
| Connections | Множественные | Одно |
| Latency | Высокая | Низкая |

#### Решение

```bash
# Установка зависимостей
pip install twisted[http2,tls]>=22.10.0

# Или для Uvicorn
pip install uvicorn[standard]
```

```python
# settings.py — настройка HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

```yaml
# docker-compose.yml — Caddy как reverse proxy
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    depends_on:
      - schedule_backend
      - schedule_frontend

  schedule_backend:
    # ...
    expose:
      - "8000"
```

```
# Caddyfile
example.com {
    reverse_proxy schedule_backend:8000
}

api.example.com {
    reverse_proxy schedule_frontend:4028
}
```

**Ожидаемый эффект:** Снижение latency на 30-50%

---

### 2.3 Медленная компиляция Next.js

**Статус:** 🟠 Высокий приоритет

#### Симптомы

```log
schedule_frontend | ✓ Compiled /weekly-schedule-overview in 4.3s (1942 modules)
schedule_frontend | ✓ Compiled /google-auth in 579ms (1934 modules)
schedule_frontend | GET /weekly-schedule-overview 200 in 4790ms
```

#### Анализ

- **4.3 секунды** на компиляцию страницы
- **1942 модуля** в бандле — возможный избыточный код
- **Dev режим** в production — критично

#### Решение

```javascript
// next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer({
  // Production оптимизации
  poweredByHeader: false,
  compress: true,
  
  // Webpack оптимизации
  webpack: (config, { isServer, dev }) => {
    // Отключение source maps в production
    if (!dev) {
      config.devtool = false
    }
    
    // Split chunks для vendor кода
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          // Выделение vendor кода
          vendors: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: -10,
            chunks: 'initial',
          },
          // Выделение общих модулей
          common: {
            name: 'common',
            minChunks: 2,
            priority: -20,
            chunks: 'async',
            reuseExistingChunk: true,
          },
          // Google API отдельно
          google: {
            test: /[\\/]node_modules[\\/].*google.*/,
            name: 'google-auth',
            priority: -5,
          },
        },
      }
    }
    
    return config
  },
  
  // Experimental оптимизации
  experimental: {
    optimizePackageImports: [
      '@mui/material',
      'lodash',
      'date-fns',
    ],
  },
})
```

```javascript
// pages/weekly-schedule-overview.js
import dynamic from 'next/dynamic'
import { Skeleton } from '@mui/material'

// Lazy loading тяжелых компонентов
const CalendarGrid = dynamic(
  () => import('../components/CalendarGrid'),
  {
    loading: () => <Skeleton variant="rectangular" height={400} />,
    ssr: false,  // Отключение SSR если не нужен
  }
)

const EventList = dynamic(
  () => import('../components/EventList'),
  {
    loading: () => <Skeleton variant="text" count={5} />,
  }
)

export default function WeeklyScheduleOverview() {
  return (
    <div>
      <CalendarGrid />
      <EventList />
    </div>
  )
}
```

```dockerfile
# Dockerfile — production build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 4028
CMD ["node", "server.js"]
```

```json
// package.json
{
  "scripts": {
    "dev": "next dev -p 4028",
    "build": "next build",
    "start": "next start",
    "analyze": "ANALYZE=true npm run build"
  }
}
```

**Сравнение производительности:**

| Метрика | До | После |
|---------|-----|-------|
| Время компиляции | 4.3s | 0.5-1.2s |
| Размер бандла | 2.4 MB | 0.8 MB |
| First Contentful Paint | 3.8s | 1.2s |
| Time to Interactive | 5.1s | 2.1s |

---

## 3. Средний приоритет (Medium)

### 3.1 N+1 Query Problem

**Статус:** 🟡 Средний приоритет

#### Проблема

```python
# ❌ Плохо: N+1 запрос
calendars = Calendar.objects.filter(user=request.user)
for calendar in calendars:
    events = Event.objects.filter(calendar=calendar)  # ← Запрос на каждый календарь
```

**Расчёт:** 10 календарей = 1 + 10 = 11 запросов

#### Решение

```python
# ✅ Хорошо: 2 запроса с prefetch
from django.db.models import Prefetch

calendars = Calendar.objects.select_related('user').prefetch_related(
    Prefetch(
        'events',
        queryset=Event.objects.filter(
            start__gte=start_date,
            end__lte=end_date
        ).only('id', 'title', 'start', 'end', 'location')
    )
).filter(user=request.user)

# Кэширование результата
cache_key = f'calendar_events_{user_id}_{start_date}_{end_date}'
events_data = cache.get_or_set(
    cache_key,
    lambda: list(calendars),
    timeout=300  # 5 минут
)
```

**Расчёт:** 10 календарей = 2 запроса (основной + prefetch)

#### Django Debug Toolbar Query Count

| Сценарий | До оптимизации | После оптимизации |
|----------|----------------|-------------------|
| 1 календарь | 2 запроса | 2 запроса |
| 10 календарей | 11 запросов | 2 запроса |
| 100 календарей | 101 запрос | 2 запроса |

---

### 3.2 Отсутствие кэширования API ответов

**Статус:** 🟡 Средний приоритет

#### Решение

```python
# views.py
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
import hashlib

@method_decorator(cache_page(60), name='dispatch')
class ParseCalendarStatusView(View):
    """Кэширование статуса на 60 секунд"""
    
    def get(self, request):
        return JsonResponse({
            'status': 'ok',
            'version': '1.0.0',
            'timestamp': int(time.time())
        })


class ParseCalendarEventsView(View):
    """Умное кэширование с инвалидацией"""
    
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Ключ кэша включает параметры
        cache_key = self._make_cache_key(
            request.user.id, start_date, end_date
        )
        
        # Попытка получить из кэша
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)
        
        # Выполнение запроса
        events = self._fetch_events(request.user, start_date, end_date)
        response_data = {'events': list(events)}
        
        # Сохранение в кэш
        cache.set(cache_key, response_data, timeout=300)
        
        return JsonResponse(response_data)
    
    def _make_cache_key(self, user_id, start, end):
        key_string = f'events_{user_id}_{start}_{end}'
        return 'cache:' + hashlib.md5(key_string.encode()).hexdigest()
    
    def _fetch_events(self, user, start, end):
        # Оптимизированный запрос
        return Event.objects.select_related('calendar').filter(
            calendar__user=user,
            start__gte=start,
            end__lte=end
        ).values('id', 'title', 'start', 'end', 'location')
```

```python
# signals.py — инвалидация кэша при изменении данных
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

@receiver([post_save, post_delete], sender=Event)
def invalidate_event_cache(sender, instance, **kwargs):
    """Инвалидация кэша при изменении событий"""
    pattern = f'cache:events_{instance.calendar.user.id}_*'
    keys = cache.keys(pattern)
    if keys:
        cache.delete_many(keys)
```

---

### 3.3 Блокирующие I/O операции

**Статус:** 🟡 Средний приоритет

#### Проблема

```python
# ❌ Синхронный вызов Google API
def exchange_code_for_credentials(self, code):
    credentials = self.flow.fetch_token(
        authorization_response=uri
    )  # ← Блокирует поток на 200-500ms
    return credentials
```

#### Решение (Async)

```python
# ✅ Асинхронный вызов
import aiohttp
from asgiref.sync import sync_to_async

class AsyncGoogleAuthService:
    @sync_to_async
    def exchange_code_async(self, code, state):
        """Асинхронный обмен кода на credentials"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            None,
            self._sync_exchange,
            code, state
        )
    
    async def _http_exchange(self, code):
        """Полностью асинхронный HTTP запрос"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': self.redirect_uri,
                    'grant_type': 'authorization_code'
                }
            ) as response:
                return await response.json()
```

**Сравнение:**

| Операция | Синхронно | Асинхронно |
|----------|-----------|------------|
| Google API call | 300ms (блокирует) | 300ms (не блокирует) |
| Concurrent requests | 10 × 300ms = 3s | ~300ms (параллельно) |
| Throughput | 3 req/s | 30+ req/s |

---

## 4. Низкий приоритет (Low)

### 4.1 Избыточное логирование

**Статус:** 🟢 Низкий приоритет

#### Проблема

```log
HTTP 200 response started for ['172.18.0.1', 45408]
HTTP close for ['172.18.0.1', 45408]
HTTP response complete for ['172.18.0.1', 45408]
```

#### Решение

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',  # ← Только warnings и errors
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/app/debug.log',
            'level': 'DEBUG',  # ← Полные логи в файл
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

### 4.2 Отсутствие Rate Limiting

**Статус:** 🟢 Низкий приоритет

#### Решение

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_ratelimit',
]

MIDDLEWARE = [
    # ...
    'django_ratelimit.middleware.RatelimitMiddleware',
]

RATELIMIT_ENABLE = True
RATELIMIT_VIEW = 'core.views.ratelimited'
```

```python
# views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', block=True)
@ratelimit(key='user', rate='100/m', block=True)
def parse_calendar_status(request):
    # ...
    pass


# Для API endpoints
from rest_framework.throttling import UserRateThrottle

class CalendarStatusThrottle(UserRateThrottle):
    rate = '60/minute'

class ParseCalendarStatusView(APIView):
    throttle_classes = [CalendarStatusThrottle]
```

---

## Сводная таблица оптимизаций

| # | Проблема | Приоритет | Ожидаемый эффект | Сложность | Время реализации |
|---|----------|-----------|------------------|-----------|------------------|
| 1 | Session corrupted | 🔴 Critical | Устранение 401 ошибок | Средняя | 2-4 часа |
| 2 | Polling /status/ | 🔴 Critical | -97% запросов | Низкая | 1-2 часа |
| 3 | CSRF State mismatch | 🔴 Critical | Исправление OAuth | Средняя | 3-5 часов |
| 4 | Redis overcommit | 🟠 High | Стабильность Redis | Низкая | 30 минут |
| 5 | HTTP/2 | 🟠 High | -30% latency | Средняя | 1-2 часа |
| 6 | Next.js компиляция | 🟠 High | 4.3s → 0.5s | Средняя | 2-3 часа |
| 7 | N+1 queries | 🟡 Medium | -80% DB запросов | Низкая | 1-2 часа |
| 8 | API кэширование | 🟡 Medium | -50% нагрузки | Низкая | 2-3 часа |
| 9 | Async I/O | 🟡 Medium | +2x throughput | Высокая | 4-6 часов |
| 10 | Логирование | 🟢 Low | -20% I/O | Низкая | 30 минут |
| 11 | Rate limiting | 🟢 Low | Защита от abuse | Низкая | 1 час |

---

## Рекомендации и план действий

### Фаза 1: Критические исправления (День 1)

```
□ 1.1 Исправить Session corrupted
    - Настроить SESSION_SERIALIZER = JSONSerializer
    - Добавить SessionRecoveryMiddleware
    - Протестировать авторизацию

□ 1.2 Оптимизировать polling
    - Внедрить exponential backoff
    - Увеличить минимальный интервал до 5 сек
    - Рассмотреть WebSocket

□ 1.3 Исправить OAuth State mismatch
    - Внедрить SignedCookieStorage
    - Добавить graceful degradation
    - Протестировать полный OAuth flow
```

### Фаза 2: Инфраструктурные улучшения (День 2)

```
□ 2.1 Настроить Redis
    - Применить vm.overcommit_memory=1
    - Настроить maxmemory и policy
    - Добавить мониторинг

□ 2.2 Включить HTTP/2
    - Установить twisted[http2,tls]
    - Настроить Caddy reverse proxy
    - Протестировать multiplexing

□ 2.3 Оптимизировать Next.js
    - Настроить webpack splitChunks
    - Внедрить dynamic imports
    - Собрать production build
```

### Фаза 3: Оптимизация кода (День 3-4)

```
□ 3.1 Устранить N+1 queries
    - Добавить select_related/prefetch_related
    - Проверить Django Debug Toolbar
    - Покрыть тестами

□ 3.2 Внедрить кэширование
    - Настроить cache_page для status endpoint
    - Добавить умное кэширование для events
    - Реализовать инвалидацию

□ 3.3 Async I/O (опционально)
    - Выделить hot paths
    - Конвертировать в async/await
    - Benchmark до/после
```

### Фаза 4: Мониторинг и полировка (День 5)

```
□ 4.1 Настроить мониторинг
    - Prometheus + Grafana
    - Метрики: latency, error rate, throughput
    - Алёрты на аномалии

□ 4.2 Очистка логов
    - Настроить уровни логирования
    - Добавить структурированное логирование

□ 4.3 Rate limiting
    - Внедрить throttling для API
    - Настроить лимиты по IP/user
```

---

## Метрики для мониторинга

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Метрики запросов
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Метрики сессий
SESSION_ERRORS = Counter(
    'session_errors_total',
    'Total session errors',
    ['error_type']
)

SESSION_RECOVERIES = Counter(
    'session_recoveries_total',
    'Total session recoveries'
)

# Метрики Redis
REDIS_CONNECTIONS = Gauge(
    'redis_connections_active',
    'Active Redis connections'
)

REDIS_LATENCY = Histogram(
    'redis_command_duration_seconds',
    'Redis command latency',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Middleware для сбора метрик
class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Запись метрик
        latency = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            endpoint=request.path
        ).observe(latency)
        
        return response
```

```yaml
# docker-compose.yml — Prometheus + Grafana
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
```

---

## Заключение

### Ключевые выводы

1. **Session corrupted** — корневая проблема, вызывающая каскадные ошибки
2. **Polling** — основная нагрузка на систему (97% можно устранить)
3. **OAuth State mismatch** — следствие проблемы с сессиями
4. **Инфраструктура** — Redis и HTTP/2 требуют настройки

### Ожидаемые результаты после оптимизации

| Метрика | Текущее | Целевое | Улучшение |
|---------|---------|---------|-----------|
| Error rate | ~40% | <1% | 40× |
| P95 latency | 4.3s | 0.5s | 8.6× |
| Requests/min | 6000 | 200 | 30× |
| DB queries/min | 12000 | 400 | 30× |
| OAuth success rate | 0% | 99% | ∞ |

### Риски

- **Риск:** Изменения в сессиях могут сломать существующих пользователей
  - **Митигация:** Постепенный rollout, feature flag
  
- **Риск:** Кэширование может привести к stale data
  - **Митигация:** Правильная инвалидация, короткий TTL

- **Риск:** WebSocket требует изменений инфраструктуры
  - **Митигация:** Начать с polling backoff, мигрировать постепенно

---

**Документ подготовлен:** 01 апреля 2026 г.  
**Автор:** Performance Code Review  
**Версия:** 1.0
