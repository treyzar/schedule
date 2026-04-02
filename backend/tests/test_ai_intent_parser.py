"""
Tests for AI intent parser
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from ai.intent_parser import (
    AIIntentParser,
    IntentType,
    ParsedIntent,
    ExtractedEventData,
)


class TestExtractedEventData:
    """Тесты для модели извлечённых данных события"""
    
    def test_creation_with_required_fields(self):
        """Тест: создание с обязательными полями"""
        data = ExtractedEventData(title='Meeting')
        
        assert data.title == 'Meeting'
        assert data.start_datetime is None
        assert data.duration_minutes is None
    
    def test_creation_with_all_fields(self):
        """Тест: создание со всеми полями"""
        data = ExtractedEventData(
            title='Meeting',
            start_datetime='2024-04-02T15:00:00+03:00',
            end_datetime='2024-04-02T16:00:00+03:00',
            duration_minutes=60,
            description='Team meeting',
            location='Office',
            attendees=['test@example.com'],
            category='work',
            priority='high',
        )
        
        assert data.title == 'Meeting'
        assert data.duration_minutes == 60
        assert len(data.attendees) == 1


class TestParsedIntent:
    """Тесты для модели распарсенного намерения"""
    
    def test_creation(self):
        """Тест: создание ParsedIntent"""
        intent = ParsedIntent(
            intent_type=IntentType.CREATE_EVENT,
            confidence=0.95,
            clarification_needed=False,
        )
        
        assert intent.intent_type == IntentType.CREATE_EVENT
        assert intent.confidence == 0.95
        assert intent.clarification_needed is False
    
    def test_to_dict(self):
        """Тест: конвертация в dict"""
        intent = ParsedIntent(
            intent_type=IntentType.CREATE_EVENT,
            confidence=0.95,
            extracted_data=ExtractedEventData(title='Meeting'),
            clarification_needed=False,
        )
        
        data = intent.to_dict()
        
        assert data['intent_type'] == 'create_event'
        assert data['confidence'] == 0.95
        assert data['extracted_data']['title'] == 'Meeting'


class TestIntentType:
    """Тесты для enum типов намерений"""
    
    def test_intent_type_values(self):
        """Тест: значения типов намерений"""
        assert IntentType.CREATE_EVENT.value == 'create_event'
        assert IntentType.FIND_FREE_TIME.value == 'find_free_time'
        assert IntentType.CHECK_SCHEDULE.value == 'check_schedule'
        assert IntentType.UNKNOWN.value == 'unknown'


class TestAIIntentParser:
    """Тесты для AI парсера намерений"""
    
    @pytest.fixture
    def parser(self):
        return AIIntentParser()
    
    @pytest.mark.asyncio
    async def test_parse_create_event(self, parser):
        """Тест: парсинг намерения создания события"""
        user_text = "Встреча с командой завтра в 15:00 на час"
        
        with patch.object(parser, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps({
                "intent_type": "create_event",
                "confidence": 0.95,
                "extracted_data": {
                    "title": "Встреча с командой",
                    "start_datetime": "2024-04-02T15:00:00+03:00",
                    "end_datetime": "2024-04-02T16:00:00+03:00",
                    "duration_minutes": 60,
                },
                "clarification_needed": False,
                "clarification_questions": [],
                "suggested_action": "create"
            })
            
            intent = await parser.parse(user_text)
            
            assert intent.intent_type == IntentType.CREATE_EVENT
            assert intent.confidence == 0.95
            assert intent.extracted_data is not None
            assert intent.extracted_data.title == "Встреча с командой"
            assert intent.clarification_needed is False
    
    @pytest.mark.asyncio
    async def test_parse_clarification_needed(self, parser):
        """Тест: парсинг с необходимостью уточнения"""
        user_text = "Напомни про проект"
        
        with patch.object(parser, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps({
                "intent_type": "create_event",
                "confidence": 0.6,
                "extracted_data": {
                    "title": "Проект"
                },
                "clarification_needed": True,
                "clarification_questions": [
                    "Когда должно состояться событие?",
                    "Какое точное название события?"
                ],
                "suggested_action": "clarify"
            })
            
            intent = await parser.parse(user_text)
            
            assert intent.clarification_needed is True
            assert len(intent.clarification_questions) == 2
    
    @pytest.mark.asyncio
    async def test_parse_find_free_time(self, parser):
        """Тест: парсинг намерения поиска свободного времени"""
        user_text = "Покажи свободное время на неделе"
        
        with patch.object(parser, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps({
                "intent_type": "find_free_time",
                "confidence": 0.95,
                "extracted_data": {},
                "clarification_needed": False,
                "clarification_questions": [],
                "suggested_action": "find_slots"
            })
            
            intent = await parser.parse(user_text)
            
            assert intent.intent_type == IntentType.FIND_FREE_TIME
            assert intent.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_parse_error_handling(self, parser):
        """Тест: обработка ошибок при парсинге"""
        user_text = "test"
        
        with patch.object(parser, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API error")
            
            intent = await parser.parse(user_text)
            
            assert intent.intent_type == IntentType.UNKNOWN
            assert intent.confidence == 0.0
            assert intent.clarification_needed is True
    
    @pytest.mark.asyncio
    async def test_parse_invalid_json_response(self, parser):
        """Тест: обработка невалидного JSON ответа"""
        user_text = "test"
        
        with patch.object(parser, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "not valid json"
            
            intent = await parser.parse(user_text)
            
            assert intent.intent_type == IntentType.UNKNOWN
            assert intent.raw_response == "not valid json"
    
    def test_parse_response_markdown_cleanup(self, parser):
        """Тест: очистка markdown маркеров из ответа"""
        response_with_markdown = """```json
{"intent_type": "create_event", "confidence": 0.95}
```"""
        
        intent = parser._parse_response(response_with_markdown)
        
        assert intent.intent_type == IntentType.CREATE_EVENT
        assert intent.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_suggest_alternative_times(self, parser):
        """Тест: запрос альтернативных времён"""
        conflicts = [
            {
                "event_id": "123",
                "summary": "Meeting",
                "start": "2024-04-02T15:00:00+03:00",
                "end": "2024-04-02T16:00:00+03:00",
            }
        ]
        
        with patch.object(parser, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = json.dumps([
                "Завтра в 10:00",
                "Послезавтра в 14:00",
                "В пятницу в 11:00"
            ])
            
            alternatives = await parser.suggest_alternative_times(conflicts)
            
            assert len(alternatives) == 3
            assert "Завтра в 10:00" in alternatives
    
    def test_build_prompt(self, parser):
        """Тест: построение промта"""
        user_text = "Встреча завтра в 15:00"
        context = "Existing events: ..."
        
        prompt = parser._build_prompt(user_text, context)
        
        assert "Встреча завтра в 15:00" in prompt
        assert "CONTEXTUAL DATA:" in prompt
        assert "Existing events: ..." in prompt
    
    def test_build_prompt_without_context(self, parser):
        """Тест: построение промта без контекста"""
        user_text = "Встреча завтра в 15:00"
        
        prompt = parser._build_prompt(user_text)
        
        assert "Встреча завтра в 15:00" in prompt
        assert "CONTEXTUAL DATA:" not in prompt
