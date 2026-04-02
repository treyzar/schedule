"""
Константы для Telegram бота
"""

# Таймауты запросов (секунды)
REQUEST_TIMEOUT_SHORT = 10
REQUEST_TIMEOUT_MEDIUM = 15
REQUEST_TIMEOUT_LONG = 45

# Максимальное количество сообщений в истории
MAX_HISTORY_MESSAGES = 6

# Количество последних оценок для отображения
MAX_RECENT_SCORES = 3

# Количество запланированных уроков для отображения
MAX_SCHEDULED_LESSONS = 2

# Предметы по умолчанию
SUBJECTS_MAP = {
    "Физика": "physics",
    "Математика": "math",
    "Английский": "english",
    "Информатика": "informatics",
    "Русский язык": "russian",
    "Химия": "chemistry",
    "Биология": "biology",
    "История": "history",
    "Профориентация": "career_guidance"
}

# Специальные предметы с расширенными данными
SPECIAL_SUBJECTS = ['math', 'career_guidance']

# Google OAuth redirect URI для Telegram бота
GOOGLE_OAUTH_REDIRECT_URI = 'http://localhost:8080/'

# Google OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Путь к файлу с секретами Google
CLIENT_SECRET_PATH = 'client_secrets.json'
