# 📚 Парсинг всех предметов Skyeng - Руководство

## ✅ Реализовано

Полная поддержка парсинга **17 предметов** из Skyeng с разными версиями API.

---

## 🎯 Возможности

### 1. **Автоматический парсинг всех предметов**
- ✅ API v1 (7 предметов): Профориентация, Python, Soft-skill, Математика, Менеджмент проектов, Курс Сингулярности, Онбординг
- ✅ API v2 (9 предметов): Биология, История, Обществознание, Физика, География, Литература, Основы безопасности, Химия, Русский
- ✅ API v3 (1 предмет): Английский

### 2. **Унификация данных**
- Адаптеры для каждой версии API
- Единый формат ответа
- Сохранение в БД

### 3. **Хранение данных**
- Предметы (`SkyengSubject`)
- Потоки (`SkyengStream`)
- Программы (`SkyengProgram`)
- Уроки (`SkyengLesson`)
- Метрики (`SkyengMetric`)

### 4. **Frontend интерфейс**
- Отображение всех предметов
- Прогресс по каждому предмету
- Статистика (уроки, ДЗ, тесты)
- Разделение на активные и неактивные

---

## 📁 Структура проекта

### Backend

```
backend/parse_avatar/
├── models.py           # Модели БД
├── adapters.py         # Адаптеры API v1/v2/v3
├── services.py         # Сервис парсинга
├── views.py            # API endpoints
├── urls.py             # Маршруты
└── migrations/         # Миграции БД
```

### Frontend

```
frontend/src/app/personal-cabinet-parsing/components/
├── ParsingInteractive.tsx    # Основной компонент
├── AllSubjectsView.tsx       # Список всех предметов
└── ...
```

---

## 🔌 API Endpoints

### 1. Получить все предметы

```bash
GET /parse_avatar/all-subjects/

# Ответ:
{
  "success": true,
  "subjects": [
    {
      "subject_key": "physics",
      "subject_name": "Физика",
      "api_version": "v2",
      "has_active_program": true,
      "stream": { "id": 123, "title": "...", "status": "active" },
      "program": { "id": 456, "title": "..." },
      "lessons_count": 28,
      "metrics": {
        "lessons_current": 0,
        "lessons_total": 28,
        "homework_rating": 4.2,
        "progress_percentage": 0
      },
      "last_parsed_at": "2026-04-01T20:25:52Z"
    }
  ],
  "parsing_results": {
    "success": [...],
    "empty": [...],
    "errors": [...]
  }
}
```

### 2. Получить предмет детально

```bash
GET /parse_avatar/subjects/{subject_key}/

# Пример:
GET /parse_avatar/subjects/physics/
```

---

## 🚀 Использование

### 1. Авторизация в Skyeng

```bash
POST /parse_calendar/skyeng-login/
Content-Type: application/json

{
  "email": "your@email.com",
  "password": "your_password"
}
```

### 2. Получение всех предметов

```bash
curl "http://localhost:8000/parse_avatar/all-subjects/" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

### 3. Frontend

Откройте:
```
http://localhost:4028/personal-cabinet-parsing
```

---

## 📊 Предметы

### API v1 (Скип-прокликай карточки)

| Предмет | Ключ | URL |
|---------|------|-----|
| Профориентация | `career_guidance` | `/api/v1/.../profession?subjectEnum=career_guidance` |
| Python | `python` | `/api/v1/.../python?subjectEnum=python` |
| Soft Skills | `soft_skills` | `/api/v1/.../profession?subjectEnum=soft_skills` |
| Математика | `math` | `/api/v1/.../math` |
| Менеджмент проектов | `managment_of_project` | `/api/v1/.../profession?subjectEnum=managment_of_project` |
| Курс Сингулярности | `lessons_about_main` | `/api/v1/.../profession?subjectEnum=lessons_about_main` |
| Онбординг | `onboarding` | Нет API |

### API v2 (Школа-база)

| Предмет | Ключ | URL |
|---------|------|-----|
| Биология | `biology` | `/api/v2/.../school-subject?subjectEnum=biology` |
| История | `history` | `/api/v2/.../school-subject?subjectEnum=history` |
| Обществознание | `social_studies` | `/api/v2/.../school-subject?subjectEnum=social_studies` |
| Физика | `physics` | `/api/v2/.../school-subject?subjectEnum=physics` |
| География | `geography` | `/api/v2/.../school-subject?subjectEnum=geography` |
| Литература | `literature` | `/api/v2/.../school-subject?subjectEnum=literature` |
| Основы безопасности | `basics_of_security` | `/api/v2/.../school-subject?subjectEnum=basics_of_security` |
| Химия | `chemistry` | `/api/v2/.../school-subject?subjectEnum=chemistry` |
| Русский | `russian` | `/api/v2/.../school-subject?subjectEnum=russian` |

### API v3 (Главный упоротый)

| Предмет | Ключ | URL |
|---------|------|-----|
| Английский | `english` | `/api/v3/.../english` |

---

## 🏗️ Архитектура

### Адаптеры

```
┌─────────────────────────────────────────────┐
│         BaseAPIAdapter                      │
│  - parse_response()                         │
│  - _parse_datetime()                        │
└─────────────────────────────────────────────┘
                    ↑
        ┌───────────┼───────────┐
        │           │           │
┌───────┴────┐ ┌───┴────────┐ ┌┴──────────────┐
│ APIv1Adapter│ │APIv2Adapter│ │ APIv3Adapter  │
│            │ │(=v1)       │ │ (English)     │
└────────────┘ └────────────┘ └───────────────┘
```

### Парсинг

```
1. SkyengParsingService.parse_all_subjects()
   ↓
2. Для каждого предмета:
   - GET запрос к API
   - Выбор адаптера (v1/v2/v3)
   - Парсинг ответа
   ↓
3. Сохранение в БД:
   - SkyengSubject
   - SkyengStream (если есть)
   - SkyengProgram (если есть)
   - SkyengLesson (список)
   - SkyengMetric
   ↓
4. Возврат сводки
```

---

## 🧪 Тестирование

### Backend

```bash
# Тест API
curl "http://localhost:8000/parse_avatar/all-subjects/" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" | python3 -m json.tool

# Проверка предметов
curl "http://localhost:8000/parse_avatar/subjects/physics/" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

### Frontend

1. Откройте `http://localhost:4028/personal-cabinet-parsing`
2. Авторизуйтесь в Skyeng (если не авторизованы)
3. Проверьте отображение всех предметов

---

##  Метрики

Для каждого предмета сохраняются:

- **Уроки**: пройдено / всего
- **ДЗ**: сдано / всего, средний балл
- **Тесты**: пройдено / всего, средний балл
- **Прогресс**: процент выполнения

---

## 🐛 Troubleshooting

### Ошибка: "Вы не авторизованы"

**Решение:**
1. Пройдите авторизацию: `/skyeng-login`
2. Проверьте cookies в браузере

### Ошибка: "Нет активных программ"

Это не ошибка — у некоторых предметов нет активных программ. Они показываются в секции "Неактивные предметы".

### Ошибка парсинга конкретного предмета

Проверьте логи backend:
```bash
sudo docker-compose logs backend | grep "Ошибка парсинга"
```

---

## 📝 Дата обновления

2026-04-01
