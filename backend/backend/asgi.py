# backend/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import ai.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = ProtocolTypeRouter({
    # Обычные HTTP-запросы обрабатывает Django
    "http": get_asgi_application(),

    # WebSocket-запросы обрабатывает AuthMiddlewareStack -> URLRouter
    "websocket": AuthMiddlewareStack(
        URLRouter(ai.routing.websocket_urlpatterns)
    ),
})
