# Skyeng Authentication Update

## Изменения

Аутентификация в Skyeng была обновлена для использования **веб-flow** через `id.skyeng.ru` вместо прямого API `/auth/public/login`.

### Почему это было сделано

Прямое API `/auth/public/login` может быть недоступно или требовать дополнительных заголовков. Веб-flow через `id.skyeng.ru` эмулирует обычный браузерный вход пользователя и является более надёжным.

---

## Как это работает

### Flow аутентификации

1. **Получение CSRF-токена**
   - Загружается страница `https://id.skyeng.ru/login`
   - Из HTML извлекается CSRF-токен
   - Создаётся новая `requests.Session` для сохранения cookies

2. **Логин с CSRF-токеном**
   - POST запрос на `https://id.skyeng.ru/frame/login-submit`
   - Данные: `username`, `password`, `csrfToken`
   - Заголовки: `X-CSRF-Token`, `Origin`, `Referer`
   - В ответе: JSON с `success: true/false` и `redirect` URL

3. **SSO редирект**
   - Если в ответе есть `redirect`, выполняется GET запрос
   - Это устанавливает cookies сессии в домене `.skyeng.ru`

4. **Получение API токенов**
   - Пробуем получить данные через API edu-avatar
   - Если успешно - сессия валидна
   - Пробуем получить явный токен через `/api/v2/auth/token`
   - Если не удалось - используем cookies сессии

5. **Создание Credentials**
   - Токен извлекается из cookies или API ответа
   - Создаётся `SkyengCredentials` объект
   - Сохраняются cookies сессии для последующих запросов

---

## Структура ответа

```python
SkyengCredentials(
    token='jwt_token_from_cookies',
    refresh_token='refresh_token_or_none',
    expires_at=datetime(2026, 4, 1, 19, 0, 0),
    user_id=12345,
    email='user@example.com',
    _session_cookies={'session_id': '...', 'JWT': '...'}
)
```

---

## Использование

### Базовая аутентификация

```python
from services.skyeng_auth import SkyengAuthService

auth_service = SkyengAuthService()
credentials = auth_service.authenticate(email, password)
```

### Аутентификация с сохранением сессии

```python
credentials, session = auth_service.authenticate_with_session(
    email='user@example.com',
    password='secret',
    save_session=True
)

# Теперь можно использовать session для запросов
response = session.get('https://edu-avatar.skyeng.ru/api/v2/...')
```

### Восстановление сессии из cookies

```python
# Сохраняем cookies из credentials
cookies = credentials._session_cookies

# Позже восстанавливаем сессию
session = auth_service.create_session_from_cookies(cookies)

# Используем сессию для запросов
response = session.get('https://edu-avatar.skyeng.ru/api/v2/...')
```

---

## Тестирование

### Запуск теста

```bash
cd /home/ivan/Рабочий стол/Projects/schedule/schedule_unified
source .venv/bin/activate

# С переменными окружения
export SKYENG_TEST_EMAIL='your@email.com'
export SKYENG_TEST_PASSWORD='your_password'
python test_skyeng_auth.py

# Или с тестовыми credentials (из test.py)
python test_skyeng_auth.py
```

### Ожидаемый вывод

```
============================================================
Тестирование аутентификации Skyeng
============================================================
Email: penis@yandex.ru
Password: ***
============================================================

Шаг 1: Аутентификация...
✓ Аутентификация успешна!
  User ID: 12345
  Email: penis@yandex.ru
  Token: eyJhbGciOiJIUzI1Ni...
  Refresh Token: None...
  Expires At: 2026-04-01 19:00:00+03:00
  Session Cookies: 5 cookies

Шаг 2: Тест создание сессии из cookies...
✓ Сессия создана, cookies: 5

Шаг 3: Проверка доступа к API...
✓ API доступно! Статус: 200
  Ответ: 1234 байт
  Stream: Physics Course
  Teacher: Иван Иванов
  Lessons: 10 занятий

============================================================
ТЕСТ УСПЕШЕН!
============================================================
```

---

## Интеграция с Django views

Аутентификация в `parse_calendar/views.py` работает без изменений:

```python
# SkyengLoginView.post()
skyeng_credentials = self.skyeng_auth.authenticate(email, password)

# Сохранение в БД
user_creds.set_skyeng_credentials(
    token=skyeng_credentials.token,
    refresh_token=skyeng_credentials.refresh_token,
    expiry=skyeng_credentials.expires_at,
    email=skyeng_credentials.email,
)
```

---

## Зависимости

Все необходимые зависимости уже установлены в `requirements.txt`:

- `beautifulsoup4` - для парсинга HTML
- `requests` - для HTTP запросов
- `tenacity` - для retry логики

---

## Безопасность

### Хранение credentials

- **Токен** и **refresh_token** шифруются в БД
- **Cookies сессии** НЕ сохраняются в БД (поле `_session_cookies` игнорируется при сериализации)
- Cookies можно сохранить в сессии Django для временного использования

### CSRF-токен

- CSRF-токен получается динамически при каждой аутентификации
- Хранится только в памяти во время аутентификации
- Используется один раз

---

## Troubleshooting

### Ошибка: "CSRF-токен не найден"

**Причина:** Страница логина изменилась или недоступна

**Решение:**
1. Проверьте доступность `https://id.skyeng.ru/login`
2. Проверьте User-Agent (должен быть браузерный)
3. Обновите парсинг CSRF в `_get_csrf_token()`

### Ошибка: "Неверный логин или пароль"

**Причина:** Неверные credentials

**Решение:** Проверьте email и пароль

### Ошибка: "Не удалось получить токен доступа"

**Причина:** Сессия не установила cookies

**Решение:**
1. Проверьте, что SSO редирект выполнен
2. Проверьте cookies в сессии: `session.cookies.get_dict()`
3. Попробуйте `authenticate_with_session()` для отладки

### Ошибка: "API вернул ошибку 401"

**Причина:** Токен истёк

**Решение:**
1. Проверьте `credentials.expires_at`
2. Выполните аутентификацию заново
3. В будущем можно реализовать refresh через перевыпуск cookies

---

## Отличия от старой версии

| Старая версия (API) | Новая версия (Web) |
|---------------------|-------------------|
| POST `/auth/public/login` | GET `/login` → POST `/frame/login-submit` |
| JSON payload | Form data + CSRF |
| JWT в ответе | JWT в cookies |
| Refresh через API | Перевыпуск через новый логин |
| Менее надёжно | Более надёжно (эмулирует браузер) |

---

## Файлы

- `backend/services/skyeng_auth.py` - обновлённый сервис аутентификации
- `backend/shared/credentials.py` - добавлено поле `_session_cookies`
- `test_skyeng_auth.py` - тестовый скрипт
- `test.py` - оригинальный скрипт (источник логики)

---

## Дата обновления

2026-04-01
