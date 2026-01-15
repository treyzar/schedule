# ai/urls.py

from django.urls import path
from . import views
from django.views.generic import TemplateView # <-- Импортируйте TemplateView

urlpatterns = [
    # --- НОВЫЙ МАРШРУТ ДЛЯ ТЕСТОВОЙ СТРАНИЦЫ ---
    # Он будет доступен по адресу /api/ai/test/
    # --- Существующие API-маршруты ---
path('chat/', views.ChatView.as_view(), name='ai_chat'),
]
