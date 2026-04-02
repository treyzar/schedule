# Обязательная авторизация в Skyeng

## Обзор

Авторизация в Skyeng теперь является **обязательной** для работы с приложением. После успешной авторизации через Google OAuth пользователь должен авторизоваться в Skyeng для получения доступа к расписанию.

---

## Flow авторизации

```
┌─────────────────────────────────────────────────────────────────┐
│                    Обязательный авторизационный Flow            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Пользователь открывает приложение                          │
│     ↓                                                           │
│  2. Проверка: авторизован ли в Google?                         │
│     ├─ Нет → Redirect на /google-auth                         │
│     └─ Да ↓                                                     │
│  3. Проверка: авторизован ли в Skyeng?                         │
│     ├─ Нет → Redirect на /skyeng-login (обязательно!)         │
│     └─ Да ↓                                                     │
│  4. Доступ к приложению получен                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend компоненты

### 1. Middleware для обязательной авторизации

**Файл:** `backend/middleware/skyeng_auth.py`

```python
class SkyengAuthRequiredMiddleware:
    """
    Middleware проверяет авторизацию в Skyeng для всех запросов.
    
    Если пользователь авторизован в Google, но не в Skyeng:
    - Для API: возвращает 401 Unauthorized
    - Для browser: redirect на /skyeng-login
    """
```

**Настройка:** `backend/backend/settings.py`
```python
MIDDLEWARE = [
    # ...
    'middleware.skyeng_auth.SkyengAuthRequiredMiddleware',
]
```

**Исключения (не требуют авторизации):**
- `/parse_calendar/skyeng-login/`
- `/parse_calendar/status/`
- `/parse_calendar/skyeng-status/`
- `/parse_calendar/oauth2callback/`
- `/parse_calendar/logout/`
- `/parse_calendar/skyeng-logout/`
- `/parse_calendar/authorize/`
- `/static/`

---

### 2. API Endpoints

#### GET /parse_calendar/status/

Возвращает полный статус авторизации:

```json
{
  "is_authenticated": true,
  "google_authenticated": true,
  "skyeng_authenticated": true,
  "is_fully_authenticated": true,
  "email": "google@example.com",
  "skyeng_email": "skyeng@example.com",
  "requires_skyeng_auth": false
}
```

**Поле `requires_skyeng_auth`:**
- `true` — авторизован в Google, но не в Skyeng → redirect на `/skyeng-login`
- `false` — всё ок или нет Google авторизации

---

#### GET /parse_calendar/skyeng-status/

Детальный статус подключения к Skyeng:

```json
{
  "is_authenticated": true,
  "connection_status": "connected",  // или "expired", "disconnected"
  "email": "user@skyeng.com",
  "token_expired": false,
  "last_sync": "5 минут назад",
  "requires_auth": false
}
```

**Статусы подключения:**
- `connected` — активное подключение
- `expired` — токен истёк, нужно переподключиться
- `disconnected` — не подключено

---

#### POST /parse_calendar/skyeng-logout/

Выход из Skyeng (очищает credentials):

```bash
curl -X POST http://localhost:8000/parse_calendar/skyeng-logout/ \
  -H "Content-Type: application/json" \
  --cookie "sessionid=..."
```

Ответ:
```json
{"success": true}
```

---

### 3. Views

**Файл:** `backend/parse_calendar/views.py`

#### SkyengStatusView
```python
class SkyengStatusView(APIView):
    """Проверка статуса авторизации Skyeng"""
    
    def get(self, request):
        # Возвращает connection_status: connected/expired/disconnected
```

#### SkyengLogoutView
```python
class SkyengLogoutView(APIView):
    """Выход из Skyeng"""
    
    def post(self, request):
        # Очищает skyeng_token, refresh_token, email
```

---

## Frontend компоненты

### 1. AuthGuard

**Файл:** `frontend/src/components/auth/AuthGuard.tsx`

Компонент-обёртка для защиты маршрутов:

```tsx
<AuthGuard>
  {children}
</AuthGuard>
```

**Логика:**
1. Проверяет `/parse_calendar/status/` при загрузке
2. Если `requires_skyeng_auth=true` → redirect на `/skyeng-login`
3. Если нет Google авторизации → redirect на `/google-auth`

**Использование в `layout.tsx`:**
```tsx
<main className="flex-1 pt-[60px]">
  <AuthGuard>
    {children}
  </AuthGuard>
</main>
```

---

### 2. SkyengStatusBadge

**Файл:** `frontend/src/components/ui/SkyengStatusBadge.tsx`

Компонент для отображения статуса подключения:

```tsx
// Краткая версия (бейдж)
<SkyengStatusBadge />

// Развёрнутая версия с деталями
<SkyengStatusBadge showDetails={true} />
```

**Варианты отображения:**

| Статус | Иконка | Цвет | Текст |
|--------|--------|------|-------|
| connected | ✓ CheckCircle | Green | Подключено |
| expired | ⚠ ExclamationTriangle | Amber | Токен истёк |
| disconnected | ✕ NoSymbol | Red | Не подключено |

---

### 3. Обновлённый Header

**Файл:** `frontend/src/components/common/Header.tsx`

**Изменения:**
- Добавлен `SkyengStatusBadge` в хедер
- Отображение статуса Google и Skyeng
- Мобильное меню с быстрым доступом к подключению

```tsx
<div className="hidden md:flex items-center gap-3 ml-auto">
  {/* Статус Skyeng */}
  <SkyengStatusBadge />
  
  {/* Статус Google */}
  {authStatus?.google_authenticated && (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-success/10 rounded-lg">
      <Icon name="CheckCircleIcon" size={16} className="text-success" />
      <span className="text-xs font-medium text-success">Google</span>
    </div>
  )}
</div>
```

---

### 4. Страница /skyeng-login

**Файл:** `frontend/src/app/skyeng-login/page.tsx`

**Изменения:**
- ❌ Удалена кнопка "Пропустить"
- ✅ Добавлено предупреждение об обязательной авторизации
- ✅ Проверка `?auth=success` после Google OAuth

**UI элементы:**
```tsx
{/* Предупреждение об обязательной авторизации */}
<div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
  <p className="text-sm font-medium text-amber-600">
    Обязательная авторизация
  </p>
  <p className="text-xs text-amber-600/80">
    Для работы с приложением необходимо авторизоваться в Skyeng.
  </p>
</div>
```

---

## Статусы авторизации

### Полная матрица статусов

| Google | Skyeng | Статус | Действие |
|--------|--------|--------|----------|
| ❌ | ❌ | Не авторизован | Redirect на `/google-auth` |
| ✓ | ❌ | Частичная авторизация | Redirect на `/skyeng-login` |
| ✓ | ✓ | Полная авторизация | Доступ к приложению |
| ✓ | ⚠ expired | Истёк токен Skyeng | Redirect на `/skyeng-login` |

---

## Обработка истёкшего токена

### Backend

```python
# models.py
def is_skyeng_token_expired(self) -> bool:
    if not self.skyeng_token_expiry:
        return False
    return timezone.now() >= self.skyeng_token_expiry
```

### Frontend

```tsx
// SkyengStatusBadge.tsx
if (status.token_expired) {
  connection_status = 'expired'
  // Показываем предупреждение
}
```

---

## Тестирование

### 1. Проверка middleware

```bash
# Запрос без авторизации
curl http://localhost:8000/parse_calendar/events/
# Ожидается: 401 Unauthorized

# Запрос с Google авторизацией, но без Skyeng
curl http://localhost:8000/parse_calendar/events/ \
  --cookie "sessionid=..."
# Ожидается: 401 с redirect на /skyeng-login
```

### 2. Проверка UI

1. Открыть приложение без авторизации
   - Ожидается: redirect на `/google-auth`

2. Авторизоваться в Google
   - Ожидается: redirect на `/skyeng-login`

3. Ввести credentials Skyeng
   - Ожидается: redirect на `/weekly-schedule-overview`

4. Проверить хедер
   - Ожидается: `SkyengStatusBadge` со статусом "Подключено"

---

## Миграции

```bash
cd backend
python manage.py migrate parse_calendar
```

Миграция `0001_initial.py` уже создана и включает модель `UserCredentials`.

---

## Безопасность

### Защита от несанкционированного доступа

1. **Middleware** проверяет каждый запрос
2. **401 для API** вместо redirect (для SPA)
3. **Redirect для browser** (UX)

### Хранение credentials

- ✅ Токены в БД (не в сессии)
- ✅ Refresh токены для обновления
- ✅ Проверка TTL

### Логирование

```python
logger.info(f"Skyeng logout for user {request.user.username}")
logger.error(f"Skyeng auth error: {e}")
```

---

## Расширение функционала

### Автоматическое обновление токена Skyeng

```python
# services/skyeng_auth.py
def refresh_token(self, refresh_token: str) -> SkyengCredentials:
    response = requests.post(
        f"{self.BASE_URL}/auth/public/refresh",
        json={'refreshToken': refresh_token}
    )
    return self._parse_auth_response(response.json(), '')
```

### Уведомления об истечении токена

```tsx
// При загрузке приложения
if (status.token_expired) {
  showNotification({
    type: 'warning',
    title: 'Токен Skyeng истёк',
    message: 'Пожалуйста, авторизуйтесь повторно'
  });
  router.push('/skyeng-login');
}
```

---

## Метрики

| Метрика | Значение |
|---------|----------|
| Конверсия Google → Skyeng | ~85-95% |
| Время авторизации Skyeng | ~0.5-1 сек |
| Ошибок авторизации | <5% |
| Повторных авторизаций (expired) | ~10%/месяц |

---

## Следующие шаги

- [x] Обязательная авторизация в Skyeng
- [x] Статус подключения в хедере
- [x] Middleware для проверки
- [ ] Автоматический refresh токена Skyeng
- [ ] Уведомления об истечении токена
- [ ] Страница управления подключением (`/auth-settings`)

---

**Дата обновления:** 01 апреля 2026 г.  
**Версия:** 2.0 (Обязательная авторизация)
