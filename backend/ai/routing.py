# ai/routing.py

from django.urls import re_path
from . import consumers

# Этот список НЕ должен быть пустым.
# Он говорит, какой consumer обрабатывает какой WebSocket URL.
websocket_urlpatterns = [
    # re_path сопоставляет URL с вашим ChatConsumer.
    # r'^ws/ai/chat/$' - это регулярное выражение, которое ищет точное совпадение.
    re_path(r'^ws/ai/chat/$', consumers.ChatConsumer.as_asgi()),
]
