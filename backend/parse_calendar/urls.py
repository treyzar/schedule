# parse_calendar/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Маршруты для авторизации Google
    path('authorize/', views.GoogleAuthorizeView.as_view(), name='google_authorize'),
    path('oauth2callback/', views.GoogleCallbackView.as_view(), name='google_callback'),

    # --- Маршрут для страницы ДНЕВНОГО расписания ---
    # Ссылается на GetInitialDataView, которую мы вернули
    path('initial-data/', views.GetInitialDataView.as_view(), name='get_initial_data'),

    # --- Маршруты для НЕДЕЛЬНОГО и МЕСЯЧНОГО расписания ---
    # Получение списка событий по диапазону дат
    path('events/', views.GoogleEventsView.as_view(), name='google_events_list'),
    
    # Управление конкретным событием (Редактирование/Удаление)
    path('events/<str:event_id>/', views.EventDetailView.as_view(), name='event_detail'),
]
