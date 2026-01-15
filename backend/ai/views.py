# ai/views.py

from django.http import StreamingHttpResponse
from openai import OpenAI
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings


# Класс SmartPlanView удален, так как он не используется.

# --- Вьюха для общего чата (HTTP-версия) ---
# Она остается на случай, если понадобится fallback или другой способ общения.
# На работу WebSocket'ов она никак не влияет.
class ChatView(APIView):
    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({"error": "Message is empty"}, status=400)

        dialog_history = request.session.get('chat_history', [])
        dialog_history.append({"role": "user", "content": user_message})

        messages_for_api = [
            {"role": "system", "content": "You are a helpful and friendly assistant."},
        ]
        messages_for_api.extend(dialog_history)

        try:
            client = OpenAI(
                base_url=settings.OLLAMA_BASE_URL,
                api_key='ollama',
            )

            stream = client.chat.completions.create(
                model=settings.OLLAMA_MODEL_NAME,
                messages=messages_for_api,
                temperature=0.7,
                stream=True,
            )

            def event_stream():
                full_response = ""
                try:
                    for chunk in stream:
                        token = chunk.choices[0].delta.content or ""
                        if token:
                            full_response += token
                            yield token

                    dialog_history.append({"role": "assistant", "content": full_response})
                    request.session['chat_history'] = dialog_history

                except Exception as e:
                    if dialog_history and dialog_history[-1]["role"] == "user":
                        dialog_history.pop()
                    request.session['chat_history'] = dialog_history
                    yield f" [ERROR: {e}]"

            return StreamingHttpResponse(event_stream(), content_type='text/plain')

        except Exception as e:
            return Response({"error": f"Не удалось связаться с моделью. Ошибка: {e}"}, status=500)
