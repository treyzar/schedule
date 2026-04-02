# 🔐 Skyeng Avatar Integration - Руководство по использованию

## 📋 Обзор

Интеграция с **avatar.skyeng.ru** позволяет автоматически парсить:
- ✅ Уроки по всем предметам (математика, физика, английский и т.д.)
- ✅ Домашние задания
- ✅ Активности пользователя
- ✅ Расписание занятий

---

## 🚀 Быстрый старт

### 1. Авторизация в Skyeng

**Вариант A: Через веб-интерфейс**
```
1. Откройте http://localhost:4028/skyeng-login
2. Введите логин и пароль от Skyeng
3. Нажмите "Войти"
4. После успешного входа вы будете перенаправлены в личный кабинет
```

**Вариант B: Через API**
```bash
curl -X POST http://localhost:8000/parse_avatar/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your@email.com", "password": "yourpassword"}' \
  -c cookies.txt
```

---

## 📡 API Endpoints

### Авторизация

#### `POST /parse_avatar/login/`
Вход в Skyeng с сохранением сессии.

**Request:**
```json
{
  "username": "your@email.com",
  "password": "yourpassword"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Вход выполнен успешно, сессия сохранена.",
  "username": "your@email.com",
  "cookies_saved": ["sessionid", "csrftoken", ...]
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Вход не удался, неверный логин или пароль"
}
```

---

#### `GET /parse_avatar/status/`
Проверка статуса авторизации.

**Response:**
```json
{
  "is_authenticated": true,
  "username": "your@email.com",
  "last_login": "2026-04-01T15:30:00",
  "session_valid": true
}
```

---

#### `POST /parse_avatar/logout/`
Выход из Skyeng (очистка сессии).

**Response:**
```json
{
  "success": true,
  "message": "Выполнен выход из Skyeng"
}
```

---

### Данные

#### `GET /parse_avatar/lessons/`
Получение списка уроков за указанный период.

**Query Parameters:**
- `start_date` (optional): Начало периода в формате ISO (YYYY-MM-DD)
- `end_date` (optional): Конец периода в формате ISO (YYYY-MM-DD)

**Пример запроса:**
```bash
curl "http://localhost:8000/parse_avatar/lessons/?start_date=2026-04-01&end_date=2026-04-30" \
  -b cookies.txt
```

**Response:**
```json
{
  "lessons": [
    {
      "id": 12345,
      "subject": "math",
      "title": "Алгебра: Квадратные уравнения",
      "start_time": "2026-04-05T14:00:00Z",
      "end_time": "2026-04-05T14:45:00Z",
      "duration": 45,
      "teacher": "Иванова Мария",
      "status": "scheduled",
      "room": "Аудитория 301",
      "homework": "Стр. 45, упражнения 1-10",
      "type": "skyeng_lesson"
    },
    {
      "id": 12346,
      "subject": "physics",
      "title": "Физика: Законы Ньютона",
      "start_time": "2026-04-03T16:00:00Z",
      "end_time": "2026-04-03T16:45:00Z",
      "duration": 45,
      "teacher": "Петров Сергей",
      "status": "completed",
      "type": "skyeng_lesson"
    }
  ],
  "total": 2,
  "period": {
    "start": "2026-04-01T00:00:00",
    "end": "2026-04-30T23:59:59"
  },
  "errors": []
}
```

---

#### `GET /parse_avatar/activities/`
Получение всех активностей (уроки + домашние задания + тесты).

**Query Parameters:**
- `start_date` (optional): Начало периода (по умолчанию -30 дней)
- `end_date` (optional): Конец периода (по умолчанию - сегодня)

**Response:**
```json
{
  "activities": [
    {
      "id": 12345,
      "subject": "math",
      "title": "Урок по математике",
      "start_time": "2026-04-05T14:00:00Z",
      "type": "skyeng_lesson",
      "status": "scheduled"
    },
    {
      "id": 67890,
      "subject": "english",
      "title": "Домашнее задание: Present Perfect",
      "due_date": "2026-04-06T23:59:59Z",
      "type": "skyeng_homework",
      "status": "pending"
    }
  ],
  "total": 2,
  "period": {
    "start": "2026-03-02T00:00:00",
    "end": "2026-04-01T23:59:59"
  },
  "errors": []
}
```

---

#### `GET /parse_avatar/all-subjects/`
Получение данных по всем предметам (полная информация).

**Response:**
```json
{
  "subjects_found": ["math", "physics", "english"],
  "data": {
    "math": {
      "stream": {
        "id": 123,
        "title": "Математика. ЕГЭ Профиль"
      },
      "program": {
        "id": 456,
        "title": "Интенсивный курс"
      }
    },
    "physics": {
      "stream": {
        "id": 124,
        "title": "Физика. ЕГЭ"
      }
    }
  },
  "errors": [],
  "total_subjects_found": 2
}
```

---

## 🔧 Интеграция с расписанием

### Добавление уроков Skyeng в общий календарь

**Пример использования на frontend:**
```typescript
// Загрузка уроков Skyeng
const fetchSkyengLessons = async (startDate: string, endDate: string) => {
  const response = await fetch(
    `http://localhost:8000/parse_avatar/lessons/?start_date=${startDate}&end_date=${endDate}`,
    { credentials: 'include' }
  );
  
  if (!response.ok) throw new Error('Failed to fetch Skyeng lessons');
  
  const data = await response.json();
  return data.lessons.map((lesson: any) => ({
    id: `skyeng_${lesson.id}`,
    title: `${lesson.subject}: ${lesson.title}`,
    startTime: lesson.start_time,
    endTime: lesson.end_time,
    type: 'skyeng',
    color: getSubjectColor(lesson.subject),
    teacher: lesson.teacher,
    room: lesson.room
  }));
};

// Интеграция с Google Calendar
const fetchAllEvents = async () => {
  const [googleEvents, skyengLessons] = await Promise.all([
    fetchGoogleCalendarEvents(),
    fetchSkyengLessons(startDate, endDate)
  ]);
  
  // Объединяем события
  return [...googleEvents, ...skyengLessons];
};
```

---

## 🎨 Предметы и цвета

Автоматическое определение цвета по предмету:

```typescript
const SUBJECT_COLORS: Record<string, string> = {
  math: '#3B82F6',      // Синий
  physics: '#8B5CF6',   // Фиолетовый
  english: '#10B981',   // Зелёный
  russian: '#F59E0B',   // Оранжевый
  chemistry: '#EF4444', // Красный
  biology: '#06B6D4',   // Циан
  history: '#EC4899',   // Розовый
  social: '#6B7280',    // Серый
};
```

---

## 🔒 Безопасность

### Хранение учётных данных

- ✅ Пароли **НЕ** сохраняются на сервере
- ✅ Cookie сессии хранятся только в Django Session
- ✅ Используется HTTPS для продакшена
- ✅ CSRF защита для всех POST запросов

### Рекомендации

1. **Никогда не передавайте пароли в открытом виде**
   - Используйте только через форму с password полем
   - Не логируйте пароли

2. **Ограничьте время жизни сессии**
   ```python
   # settings.py
   SESSION_COOKIE_AGE = 86400 * 7  # 7 дней
   ```

3. **Используйте rate limiting**
   ```python
   # Ограничение попыток входа
   @method_decorator(ratelimit(key='ip', rate='5/m'), name='post')
   def post(self, request):
       ...
   ```

---

## 🐛 Отладка

### Включение подробного логирования

**backend/settings.py:**
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'parse_avatar': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Просмотр логов

```bash
# Логи backend
sudo docker-compose logs -f backend | grep "parse_avatar"

# Фильтрация по ошибкам
sudo docker-compose logs backend | grep "❌"
```

### Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `CSRF-токен не найден` | Изменилась структура страницы входа | Обновить `find_csrf_token()` |
| `Вход не удался` | Неверный логин/пароль | Проверить учётные данные |
| `401 Unauthorized` | Истёк срок сессии | Выполнить вход заново |
| `Failed to fetch` | API Skyeng недоступен | Проверить соединение |

---

## 📊 Производительность

### Оптимизация запросов

**Кэширование данных:**
```python
from django.core.cache import cache

def get_lessons_cached(subject, start_date, end_date):
    cache_key = f"skyeng_lessons_{subject}_{start_date}_{end_date}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    # Запрос к API
    lessons = fetch_lessons(subject, start_date, end_date)
    cache.set(cache_key, lessons, timeout=3600)  # 1 час
    return lessons
```

### Параллельная загрузка предметов

**Асинхронный подход:**
```python
import asyncio
import aiohttp

async def fetch_all_subjects_async():
    subjects = ['math', 'physics', 'english', ...]
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_subject(session, subj) for subj in subjects]
        results = await asyncio.gather(*tasks)
    
    return results
```

---

## 📈 Метрики

### Отслеживание использования

```python
# Счётчик успешных входов
logger.info(f"User {username} successfully logged in")

# Счётчик загруженных уроков
logger.info(f"Loaded {len(lessons)} lessons for {subject}")

# Время выполнения запроса
import time
start = time.time()
# ... запрос ...
logger.info(f"Request completed in {time.time() - start:.2f}s")
```

---

## 🔄 Roadmap

### Планируемые улучшения

- [ ] Парсинг домашних заданий
- [ ] Парсинг оценок и тестов
- [ ] Автоматическая синхронизация с Google Calendar
- [ ] Уведомления о предстоящих уроках
- [ ] Экспорт расписания в iCal/CSV
- [ ] Поддержка нескольких аккаунтов

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи backend
2. Убедитесь, что сессия активна (`/parse_avatar/status/`)
3. Проверьте доступность API Skyeng
4. Откройте issue с подробным описанием проблемы

---

**Интеграция готова к использованию!** 🎉
