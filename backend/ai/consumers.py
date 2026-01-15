# ai/consumers.py

import json
import requests  # <-- Используем requests вместо openai
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

def get_ollama_response_natively(messages):
    """
    ФИНАЛЬНАЯ, НАДЕЖНАЯ ВЕРСИЯ.
    Общается с Ollama напрямую через ее родной API, используя requests.
    Возвращает полный, собранный ответ.
    """
    # URL для нативного API Ollama
    url = settings.OLLAMA_BASE_URL.replace("/v1", "") + "/api/chat"
    
    payload = {
        "model": settings.OLLAMA_MODEL_NAME,
        "messages": messages,
        "stream": True # Мы все еще используем стриминг для эффективности, но собираем ответ здесь
    }

    try:
        # Отправляем запрос с потоковой обработкой
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()  # Проверяем на HTTP-ошибки (4xx, 5xx)

        full_response_parts = []
        # итерируемся по строкам ответа
        for line in response.iter_lines():
            if line:
                # Каждая строка - это отдельный JSON
                line_json = json.loads(line)
                # Извлекаем токен из правильной структуры
                token = line_json.get("message", {}).get("content", "")
                if token:
                    full_response_parts.append(token)
        
        # Соединяем все части и возвращаем
        return "".join(full_response_parts)

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request to Ollama failed: {e}")
        return f"[ERROR: Could not connect to Ollama at {url}]"
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from Ollama: {e}")
        return "[ERROR: Received invalid data from Ollama]"


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        if 'chat_history' not in self.scope['session']:
            self.scope['session']['chat_history'] = []
        print("WebSocket connected and session initialized.")

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            user_message = text_data_json['message']

            dialog_history = self.scope['session'].get('chat_history', [])
            dialog_history.append({"role": "user", "content": user_message})

            messages_for_api = [
                {"role": "system", "content": "You are a helpful and friendly AI assistant."},
            ]
            messages_for_api.extend(dialog_history[-10:])
            
            # Оборачиваем нашу новую надежную функцию
            async_get_full_response = sync_to_async(get_ollama_response_natively, thread_sensitive=True)
            
            # Ждем полного ответа
            full_response = await async_get_full_response(messages_for_api)
            
            # Отправляем один финальный JSON
            if full_response:
                await self.send(text_data=json.dumps({
                    'full_response': full_response,
                    'status': 'done'
                }))

            # Сохраняем историю
            dialog_history.append({"role": "assistant", "content": full_response})
            self.scope['session']['chat_history'] = dialog_history
            await sync_to_async(self.scope['session'].save)()

        except Exception as e:
            error_message = f"An error occurred in consumer: {str(e)}"
            print(f"Error in ChatConsumer: {error_message}", exc_info=True)
            await self.send(text_data=json.dumps({'error': error_message}))
