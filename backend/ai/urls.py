# ai/urls.py

from django.urls import path
from .views import (
    ScheduleContextView,
    ChatView,
    ParseIntentView,
    CreateEventFromNaturalLanguage,
    CheckEventConflictView,
    FindFreeTimeView,
)

urlpatterns = [
    # === Контекст и чат ===
    path('schedule-context/', ScheduleContextView.as_view(), name='schedule_context'),
    path('chat/', ChatView.as_view(), name='ai_chat'),
    
    # === AI Intent Parser ===
    path('intent/parse/', ParseIntentView.as_view(), name='parse_intent'),
    
    # === Создание событий из естественного языка ===
    path('events/create/', CreateEventFromNaturalLanguage.as_view(), name='create_event_nlp'),
    path('events/check-conflict/', CheckEventConflictView.as_view(), name='check_event_conflict'),
    path('events/find-free-time/', FindFreeTimeView.as_view(), name='find_free_time'),
]
