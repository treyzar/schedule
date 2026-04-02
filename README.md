# 📅 Schedule Unified — Умная система управления расписанием

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![AI](https://img.shields.io/badge/AI-Qwen3.5--9B-orange.svg)](https://ollama.ai/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

---

## 📖 Описание

**Schedule Unified** — это интеллектуальная система управления расписанием с AI-помощником, которая объединяет:

- 📅 **Google Calendar** — синхронизация календаря
- 📚 **Skyeng** — отслеживание уроков, оценок и дедлайнов
- 🤖 **AI-помощник** — управление через естественный язык (Qwen 3.5)
- 💬 **Telegram Bot** — удобное взаимодействие
- 🌐 **Web Interface** — современный интерфейс на Next.js

---

## ✨ Ключевые возможности

### 🗣️ Управление естественным языком

Общайтесь с помощником как с живым ассистентом:

```
"Запиши меня к стоматологу завтра в 15:00"
"Какие у меня дела на сегодня?"
"Когда следующая встреча с командой?"
"Найди свободное время на неделе"
"Какие у меня оценки по английскому?"
```

### 🔒 Безопасное создание событий

**Все события создаются только после вашего подтверждения!**

```
1. Вы: "Запиши меня к врачу завтра в 14:00"
2. AI создаёт черновик и показывает вам
3. Вы подтверждаете: "подтвердить"
4. Событие создаётся в Google Calendar ✨
```

### 📊 Полная осведомлённость

AI видит всё ваше расписание:

| Источник | Данные |
|----------|--------|
| **Google Calendar** | Встречи, события, напоминания |
| **Skyeng** | Уроки, ДЗ, тесты, дедлайны, оценки, прогресс |
| **Анализ** | Свободные слоты, конфликты, рекомендации |

### 📱 Мультиплатформенность

- **Telegram Bot** — быстрое взаимодействие в мессенджере
- **Web Interface** — полноценный интерфейс с календарём
- **WebSocket** — мгновенные ответы в реальном времени

---

## 🏗️ Архитектура проекта

```
┌─────────────────────────────────────────────────────────────────┐
│                        Schedule Unified                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Telegram   │  │     Web      │  │   WebSocket  │         │
│  │     Bot      │  │  Interface   │  │    Client    │         │
│  │              │  │  (Next.js)   │  │              │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                    │
│                  ┌────────▼────────┐                           │
│                  │  Django Backend │                           │
│                  │   (FastAPI)     │                           │
│                  └────────┬────────┘                           │
│                           │                                    │
│         ┌─────────────────┼─────────────────┐                 │
│         │                 │                 │                  │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐         │
│  │  AI Service  │  │   Google     │  │   Skyeng     │         │
│  │  (Qwen 3.5)  │  │   Calendar   │  │     API      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
       │   Redis     │ │ PostgreSQL  │ │   Ollama    │
       │  (Cache)    │ │   (Database)│ │   (AI)      │
       └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 📁 Структура проекта

```
schedule_unified/
├── backend/                    # Django backend
│   ├── ai/                     # AI-помощник
│   │   ├── consumers.py        # WebSocket consumer
│   │   ├── views.py            # API endpoints
│   │   └── intent_parser.py    # Распознавание намерений
│   ├── parse_calendar/         # Google Calendar интеграция
│   │   ├── views.py            # Calendar API
│   │   ├── models.py           # User credentials
│   │   └── migrations/         # Миграции БД
│   ├── parse_avatar/           # Skyeng интеграция
│   │   ├── models.py           # Skyeng модели
│   │   ├── views.py            # Skyeng API
│   │   └── services.py         # Бизнес-логика
│   ├── services/               # Общие сервисы
│   ├── shared/                 # Общие утилиты
│   │   ├── credentials.py      # Управление credentials
│   │   └── encryption.py       # Шифрование данных
│   ├── config/                 # Конфигурация
│   ├── tests/                  # Тесты
│   ├── manage.py               # Django management
│   └── requirements.txt        # Python зависимости
│
├── frontend/                   # Next.js frontend
│   ├── src/                    # Исходный код
│   │   ├── app/                # App Router
│   │   ├── components/         # React компоненты
│   │   └── lib/                # Утилиты
│   ├── public/                 # Статические файлы
│   ├── package.json            # Node зависимости
│   └── Dockerfile              # Docker образ
│
├── telegram/                   # Telegram bot
│   ├── bot.py                  # Основной бот
│   ├── bot_refactored.py       # Рефакторинг
│   ├── services/               # Сервисы
│   │   ├── skyeng_data.py      # Skyeng данные
│   │   └── google_data.py      # Google данные
│   ├── requirements.txt        # Python зависимости
│   └── .env                    # Переменные окружения
│
├── docker-compose.yml          # Docker Compose конфигурация
├── Makefile                    # Make команды
└── docs/                       # Документация
    ├── GOOGLE_CALENDAR_AI_INTEGRATION.md
    ├── SKYENG_INTEGRATION.md
    └── PERFORMANCE_REVIEW.md
```

---

## 🚀 Быстрый старт

### Требования

- Docker и Docker Compose
- Python 3.10+
- Node.js 18+
- Ollama с моделью `qwen3.5:9b`

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/schedule_unified.git
cd schedule_unified
```

### 2. Настройка переменных окружения

#### Backend (.env)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Ollama AI
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL_NAME=qwen3.5:9b

# Redis
REDIS_URL=redis://redis:6379/1

# Django
SECRET_KEY=your-secret-key
DEBUG=True
```

#### Frontend (.env)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Telegram (.env)

```bash
TELEGRAM_BOT_TOKEN=your-bot-token
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL_NAME=qwen3.5:9b
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 3. Установка Ollama модели

```bash
# Установить Ollama: https://ollama.ai/
ollama pull qwen3.5:9b
```

### 4. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 5. Применение миграций

```bash
docker-compose exec backend python manage.py migrate
```

### 6. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```

---

## 📱 Использование

### Telegram Bot

1. **Запуск бота:** `/start`
2. **Подключение Google Calendar:** `/login_google`
3. **Подключение Skyeng:** `/login_skyeng почта пароль`
4. **Проверка статуса:** `/status`

### Основные команды

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота |
| `/help` | Справка |
| `/status` | Статус подключений |
| `/today` | Сводка на сегодня |
| `/week` | Расписание на неделю |
| `/grades` | Успеваемость Skyeng |
| `/calendar` | События календаря |
| `/lessons` | Уроки Skyeng |

### AI-помощник

Просто напишите сообщение:

```
"Запиши меня к стоматологу завтра в 15:00"
"Какие у меня оценки по русскому?"
"Когда дедлайн по домашке?"
"Найди свободное время на неделе"
```

---

## 🔧 Разработка

### Backend

```bash
cd backend

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера разработки
python manage.py runserver

# Запуск тестов
python manage.py test

# Применение миграций
python manage.py migrate
```

### Frontend

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev

# Сборка
npm run build

# Запуск production
npm start
```

### Telegram Bot

```bash
cd telegram

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python bot.py
```

### Тестирование

```bash
# Backend тесты
docker-compose exec backend python manage.py test

# Frontend тесты
cd frontend && npm test

# Запуск в режиме разработки
docker-compose -f docker-compose.dev.yml up
```

---

## 🛠️ Технологии

### Backend

| Технология | Версия | Описание |
|------------|--------|----------|
| **Python** | 3.10+ | Язык программирования |
| **Django** | 4.2+ | Web-фреймворк |
| **Django Channels** | 4.x | WebSocket поддержка |
| **FastAPI** | 0.100+ | API endpoints |
| **PostgreSQL** | 15+ | База данных |
| **Redis** | 7+ | Кэш и брокер |
| **Ollama** | latest | AI модель |

### Frontend

| Технология | Версия | Описание |
|------------|--------|----------|
| **Next.js** | 14+ | React фреймворк |
| **React** | 18+ | UI библиотека |
| **TypeScript** | 5+ | Типизация |
| **Tailwind CSS** | 3+ | Стилизация |
| **shadcn/ui** | latest | UI компоненты |

### DevOps

| Технология | Описание |
|------------|----------|
| **Docker** | Контейнеризация |
| **Docker Compose** | Оркестрация |
| **GitHub Actions** | CI/CD |

---

## 🔐 Безопасность

### Защита данных

- ✅ **Шифрование токенов** — все OAuth токены зашифрованы
- ✅ **Подтверждение действий** — критичные операции требуют подтверждения
- ✅ **Сессионная изоляция** — пользователи видят только свои данные
- ✅ **HTTPS** — безопасное соединение

### OAuth 2.0

```
1. Пользователь нажимает /login_google
2. Открывается страница авторизации Google
3. Пользователь предоставляет доступ
4. Google возвращает OAuth токен
5. Токен шифруется и сохраняется в БД
```

---

## 📊 Мониторинг

### Health Check

```bash
curl http://localhost:8000/health/

# Ответ:
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "google": "healthy",
    "skyeng": "healthy",
    "ollama": "healthy"
  }
}
```

### Логи

```bash
# Все логи
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# AI события
docker-compose logs -f backend | grep -E "Intent|Event|Calendar"
```

---

## 📈 Производительность

### Бенчмарки

| Метрика | Значение |
|---------|----------|
| **Время ответа AI** | ~2-5 сек |
| **WebSocket latency** | <100ms |
| **API response time** | <200ms |
| **Память (backend)** | ~500MB |
| **Память (frontend)** | ~200MB |

### Оптимизация

- ✅ **Кэширование** — Redis для частых запросов
- ✅ **Асинхронность** — asyncio для I/O операций
- ✅ **Индексы БД** — оптимизированные запросы
- ✅ **Code splitting** — разделение кода на чанки

---

## 📚 Документация

- [**AI Integration**](GOOGLE_CALENDAR_AI_INTEGRATION.md) — AI-помощник и Google Calendar
- [**Skyeng Integration**](SKYENG_INTEGRATION.md) — Интеграция с Skyeng
- [**Performance Review**](performance-review.md) — Отчёт о производительности
- [**Refactoring Report**](REFACTORING_REPORT.md) — Отчёт о рефакторинге

---

## ❓ FAQ

### Q: AI не отвечает, что делать?

**A:** 
1. Проверьте Ollama: `ollama list`
2. Проверьте логи: `docker-compose logs -f backend`
3. Перезапустите: `docker-compose restart backend`

### Q: Как отключить Google Calendar?

**A:** Напишите `/logout_google` в Telegram боте.

### Q: Где хранятся данные?

**A:** Все данные хранятся локально в PostgreSQL. Токены зашифрованы.

### Q: Можно ли использовать другую AI модель?

**A:** Да, измените `OLLAMA_MODEL_NAME` в `.env`.

---

## 🤝 Вклад в проект

### Pull Request Process

1. Создайте ветку: `git checkout -b feature/new-feature`
2. Внесите изменения: `git commit -m 'Add new feature'`
3. Отправьте: `git push origin feature/new-feature`
4. Создайте Pull Request

### Code Style

```bash
# Backend
black backend/
flake8 backend/
mypy backend/

# Frontend
npm run lint
npm run format
```

---

## 👥 Авторы

- **Иван Христофоров** — *Основной разработчик*

---

## 📝 Лицензия

MIT License — см. файл [LICENSE](LICENSE) для деталей.

---

## 🙏 Благодарности

- [Ollama](https://ollama.ai/) — локальные AI модели
- [Google Calendar API](https://developers.google.com/calendar) — календарь
- [Skyeng](https://skyeng.ru/) — платформа обучения
- [Telegram Bot API](https://core.telegram.org/bots) — мессенджер
- [Django](https://www.djangoproject.com/) — backend фреймворк
- [Next.js](https://nextjs.org/) — frontend фреймворк

---

## 📞 Контакты

- **Email:** ivan.khristoforov@sinhub.ru
- **Telegram:** [@yourusername](https://t.me/yourusername)
- **GitHub:** [yourusername](https://github.com/yourusername)

---

**Сделано с ❤️ для умного планирования времени**

⭐ Если вам нравится проект, поставьте звезду!
