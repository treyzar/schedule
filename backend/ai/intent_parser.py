"""
AI Intent Parser - парсинг намерений пользователя для создания событий.
Использует Ollama для извлечения структурированных данных из естественного языка.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
from config import get_config

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Типы намерений пользователя"""
    CREATE_EVENT = "create_event"
    FIND_FREE_TIME = "find_free_time"
    CHECK_SCHEDULE = "check_schedule"
    OPTIMIZE_SCHEDULE = "optimize_schedule"
    DELETE_EVENT = "delete_event"
    UPDATE_EVENT = "update_event"
    UNKNOWN = "unknown"


@dataclass
class ExtractedEventData:
    """Извлечённые данные события"""
    title: str
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    category: Optional[str] = None
    priority: Optional[str] = None


@dataclass
class ParsedIntent:
    """Результат парсинга намерения"""
    intent_type: IntentType
    confidence: float
    extracted_data: Optional[ExtractedEventData] = None
    clarification_needed: bool = False
    clarification_questions: Optional[List[str]] = None
    suggested_action: Optional[str] = None
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в dict"""
        data = asdict(self)
        data['intent_type'] = self.intent_type.value
        return data


class AIIntentParser:
    """
    Парсер намерений пользователя на основе AI.
    
    Пример использования:
        parser = AIIntentParser()
        intent = await parser.parse("Создай встречу с командой завтра в 15:00")
        
        if intent.intent_type == IntentType.CREATE_EVENT:
            if intent.clarification_needed:
                # Задаем уточняющие вопросы
                ask_questions(intent.clarification_questions)
            else:
                # Создаём событие
                create_event(intent.extracted_data)
    """
    
    def __init__(self):
        config = get_config()
        self.ollama_url = config.ollama.chat_url
        self.model = config.ollama.model_name
        self.timeout = config.ollama.timeout
    
    async def parse(self, user_text: str, context: Optional[str] = None) -> ParsedIntent:
        """
        Парсит намерение пользователя из текста.
        
        Args:
            user_text: Текст сообщения пользователя
            context: Дополнительный контекст (опционально)
            
        Returns:
            ParsedIntent объект
        """
        prompt = self._build_prompt(user_text, context)
        
        try:
            response = await self._call_ollama(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Error parsing intent: {e}", exc_info=True)
            return ParsedIntent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                clarification_needed=True,
                clarification_questions=["Не удалось распознать команду. Повторите, пожалуйста."],
                raw_response=str(e)
            )
    
    def _build_prompt(self, user_text: str, context: Optional[str]) -> str:
        """Строит промт для AI"""
        
        context_block = ""
        if context:
            context_block = f"\n\nCONTEXTUAL DATA:\n{context}"
        
        return f"""
You are an intent parser for a calendar assistant. Extract structured data from user's message.

RULES:
1. Respond ONLY with valid JSON
2. Do not include any text outside JSON
3. Use ISO 8601 format for dates (YYYY-MM-DDTHH:MM:SS+03:00)
4. If information is missing, set clarification_needed=true
5. Detect conflicts with existing events if context provided

INTENT TYPES:
- create_event: Create new calendar event
- find_free_time: Find available time slots
- check_schedule: Check existing schedule
- optimize_schedule: Optimize schedule
- delete_event: Delete existing event
- update_event: Update existing event
- unknown: Cannot determine intent

RESPONSE FORMAT:
{{
    "intent_type": "create_event",
    "confidence": 0.95,
    "extracted_data": {{
        "title": "Meeting title",
        "start_datetime": "2024-04-02T15:00:00+03:00",
        "end_datetime": "2024-04-02T16:00:00+03:00",
        "duration_minutes": 60,
        "description": "Optional description",
        "location": "Optional location",
        "attendees": ["email@example.com"],
        "category": "work",
        "priority": "high"
    }},
    "clarification_needed": false,
    "clarification_questions": [],
    "suggested_action": "create"
}}

EXAMPLES:

User: "Встреча с командой завтра в 15:00 на час"
Assistant: {{"intent_type":"create_event","confidence":0.98,"extracted_data":{{"title":"Встреча с командой","start_datetime":"2024-04-02T15:00:00+03:00","end_datetime":"2024-04-02T16:00:00+03:00","duration_minutes":60}},"clarification_needed":false,"clarification_questions":[],"suggested_action":"create"}}

User: "Напомни про проект"
Assistant: {{"intent_type":"create_event","confidence":0.6,"extracted_data":{{"title":"Проект"}},"clarification_needed":true,"clarification_questions":["Когда должно состояться событие?","Какое точное название события?"],"suggested_action":"clarify"}}

User: "Покажи свободное время на неделе"
Assistant: {{"intent_type":"find_free_time","confidence":0.95,"extracted_data":{{}},"clarification_needed":false,"clarification_questions":[],"suggested_action":"find_slots"}}

USER MESSAGE: {user_text}{context_block}

Respond with JSON only:
"""
    
    async def _call_ollama(self, prompt: str) -> str:
        """Вызывает Ollama API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a JSON-only assistant. Respond ONLY with valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "stream": False,
                        "format": "json",
                    },
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        logger.error(f"Ollama API error: {response.status}")
                        raise Exception(f"Ollama API error: {response.status}")
                    
                    data = await response.json()
                    return data.get("message", {}).get("content", "")
                    
        except asyncio.TimeoutError:
            logger.error("Ollama API timeout")
            raise Exception("AI service timeout")
    
    def _parse_response(self, response_text: str) -> ParsedIntent:
        """Парсит ответ от AI"""
        try:
            # Очищаем ответ от возможных markdown маркеров
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Парсим JSON
            data = json.loads(response_text)
            
            # Валидируем и создаём объект
            intent_type = IntentType(data.get("intent_type", "unknown"))
            confidence = float(data.get("confidence", 0.5))
            
            extracted_data = None
            if data.get("extracted_data"):
                extracted_data = ExtractedEventData(**data["extracted_data"])
            
            clarification_questions = data.get("clarification_questions", [])
            
            return ParsedIntent(
                intent_type=intent_type,
                confidence=confidence,
                extracted_data=extracted_data,
                clarification_needed=data.get("clarification_needed", False),
                clarification_questions=clarification_questions if clarification_questions else None,
                suggested_action=data.get("suggested_action"),
                raw_response=response_text
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return ParsedIntent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                clarification_needed=True,
                clarification_questions=["Не удалось распознать команду. Повторите, пожалуйста."],
                raw_response=response_text
            )
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}", exc_info=True)
            return ParsedIntent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                clarification_needed=True,
                raw_response=response_text
            )
    
    async def suggest_alternative_times(
        self,
        conflicts: List[dict],
        preferred_duration: int = 60
    ) -> List[str]:
        """
        Запрашивает у AI альтернативные времена для события.
        
        Args:
            conflicts: Список конфликтующих событий
            preferred_duration: Предпочтительная длительность в минутах
            
        Returns:
            Список предложений в текстовом формате
        """
        prompt = f"""
Given these conflicting events, suggest 3 alternative time slots.
Preferred duration: {preferred_duration} minutes.

Conflicts:
{json.dumps(conflicts, ensure_ascii=False)}

Respond with JSON array of strings, each string is a suggested time slot.
Example: ["Завтра в 10:00", "Послезавтра в 14:00", "В пятницу в 11:00"]
"""
        try:
            response = await self._call_ollama(prompt)
            data = json.loads(response)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error getting alternative times: {e}")
            return []
