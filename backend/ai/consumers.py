# ai/consumers.py

import json
import logging
import requests
from typing import List, Dict, Optional
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from datetime import datetime, timedelta, time
import asyncio

logger = logging.getLogger(__name__)


async def _get_skyeng_context(user_id: int) -> Optional[str]:
    """Получить контекст данных Skyeng (уроки, предметы, дедлайны, оценки)."""
    try:
        from parse_avatar.models import SkyengSubject, SkyengLesson, SkyengMetric
        from django.utils import timezone
        
        logger.info(f"_get_skyeng_context called with user_id={user_id}")
        
        # Получаем все предметы пользователя
        subjects = list(await sync_to_async(lambda: list(SkyengSubject.objects.filter(user_id=user_id)))())
        
        logger.info(f"Found {len(subjects)} Skyeng subjects for user {user_id}")
        
        if not subjects:
            logger.info(f"No Skyeng subjects found for user {user_id}")
            return None
        
        lines = ["\n=== 📚 SKYENG: УРОКИ, ОЦЕНКИ И ПРЕДМЕТЫ ==="]
        
        for subject in subjects:
            logger.info(f"Processing subject: {subject.subject_name} (key={subject.subject_key})")
            lines.append(f"\n## 📖 Предмет: {subject.subject_name}")
            
            # Получаем уроки по предмету
            lessons = await sync_to_async(lambda: list(
                SkyengLesson.objects.filter(subject=subject).order_by('-available_at')[:30]
            ))()
            
            logger.info(f"Found {len(lessons)} lessons for subject {subject.subject_name}")
            
            if lessons:
                # Группируем по статусу и типу
                homework_active = [l for l in lessons if l.lesson_type == 'homework' and l.status in ('available', 'passed')]
                tests_active = [l for l in lessons if l.lesson_type == 'test' and l.status in ('available', 'passed')]
                passed_lessons = [l for l in lessons if l.status == 'passed' and l.score is not None]
                upcoming = [l for l in lessons if l.status == 'available' and l.deadline_at]
                
                # Оценки (только прошедшие уроки с оценками)
                if passed_lessons:
                    lines.append(f"### 🎯 Оценки ({len(passed_lessons)}):")
                    # Считаем средний балл
                    avg_score = sum(float(l.score) for l in passed_lessons) / len(passed_lessons)
                    lines.append(f"  **Средний балл: {avg_score:.2f}**")
                    for lesson in passed_lessons[:10]:
                        score_display = f"**{lesson.score}**" if float(lesson.score) >= 8 else f"{lesson.score}"
                        lines.append(f"  • {lesson.title}: {score_display}")
                
                # Домашние задания активные
                if homework_active:
                    hw_passed = [l for l in homework_active if l.status == 'passed']
                    hw_available = [l for l in homework_active if l.status == 'available']
                    lines.append(f"\n### 📝 Домашние задания (сдано: {hw_passed[0:5]}, доступно: {len(hw_available)}):")
                    for lesson in hw_available[:5]:
                        deadline = ""
                        if lesson.deadline_at:
                            days_left = (lesson.deadline_at - timezone.now()).days
                            deadline_str = lesson.deadline_at.strftime('%d.%m.%Y %H:%M')
                            if days_left < 0:
                                deadline = f" ⚠️ **ПРОСРОЧЕНО**: {deadline_str}"
                            elif days_left == 0:
                                deadline = f" 🔥 **СРОК СЕГОДНЯ**: {deadline_str}"
                            elif days_left <= 3:
                                deadline = f" ⏰ СРОК ЧЕРЕЗ {days_left} дн.: {deadline_str}"
                            else:
                                deadline = f" (срок: {deadline_str})"
                        score_str = f" ✅ Оценка: {lesson.score}" if lesson.score and lesson.status == 'passed' else ""
                        lines.append(f"  • {lesson.title}{deadline}{score_str}")
                
                # Тесты
                if tests_active:
                    tests_passed = [l for l in tests_active if l.status == 'passed']
                    tests_available = [l for l in tests_active if l.status == 'available']
                    lines.append(f"\n### 📊 Тесты (пройдено: {len(tests_passed)}, доступно: {len(tests_available)}):")
                    for lesson in tests_available[:5]:
                        deadline = ""
                        if lesson.deadline_at:
                            days_left = (lesson.deadline_at - timezone.now()).days
                            if days_left < 0:
                                deadline = f" ⚠️ **ПРОСРОЧЕНО**: {lesson.deadline_at.strftime('%d.%m')}"
                            elif days_left <= 3:
                                deadline = f" ⏰ **СРОК ЧЕРЕЗ {days_left} дн.!**"
                        score_str = f" ✅ Оценка: {lesson.score}" if lesson.score and lesson.status == 'passed' else ""
                        lines.append(f"  • {lesson.title}{deadline}{score_str}")
                
                # Пройденные уроки без оценок
                passed_no_score = [l for l in lessons if l.status == 'passed' and l.score is None]
                if passed_no_score:
                    lines.append(f"\n### ✅ Пройдено уроков: {len(passed_no_score)}")
                
            # Получаем метрики если есть
            try:
                metric = await sync_to_async(lambda: SkyengMetric.objects.filter(subject=subject).first())()
                if metric:
                    lines.append(f"\n### 📈 Прогресс предмета:")
                    lines.append(f"  • Уроков пройдено: {metric.lessons_current}/{metric.lessons_total} ({metric.progress_percentage}%)")
                    if metric.homework_total > 0:
                        lines.append(f"  • ДЗ сдано: {metric.homework_current}/{metric.homework_total}")
                        if metric.homework_rating:
                            lines.append(f"  • Средний балл ДЗ: {metric.homework_rating}")
                    if metric.tests_total > 0:
                        lines.append(f"  • Тестов пройдено: {metric.tests_current}/{metric.tests_total}")
                        if metric.tests_rating:
                            lines.append(f"  • Средний балл тестов: {metric.tests_rating}")
            except Exception as e:
                logger.warning(f"Failed to get metrics for {subject.subject_name}: {e}")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error getting Skyeng context: {e}", exc_info=True)
        return None


async def _get_google_calendar_context(google_credentials: Optional[Dict]) -> Optional[str]:
    """Получить контекст расписания из Google Calendar."""
    try:
        if not google_credentials:
            return None

        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        # Конвертируем expires_at в expiry (формат Google OAuth)
        creds_data = {
            k: v for k, v in google_credentials.items()
            if k not in ('expires_at', 'email')
        }
        # Конвертируем ISO строку в datetime для expiry
        if 'expires_at' in google_credentials and google_credentials['expires_at']:
            try:
                expiry_dt = datetime.fromisoformat(google_credentials['expires_at'])
                creds_data['expiry'] = expiry_dt
            except (ValueError, TypeError):
                pass

        creds = Credentials(**creds_data)
        service = build('calendar', 'v3', credentials=creds)

        # Получаем события на неделю
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59)

        time_min = start_of_week.isoformat() + 'Z'
        time_max = end_of_week.isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return "\n=== GOOGLE CALENDAR: Нет событий на эту неделю ==="

        # Формируем текстовый контекст
        lines = ["\n=== GOOGLE CALENDAR: Расписание на неделю ==="]
        lines.append(f"Всего событий: {len(events)}")

        # Группируем по дням
        events_by_day = {}
        for event in events:
            start = event.get('start', {})
            start_dt = start.get('dateTime', start.get('date', ''))
            try:
                if start_dt:
                    event_date = start_dt.split('T')[0]
                    if event_date not in events_by_day:
                        events_by_day[event_date] = []
                    events_by_day[event_date].append(event)
            except:
                pass

        for day in sorted(events_by_day.keys()):
            day_events = events_by_day[day]
            day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%A')
            lines.append(f"\n{day} ({day_name}):")

            for event in day_events:
                start = event.get('start', {})
                end = event.get('end', {})
                start_time = start.get('dateTime', start.get('date', ''))
                end_time = end.get('dateTime', end.get('date', ''))

                # Форматируем время
                try:
                    start_str = start_time.split('T')[1][:5] if 'T' in start_time else 'весь день'
                    end_str = end_time.split('T')[1][:5] if 'T' in end_time else 'весь день'
                except:
                    start_str = ''
                    end_str = ''

                summary = event.get('summary', 'Без названия')
                lines.append(f"  {start_str}-{end_str}: {summary}")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error getting Google Calendar context: {e}")
        return None


async def get_full_context(user_id: int, google_credentials: Optional[Dict] = None) -> str:
    """Получить полный контекст для AI: календарь + Skyeng + другая информация."""
    logger.info(f"get_full_context called with user_id={user_id}, has_google_creds={bool(google_credentials)}")
    contexts = []
    
    # Google Calendar
    calendar_context = await _get_google_calendar_context(google_credentials)
    if calendar_context:
        logger.info(f"Google Calendar context: {len(calendar_context)} chars")
        contexts.append(calendar_context)
    else:
        logger.info("No Google Calendar context")
    
    # Skyeng
    skyeng_context = await _get_skyeng_context(user_id)
    if skyeng_context:
        logger.info(f"Skyeng context: {len(skyeng_context)} chars")
        contexts.append(skyeng_context)
    else:
        logger.info("No Skyeng context")
    
    if not contexts:
        logger.warning("No contexts available")
        return "Нет доступных данных о расписании и учебе."
    
    full_context = "\n".join(contexts)
    logger.info(f"Full context length: {len(full_context)} chars")
    logger.info(f"Context preview: {full_context[:500]}...")
    return full_context


class OllamaClient:
    """Клиент для взаимодействия с Ollama API."""

    DEFAULT_SYSTEM_PROMPT = """Ты - интеллектуальный AI-помощник для управления расписанием, календарем и учебой.

## Твоя специализация:
- Анализ расписания пользователя (Google Calendar)
- Отслеживание уроков, домашних заданий и тестов (Skyeng)
- Контроль дедлайнов и просроченных задач
- Анализ успеваемости и оценок
- Поиск свободного времени для встреч и задач
- Обнаружение конфликтов в расписании
- Оптимизация использования времени
- Предложения по улучшению продуктивности
- Помощь в планировании дня/недели/месяца

## Твои ответы:
- **Используй Markdown**: заголовки `##`, `###`, списки `-`, **жирный текст** для важного
- Кратко и по делу
- Структурированно (списки, заголовки когда нужно)
- С конкретными рекомендациями
- На русском языке
- Используй эмодзи для наглядности: 📚 📝 📊 ✅ ⏰ ⚠️ 🔥

## ВАЖНО:
Ты получаешь актуальные данные в каждом запросе:
- **Google Calendar**: события и встречи
- **Skyeng**: уроки, домашние задания, тесты, оценки, дедлайны, прогресс по предметам

Внимательно анализируй предоставленные данные в разделе "=== АКТУАЛЬНОЕ РАСПИСАНИЕ ПОЛЬЗОВАТЕЛЯ ===".
Если в данных есть информация - используй её для ответа.
Если данных нет - честно говори об этом и предлагай помощь.

## Формат ответа:
- Начинай с главного (прямой ответ на вопрос)
- Затем детали (списком)
- В конце рекомендации (если уместно)
"""

    MAX_HISTORY_MESSAGES = 8
    REQUEST_TIMEOUT = 90  # секунды

    def __init__(
        self,
        base_url: str,
        model_name: str,
        system_prompt: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/v1")
        self.model_name = model_name
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT

    def _build_payload(self, messages: List[Dict[str, str]], schedule_context: Optional[str] = None) -> Dict:
        """Собрать payload для API запроса."""
        system_message = {"role": "system", "content": self.system_prompt}
        
        # Добавляем контекст расписания к системному сообщению
        if schedule_context:
            system_message["content"] += f"\n\n=== АКТУАЛЬНОЕ РАСПИСАНИЕ ПОЛЬЗОВАТЕЛЯ ===\n{schedule_context}\n=== КОНЕЦ РАСПИСАНИЯ ===\n\nИспользуй эти данные о расписании для ответа на вопросы пользователя."
        
        return {
            "model": self.model_name,
            "messages": [
                system_message,
                *messages[-self.MAX_HISTORY_MESSAGES:]
            ],
            "stream": False
        }

    def get_chat_response(self, messages: List[Dict[str, str]], schedule_context: Optional[str] = None) -> str:
        """Получить ответ от Ollama API."""
        url = f"{self.base_url}/api/chat"
        payload = self._build_payload(messages, schedule_context)

        try:
            logger.info(f"Sending request to Ollama: {url}")
            response = requests.post(
                url,
                json=payload,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            result = response.json()
            content = result.get("message", {}).get("content", "")

            if not content:
                logger.warning("Empty response from Ollama")
                return "[ERROR: Пустой ответ от Ollama]"

            logger.info(f"Received response from Ollama: {len(content)} chars")
            return content

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timeout after {self.REQUEST_TIMEOUT}s")
            return f"[ERROR: Превышено время ожидания ({self.REQUEST_TIMEOUT}с)]"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ollama connection error: {e}")
            return f"[ERROR: Не удалось подключиться к Ollama. Убедитесь, что Ollama запущен: ollama serve]"
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return f"[ERROR: Ошибка запроса: {str(e)}]"
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            return "[ERROR: Ошибка парсинга ответа]"
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return f"[ERROR: Неожиданная ошибка: {str(e)}]"


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для AI чата."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ollama_client: Optional[OllamaClient] = None
        self._session_history: List[Dict] = []

    async def connect(self):
        """Обработка подключения."""
        try:
            # Инициализируем Ollama клиент
            self.ollama_client = OllamaClient(
                base_url=settings.OLLAMA_BASE_URL,
                model_name=settings.OLLAMA_MODEL_NAME
            )

            # Инициализируем сессию
            await self._initialize_session()

            await self.accept()
            logger.info("WebSocket connected and initialized")
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {e}", exc_info=True)
            await self.close()

    async def disconnect(self, close_code: int):
        """Обработка отключения."""
        logger.info(f"WebSocket disconnected: {close_code}")

    async def receive(self, text_data: str):
        """Обработка входящего сообщения."""
        try:
            # Парсим сообщение
            data = json.loads(text_data)
            
            # Проверяем, является ли это командой управления
            action = data.get('action')
            if action == 'clear_history':
                await self._clear_dialog_history()
                await self.send(text_data=json.dumps({
                    'status': 'success',
                    'message': 'История чата очищена'
                }))
                return

            user_message = data.get('message', '').strip()

            if not user_message:
                await self._send_error("Пустое сообщение")
                return

            logger.info(f"Received message: {user_message[:50]}...")

            # Получаем полный контекст: Google Calendar + Skyeng + другое
            user_id = self.scope['session'].get('_auth_user_id') if self._has_session() else None
            google_credentials = self.scope['session'].get('google_credentials') if self._has_session() else None
            
            schedule_context = await get_full_context(
                user_id=user_id if user_id else 0,
                google_credentials=google_credentials
            )

            # Получаем историю диалога
            dialog_history = await self._get_dialog_history()

            # Формируем сообщения для API
            messages_for_api = [
                {"role": "system", "content": self.ollama_client.system_prompt},
                *dialog_history[-self.ollama_client.MAX_HISTORY_MESSAGES:],
                {"role": "user", "content": user_message}
            ]

            logger.info(f"Sending {len(messages_for_api)} messages to Ollama with schedule context")

            # Получаем ответ от Ollama (в thread pool)
            full_response = await sync_to_async(
                self.ollama_client.get_chat_response,
                thread_sensitive=False
            )(messages_for_api, schedule_context)

            logger.info(f"Got response: {full_response[:50] if full_response else 'None'}...")

            # Отправляем ответ
            await self._send_response(full_response)

            # Сохраняем историю
            await self._save_dialog_history(
                dialog_history + [{"role": "user", "content": user_message}],
                full_response
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            await self._send_error("Неверный формат сообщения")
        except Exception as e:
            logger.error(f"Error in ChatConsumer: {e}", exc_info=True)
            await self._send_error("Внутренняя ошибка сервера")

    async def _initialize_session(self):
        """Инициализировать сессию."""
        if self._has_session():
            if 'chat_history' not in self.scope['session']:
                self.scope['session']['chat_history'] = []
            await sync_to_async(self.scope['session'].save)()
        else:
            self._session_history = []

    def _has_session(self) -> bool:
        """Проверить наличие сессии."""
        return 'session' in self.scope and self.scope['session']

    async def _get_dialog_history(self) -> List[Dict]:
        """Получить историю диалога."""
        if self._has_session():
            return self.scope['session'].get('chat_history', [])
        return self._session_history

    async def _clear_dialog_history(self):
        """Очистить историю диалога."""
        if self._has_session():
            self.scope['session']['chat_history'] = []
            await sync_to_async(self.scope['session'].save)()
        else:
            self._session_history = []
        logger.info("Dialog history cleared")

    async def _send_response(self, content: str):
        """Отправить ответ клиенту."""
        try:
            await self.send(text_data=json.dumps({
                'full_response': content,
                'status': 'done' if not content.startswith('[ERROR:') else 'error'
            }))
        except Exception as e:
            logger.error(f"Failed to send response: {e}")

    async def _send_error(self, message: str):
        """Отправить ошибку клиенту."""
        try:
            await self.send(text_data=json.dumps({
                'error': message,
                'status': 'error'
            }))
        except Exception as e:
            logger.error(f"Failed to send error: {e}")

    async def _save_dialog_history(
        self,
        history: List[Dict],
        response: str
    ):
        """Сохранить историю диалога."""
        history.append({"role": "assistant", "content": response})

        if self._has_session():
            self.scope['session']['chat_history'] = history
            await sync_to_async(self.scope['session'].save)()
        else:
            self._session_history = history
