# 📅 Настройка Google Calendar API для создания событий

Полная инструкция по настройке создания событий в Google Calendar через ваше приложение.

---

## 🔑 Шаг 1: Создание проекта в Google Cloud Console

### 1.1. Откройте Google Cloud Console
Перейдите на https://console.cloud.google.com/

### 1.2. Создайте новый проект
1. Нажмите **"Select a project"** → **"NEW PROJECT"**
2. Введите название: `SmartScheduler` или любое другое
3. Нажмите **"CREATE"**

### 1.3. Включите Google Calendar API
1. В меню слева выберите **"APIs & Services"** → **"Library"**
2. Найдите **"Google Calendar API"**
3. Нажмите на него и нажмите **"ENABLE"**

---

## 🔐 Шаг 2: Настройка OAuth 2.0

### 2.1. Создайте OAuth consent screen
1. Перейдите в **"APIs & Services"** → **"OAuth consent screen"**
2. Выберите **"External"** (если у вас нет Google Workspace)
3. Нажмите **"CREATE"**

### 2.2. Заполните информацию о приложении
```
App name: SmartScheduler
User support email: ваш-email@gmail.com
App logo: (опционально)
App domain: http://localhost:8000 (для разработки)
Developer contact: ваш-email@gmail.com
```

### 2.3. Добавьте scopes
Нажмите **"ADD OR REMOVE SCOPES"** и добавьте:
- `.../auth/calendar` - Полный доступ к календарю
- `.../auth/calendar.events` - Управление событиями
- `.../auth/userinfo.email` - Доступ к email

### 2.4. Добавьте тестовых пользователей
1. Перейдите в **"Test users"**
2. Нажмите **"ADD USERS"**
3. Добавьте ваш Google email (например, `your-email@gmail.com`)

---

## 📝 Шаг 3: Создание OAuth credentials

### 3.1. Создайте OAuth client ID
1. Перейдите в **"APIs & Services"** → **"Credentials"**
2. Нажмите **"CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Выберите **"Web application"**

### 3.2. Настройте redirect URI
```
Authorized JavaScript origins:
  - http://localhost:8000
  - http://localhost:4028

Authorized redirect URIs:
  - http://localhost:8000/parse_calendar/oauth2callback/
```

### 3.3. Скачайте credentials
1. После создания нажмите **"DOWNLOAD JSON"**
2. Сохраните файл как `client_secrets.json`
3. Поместите его в директорию `/backend/`:
   ```
   /home/ivan/Рабочий стол/Projects/schedule/schedule_unified/backend/client_secrets.json
   ```

---

## ⚙️ Шаг 4: Настройка приложения

### 4.1. Проверьте settings.py
Убедитесь, что в `/backend/backend/settings.py` указаны правильные scopes:

```python
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.email',
]
```

### 4.2. Установите зависимости
```bash
cd /home/ivan/Рабочий стол/Projects/schedule/schedule_unified/backend
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 4.3. Запустите миграции (если нужно)
```bash
python manage.py migrate
```

### 4.4. Запустите сервер
```bash
python manage.py runserver
```

---

## 🚀 Шаг 5: Использование

### 5.1. Авторизация в Google Calendar

#### Через браузер:
1. Откройте http://localhost:8000/parse_calendar/authorize/
2. Войдите в свой Google аккаунт
3. Разрешите доступ к календарю
4. Вас перенаправит на страницу входа Skyeng (если нужно)

#### Через frontend:
1. Откройте http://localhost:4028/google-auth
2. Нажмите **"Подключить Google Calendar"**
3. Пройдите авторизацию

### 5.2. Создание события через API

#### POST запрос:
```bash
curl -X POST http://localhost:8000/parse_calendar/events/create/ \
  -H "Content-Type: application/json" \
  --cookie "sessionid=YOUR_SESSION_ID" \
  -d '{
    "summary": "Встреча с командой",
    "start_datetime": "2024-04-02T15:00:00",
    "end_datetime": "2024-04-02T16:00:00",
    "description": "Обсуждение проекта",
    "location": "Офис",
    "attendees": ["colleague@example.com"],
    "category": "work",
    "priority": "high"
  }'
```

#### Ответ:
```json
{
  "success": true,
  "event": {
    "id": "abc123xyz",
    "summary": "Встреча с командой",
    "start": {"dateTime": "2024-04-02T15:00:00+03:00"},
    "end": {"dateTime": "2024-04-02T16:00:00+03:00"},
    "html_link": "https://calendar.google.com/..."
  },
  "message": "Событие успешно создано"
}
```

### 5.3. Создание события через frontend

1. Откройте http://localhost:4028/google-calendar-integration
2. Прокрутите вниз до **"Создать событие в Google Calendar"**
3. Заполните форму:
   - Название события
   - Время начала и окончания
   - Описание (опционально)
   - Местоположение (опционально)
   - Участники (опционально)
4. Нажмите **"Проверить конфликты и создать"** или **"Создать событие"**

### 5.4. Проверка конфликтов

```bash
curl -X POST http://localhost:8000/parse_calendar/events/check-conflict/ \
  -H "Content-Type: application/json" \
  --cookie "sessionid=YOUR_SESSION_ID" \
  -d '{
    "start_datetime": "2024-04-02T15:00:00",
    "end_datetime": "2024-04-02T16:00:00"
  }'
```

### 5.5. Поиск свободного времени

```bash
curl -X POST http://localhost:8000/parse_calendar/events/find-free-time/ \
  -H "Content-Type: application/json" \
  --cookie "sessionid=YOUR_SESSION_ID" \
  -d '{
    "duration_minutes": 60,
    "date_start": "2024-04-01",
    "date_end": "2024-04-07",
    "working_hours_start": 9,
    "working_hours_end": 18
  }'
```

---

## 🧪 Шаг 6: Тестирование

### 6.1. Проверка авторизации
```bash
curl http://localhost:8000/parse_calendar/status/ \
  --cookie "sessionid=YOUR_SESSION_ID"
```

### 6.2. Получение списка событий
```bash
curl "http://localhost:8000/parse_calendar/events/?start_date=2024-04-01&end_date=2024-04-30" \
  --cookie "sessionid=YOUR_SESSION_ID"
```

### 6.3. Обновление события
```bash
curl -X PATCH http://localhost:8000/parse_calendar/events/EVENT_ID/update/ \
  -H "Content-Type: application/json" \
  --cookie "sessionid=YOUR_SESSION_ID" \
  -d '{
    "summary": "Новое название",
    "start_datetime": "2024-04-02T16:00:00",
    "end_datetime": "2024-04-02T17:00:00"
  }'
```

### 6.4. Удаление события
```bash
curl -X DELETE http://localhost:8000/parse_calendar/events/EVENT_ID/delete/ \
  --cookie "sessionid=YOUR_SESSION_ID"
```

---

## 🔧 Решение проблем

### Ошибка: "Client secrets file not found"
**Решение:** Убедитесь, что файл `client_secrets.json` находится в `/backend/`

### Ошибка: "insufficientPermission"
**Решение:** 
1. Проверьте scopes в settings.py
2. Перепройдите авторизацию
3. Проверьте, что пользователь добавлен в тестовые

### Ошибка: "redirect_uri_mismatch"
**Решение:** 
1. Проверьте redirect URI в Google Cloud Console
2. Убедитесь, что он совпадает с `GOOGLE_REDIRECT_URI` в settings.py

### Ошибка: "invalid_grant"
**Решение:** 
1. Время на сервере должно быть синхронизировано
2. Перепройдите авторизацию

---

## 📊 API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/parse_calendar/authorize/` | GET | Начало OAuth авторизации |
| `/parse_calendar/oauth2callback/` | GET | Callback от Google OAuth |
| `/parse_calendar/logout/` | POST | Выход из Google Calendar |
| `/parse_calendar/status/` | GET | Проверка статуса авторизации |
| `/parse_calendar/events/` | GET | Получение списка событий |
| `/parse_calendar/events/create/` | POST | Создание события |
| `/parse_calendar/events/{id}/update/` | PATCH | Обновление события |
| `/parse_calendar/events/{id}/delete/` | DELETE | Удаление события |
| `/parse_calendar/events/check-conflict/` | POST | Проверка конфликтов |
| `/parse_calendar/events/find-free-time/` | POST | Поиск свободного времени |

---

## 🎯 Примеры использования

### Python (requests)
```python
import requests
from datetime import datetime, timedelta

# Авторизация (через браузер)
# ... после авторизации получите sessionid из cookies

# Создание события
session = requests.Session()
session.cookies.set('sessionid', 'YOUR_SESSION_ID')

response = session.post(
    'http://localhost:8000/parse_calendar/events/create/',
    json={
        'summary': 'Встреча с командой',
        'start_datetime': (datetime.now() + timedelta(days=1)).isoformat(),
        'end_datetime': (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
        'description': 'Еженедельная встреча',
        'location': 'Zoom',
    }
)

print(response.json())
```

### JavaScript (fetch)
```javascript
// Создание события
const response = await fetch('http://localhost:8000/parse_calendar/events/create/', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    summary: 'Встреча с командой',
    start_datetime: '2024-04-02T15:00:00',
    end_datetime: '2024-04-02T16:00:00',
    description: 'Обсуждение проекта',
  }),
});

const data = await response.json();
console.log(data);
```

---

## ✅ Чеклист готовности

- [ ] Проект создан в Google Cloud Console
- [ ] Google Calendar API включён
- [ ] OAuth consent screen настроен
- [ ] OAuth client ID создан
- [ ] Файл `client_secrets.json` загружен в `/backend/`
- [ ] Scopes настроены правильно
- [ ] Авторизация работает
- [ ] Создание событий работает
- [ ] Проверка конфликтов работает
- [ ] Поиск свободного времени работает

---

## 🎉 Готово!

Теперь вы можете:
- ✅ Создавать события в Google Calendar через API
- ✅ Создавать события через frontend интерфейс
- ✅ Проверять конфликты перед созданием
- ✅ Находить свободное время
- ✅ Обновлять и удалять события
- ✅ Приглашать участников на встречи

Все изменения синхронизируются с вашим реальным Google Calendar!
