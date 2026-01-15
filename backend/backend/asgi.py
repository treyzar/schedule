# smart_scheduler/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import ai.routing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = ProtocolTypeRouter({
    # Обычные HTTP-запросы по-прежнему будет обрабатывать Django
    "http": get_asgi_application(),

    # WebSocket-запросы будет обрабатывать AuthMiddlewareStack -> URLRouter
    "websocket": AuthMiddlewareStack(
        URLRouter(
            ai.routing.websocket_urlpatterns # <-- Указываем на наши WS-маршруты
        )
    ),
})
